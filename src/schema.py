from typing import Optional
from pydantic import BaseModel, Field

class ChunkMetadata(BaseModel):
    source_doc: str
    source_url: Optional[str] = None
    jurisdiction: str
    act_or_court: str
    section_or_citation: str
    date_enacted: Optional[str] = None
    date_judgment: Optional[str] = None
    effective_until: Optional[str] = None
    doc_type: str = Field(pattern="^(statute|judgment)$")
    
    # Store reference to parent section for sub-clauses if split
    parent_section: Optional[str] = None

class Chunk(BaseModel):
    chunk_id: str
    text: str
    contextual_text: str
    metadata: ChunkMetadata
