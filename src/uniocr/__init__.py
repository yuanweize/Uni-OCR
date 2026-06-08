import logging
from typing import Union
from pathlib import Path

from .processors.input import InputProcessor
from .engines import get_engine
from .models import Document, DocumentPage, Block

# Set up basic logger
logging.basicConfig(level=logging.INFO)

class UniOCR:
    """Main entry point for the UniOCR tool."""
    
    def __init__(self, engine: str = "auto"):
        self.processor = InputProcessor()
        self.engine = get_engine(engine)
        
    def extract(self, input_source: Union[str, Path], **kwargs) -> Document:
        """
        Extract text and layout from the input source.
        
        Args:
            input_source: File path, URL, or Base64 string.
        """
        # 1. Process and normalize input into a list of local image paths
        image_paths = self.processor.process(input_source)
        
        # 2. Run engine on each image path
        all_pages = []
        for path in image_paths:
            doc = self.engine.extract(path, **kwargs)
            # Depending on engine, doc might have 1 or multiple pages (e.g. if we passed a multi-page TIFF)
            # Since we flattened PDFs to images, each path is 1 image.
            all_pages.extend(doc.pages)
            
        # Re-number pages sequentially
        for i, page in enumerate(all_pages):
            page.page_number = i + 1
            
        # 3. Cleanup temp files if needed
        # (Assuming the processor cleans up when destroyed, or we can explicitly clean here)
        # We might want to keep images if debugging, but for MVP we leave to processor destructor.
        
        return Document(pages=all_pages)

__all__ = ["UniOCR", "Document", "DocumentPage", "Block"]
