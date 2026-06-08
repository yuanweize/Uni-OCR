import os
import subprocess
import json
from pathlib import Path
from typing import Any, List, Union

from .base import BaseOCREngine
from ..models import Document, DocumentPage, Block


class AppleVisionAdapter(BaseOCREngine):
    """
    Apple Vision Framework OCR Adapter.
    Uses a subprocess calling a Swift/ObjC helper via `osascript` or pyobjc.
    On macOS with pyobjc-framework-Vision installed, uses native bindings.
    """

    def __init__(self) -> None:
        self._vision_mod = None
        self._foundation_mod = None
        if not self.is_available():
            raise RuntimeError(
                "Apple Vision framework is not available. "
                "Install pyobjc-framework-Vision on macOS, or run on a Mac."
            )
        import Vision
        import Foundation
        self._vision_mod = Vision
        self._foundation_mod = Foundation

    def is_available(self) -> bool:
        if os.uname().sysname != "Darwin":
            return False
        try:
            import Vision  # noqa: F401
            import Foundation  # noqa: F401
            return True
        except ImportError:
            return False

    def extract(self, input_source: Union[str, Path], **kwargs: Any) -> Document:
        input_path = Path(input_source)
        if not input_path.exists():
            raise FileNotFoundError(f"Image file not found: {input_path}")

        Foundation = self._foundation_mod
        Vision = self._vision_mod

        url = Foundation.NSURL.fileURLWithPath_(str(input_path.resolve()))
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)

        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)

        languages = kwargs.get("languages", ["en-US", "zh-Hans"])
        request.setRecognitionLanguages_(languages)

        success, error = handler.performRequests_error_([request], None)
        if not success:
            raise RuntimeError(f"Apple Vision request failed: {error}")

        results = request.results()
        blocks: List[Block] = []
        page_text_lines: List[str] = []

        for observation in results:
            candidate = observation.topCandidates_(1).firstObject()
            if candidate is None:
                continue
            text = candidate.string()
            confidence = float(candidate.confidence())

            rect = observation.boundingBox()
            x_min = float(rect.origin.x)
            y_min = float(rect.origin.y)
            x_max = x_min + float(rect.size.width)
            y_max = y_min + float(rect.size.height)

            blocks.append(
                Block(
                    block_type="text",
                    text=text,
                    bbox=(x_min, y_min, x_max, y_max),
                    confidence=confidence,
                )
            )
            page_text_lines.append(text)

        full_text = "\n".join(page_text_lines)
        page = DocumentPage(
            page_number=1,
            blocks=blocks,
            text=full_text,
            markdown=full_text,
        )
        return Document(pages=[page])
