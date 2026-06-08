import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base import BaseOCREngine
from ..models import Document, DocumentPage, Block

logger = logging.getLogger(__name__)


class PaddleOCRVLAdapter(BaseOCREngine):
    """PaddleOCR-VL engine adapter with optional MLX-VLM acceleration.

    Supports two modes:
      1. **Local inference** (default): loads the VLM model directly into memory.
         Slower but requires no separate service.
      2. **MLX-VLM accelerated** (recommended on Apple Silicon): connects to a
         running ``mlx_vlm.server`` for the VLM component, leveraging Apple
         Neural Engine for significantly faster inference.

    To use MLX-VLM mode, start the server first::

        mlx_vlm.server --port 8111

    Then initialise the adapter::

        adapter = PaddleOCRVLAdapter(
            mlx_vlm_url="http://localhost:8111/",
            mlx_vlm_model="PaddlePaddle/PaddleOCR-VL-1.6",
        )
    """

    def __init__(
        self,
        device: str = "cpu",
        mlx_vlm_url: Optional[str] = None,
        mlx_vlm_model: Optional[str] = None,
        pipeline_version: str = "v1.6",
    ) -> None:
        self._device = device
        self._mlx_vlm_url = mlx_vlm_url or os.environ.get("UNIOCR_MLX_VLM_URL")
        self._mlx_vlm_model = mlx_vlm_model or os.environ.get(
            "UNIOCR_MLX_VLM_MODEL", "PaddlePaddle/PaddleOCR-VL-1.6"
        )
        self._pipeline_version = pipeline_version
        self._pipeline: Optional[Any] = None  # Lazy-loaded

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _get_pipeline(self) -> Any:
        """Lazy-load the PaddleOCR-VL pipeline on first use."""
        if self._pipeline is not None:
            return self._pipeline

        from paddleocr import PaddleOCRVL

        kwargs: Dict[str, Any] = {
            "device": self._device,
            "pipeline_version": self._pipeline_version,
        }

        # If an MLX-VLM server URL is configured, route the VLM component
        # through it for accelerated inference on Apple Silicon.
        if self._mlx_vlm_url:
            logger.info(
                "PaddleOCR-VL will use MLX-VLM backend at %s (model: %s)",
                self._mlx_vlm_url,
                self._mlx_vlm_model,
            )
            kwargs.update(
                {
                    "vl_rec_backend": "mlx-vlm-server",
                    "vl_rec_server_url": self._mlx_vlm_url,
                    "vl_rec_api_model_name": self._mlx_vlm_model,
                }
            )
        else:
            logger.info(
                "PaddleOCR-VL running in local inference mode (device=%s). "
                "Consider starting mlx_vlm.server for faster inference.",
                self._device,
            )

        logger.info("Loading PaddleOCR-VL pipeline (this may take a moment)…")
        self._pipeline = PaddleOCRVL(**kwargs)
        return self._pipeline

    def is_available(self) -> bool:
        try:
            import paddleocr  # noqa: F401
            return True
        except ImportError:
            return False

    # ------------------------------------------------------------------
    # Core extraction
    # ------------------------------------------------------------------

    def extract(self, input_source: Union[str, Path], **kwargs: Any) -> Document:
        input_path = Path(input_source)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        pipeline = self._get_pipeline()
        results_generator = pipeline.predict(input=str(input_path))

        pages: List[DocumentPage] = []
        for page_idx, res in enumerate(results_generator):
            blocks = self._parse_blocks(res)

            # PaddleOCRVLResult.markdown is a dict with 'markdown_texts' key
            page_md = ""
            try:
                md_data = res.markdown
                if isinstance(md_data, dict):
                    page_md = md_data.get("markdown_texts", "")
                elif isinstance(md_data, str):
                    page_md = md_data
            except Exception:
                pass

            # Build text from blocks; fall back to markdown content
            page_text = "\n".join(b.text for b in blocks)
            if not page_text and page_md:
                # Strip basic markdown formatting to produce plain text
                import re
                page_text = re.sub(r"[#*_`>|]", "", page_md).strip()
            if not page_md:
                page_md = "\n\n".join(b.text for b in blocks)

            pages.append(
                DocumentPage(
                    page_number=page_idx + 1,
                    blocks=blocks,
                    text=page_text,
                    markdown=page_md,
                )
            )

        return Document(pages=pages)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_blocks(res: Any) -> List[Block]:
        """Extract standardised Block objects from a PaddleOCR result.

        PaddleOCRVLResult is a dict subclass; the core data lives under
        ``res['res']['parsing_res_list']``.
        """
        try:
            inner = res["res"]
            parsed_res = inner.get("parsing_res_list", [])
        except (KeyError, TypeError):
            parsed_res = []

        blocks: List[Block] = []
        for item in parsed_res:
            raw_bbox = item.get("block_bbox", (0, 0, 0, 0))
            blocks.append(
                Block(
                    block_type=item.get("block_label", "text"),
                    text=item.get("block_content", ""),
                    bbox=tuple(float(v) for v in raw_bbox),
                    confidence=1.0,
                    extra_data=item,
                )
            )
        return blocks
