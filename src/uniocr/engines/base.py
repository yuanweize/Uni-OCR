from abc import ABC, abstractmethod
from typing import Union, List, Any
from pathlib import Path

from ..models import Document

class BaseOCREngine(ABC):
    """Abstract base class for all OCR engines in UniOCR."""
    
    @abstractmethod
    def extract(self, input_source: Union[str, Path], **kwargs: Any) -> Document:
        """
        Extract structured information from the given input source.
        
        Args:
            input_source: Can be a local file path, URL, or base64 string.
                          The Input Processor should ideally normalize this to a
                          local file or image array before it reaches the engine,
                          but the engine should be robust.
            **kwargs: Engine-specific parameters (e.g., language, fast_mode).
            
        Returns:
            Document: A unified document object containing the parsed blocks, 
                      text, and markdown.
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the engine is currently available in the environment.
        Used by the dispatcher to fallback if needed.
        """
        pass
