from pydantic import BaseModel
from typing import List, Optional, Literal

class DocumentChunk(BaseModel):
    id: str
    content: str
    source: str
    page: Optional[int] = None
    type: Literal["text", "table", "data_row"]
    quarter: Optional[str] = None
    
class SearchResult(BaseModel):
    chunk: DocumentChunk
    score: float
