import os
from pathlib import Path
from typing import Any, Union

from .base import BaseOCREngine
from ..models import Document, DocumentPage, Block

class PaddleOCRVLAdapter(BaseOCREngine):
    """
    PaddleOCR-VL Adapter.
    Uses PaddleOCRVL internally for comprehensive document analysis.
    """
    def __init__(self):
        if not self.is_available():
            raise RuntimeError("PaddleOCR dependencies are not installed.")
        from paddleocr import PaddleOCRVL
        # Assume CPU device for local fallback if not configured otherwise
        self.pipeline = PaddleOCRVL(device="cpu")

    def is_available(self) -> bool:
        try:
            import paddleocr
            return True
        except ImportError:
            return False

    def extract(self, input_source: Union[str, Path], **kwargs: Any) -> Document:
        input_path = Path(input_source)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # PaddleOCR pipeline returns a generator of results per page
        results_generator = self.pipeline.predict(input=str(input_path))
        
        pages = []
        for i, res in enumerate(results_generator):
            blocks = []
            
            # The result object contains layout analysis blocks and text
            # Usually res.res['layout_det_res']['boxes'] and res.res['parsing_res_list']
            # PaddleOCRVL result structure varies slightly, but typically provides markdown
            
            # For this MVP we just dump the raw text / markdown into our standard structure
            # and try to extract basic blocks if they exist.
            
            parsed_res = res.res.get('parsing_res_list', [])
            for block_data in parsed_res:
                bbox = block_data.get('block_bbox', (0,0,0,0))
                blocks.append(Block(
                    block_type=block_data.get('block_label', 'text'),
                    text=block_data.get('block_content', ''),
                    bbox=tuple(bbox),
                    confidence=1.0, # PaddleOCRVL block conf isn't always surfaced cleanly here
                    extra_data=block_data
                ))
            
            page = DocumentPage(
                page_number=i + 1,
                blocks=blocks,
                text=res.get_text() if hasattr(res, 'get_text') else "", 
                markdown=res.get_markdown() if hasattr(res, 'get_markdown') else str(res.res)
            )
            pages.append(page)

        return Document(pages=pages)
