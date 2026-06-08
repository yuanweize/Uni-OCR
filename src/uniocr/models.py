from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class Block:
    """A recognized block of text/table/figure."""
    block_type: str  # e.g., 'text', 'table', 'figure', 'title'
    text: str
    bbox: Tuple[float, float, float, float]  # [x1, y1, x2, y2]
    confidence: float
    polygon_points: Optional[List[Tuple[float, float]]] = None
    extra_data: Any = None  # Original raw data from the engine if needed

    def to_dict(self) -> Dict[str, Any]:
        """Serialize block to a JSON-compatible dict."""
        d: Dict[str, Any] = {
            "block_type": self.block_type,
            "text": self.text,
            "bbox": list(self.bbox),
            "confidence": self.confidence,
        }
        if self.polygon_points:
            d["polygon_points"] = [list(p) for p in self.polygon_points]
        return d

@dataclass
class DocumentPage:
    """A single page of a document."""
    page_number: int
    blocks: List[Block] = field(default_factory=list)
    text: str = ""
    markdown: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize page to a JSON-compatible dict."""
        return {
            "page_number": self.page_number,
            "text": self.text,
            "markdown": self.markdown,
            "blocks": [b.to_dict() for b in self.blocks],
        }

@dataclass
class Document:
    """A completely parsed document, which could contain multiple pages."""
    pages: List[DocumentPage] = field(default_factory=list)
    engine_name: str = ""
    
    @property
    def text(self) -> str:
        """Returns the full text of all pages combined."""
        return "\n\n".join(page.text for page in self.pages)
        
    @property
    def markdown(self) -> str:
        """Returns the full markdown of all pages combined."""
        return "\n\n".join(page.markdown for page in self.pages)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize entire document to a JSON-compatible dict."""
        return {
            "engine": self.engine_name,
            "page_count": len(self.pages),
            "text": self.text,
            "markdown": self.markdown,
            "pages": [p.to_dict() for p in self.pages],
        }
