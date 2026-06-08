from typing import Optional
import logging

from .base import BaseOCREngine

logger = logging.getLogger(__name__)

def get_engine(engine_name: str = "auto") -> BaseOCREngine:
    """
    Factory function to get the appropriate OCR engine.
    If engine_name is 'auto', it tries PaddleOCR first, then Apple Vision.
    """
    if engine_name in ("paddle", "auto"):
        try:
            from .paddle import PaddleOCRVLAdapter
            adapter = PaddleOCRVLAdapter()
            if adapter.is_available():
                logger.info("Using PaddleOCRVL Engine.")
                return adapter
        except Exception as e:
            if engine_name == "paddle":
                raise RuntimeError(f"PaddleOCR explicitly requested but unavailable: {e}")
            logger.debug(f"PaddleOCRVL unavailable: {e}")
            
    if engine_name in ("apple", "auto"):
        try:
            from .apple_vision import AppleVisionAdapter
            adapter = AppleVisionAdapter()
            if adapter.is_available():
                logger.info("Using Apple Vision Engine.")
                return adapter
        except Exception as e:
            if engine_name == "apple":
                raise RuntimeError(f"Apple Vision explicitly requested but unavailable: {e}")
            logger.debug(f"Apple Vision unavailable: {e}")

    raise RuntimeError(f"No suitable OCR engine found for '{engine_name}'.")

