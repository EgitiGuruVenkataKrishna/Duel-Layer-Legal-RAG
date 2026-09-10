import re
import hashlib
from typing import List, Dict, Any, Tuple
from src.schema import Chunk, ChunkMetadata
from src.embeddings.contextualizer import contextualize

def generate_chunk_id(source_doc: str, section: str, index: int = 0) -> str:
    """Generates a stable, deterministic hash for a chunk."""
    unique_string = f"{source_doc}::{section}::{index}"
    return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()

def chunk_statute(text: str, metadata_template: Dict[str, Any]) -> List[Chunk]:
    """
    Splits statute text at section boundaries.
    Looks for 'Section 1', 'Section 1.', etc.
    """
    # Regex to find section headers like "Section 1", "Section 1.", "1. " (at start of line)
    pattern = re.compile(r'(?i)^\s*(?:Section\s+\d+[a-z]?\.?|\d+\.\s)', re.MULTILINE)
    
    matches = list(pattern.finditer(text))
    chunks = []
    
    if not matches:
        # If no sections found, treat as one chunk
        chunks.append(_create_chunk(text, metadata_template, metadata_template.get("section_or_citation", "Full Text"), 0))
        return chunks
        
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i+1].start() if i + 1 < len(matches) else len(text)
        
        chunk_text = text[start:end].strip()
        if not chunk_text:
            continue
            
        section_name = match.group().strip()
        # Clean trailing dot or whitespace for section name
        section_name = re.sub(r'[\.\s]+$', '', section_name)
        
        chunks.append(_create_chunk(chunk_text, metadata_template, section_name, i))
        
    return chunks

def chunk_judgment(text: str, metadata_template: Dict[str, Any]) -> List[Chunk]:
    """
    Splits judgment text at paragraph boundaries.
    Looks for paragraph numbers like '1.', '2.', etc. at the start of a line.
    """
    pattern = re.compile(r'^\s*(?:\d+\.|\[\d+\])\s', re.MULTILINE)
    
    matches = list(pattern.finditer(text))
    chunks = []
    
    if not matches:
        chunks.append(_create_chunk(text, metadata_template, metadata_template.get("section_or_citation", "Full Text"), 0))
        return chunks
        
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i+1].start() if i + 1 < len(matches) else len(text)
        
        chunk_text = text[start:end].strip()
        if not chunk_text:
            continue
            
        para_name = match.group().strip()
        chunks.append(_create_chunk(chunk_text, metadata_template, f"Para {para_name}", i))
        
    return chunks

def _create_chunk(text: str, metadata_template: Dict[str, Any], section_name: str, index: int) -> Chunk:
    """Helper to create a Chunk object with contextualized text."""
    meta = metadata_template.copy()
    meta["section_or_citation"] = section_name
    
    chunk_id = generate_chunk_id(meta["source_doc"], section_name, index)
    
    # We apply contextualization here so it's ready for embeddings
    contextual_text = contextualize(meta, text)
    
    return Chunk(
        chunk_id=chunk_id,
        text=text,
        contextual_text=contextual_text,
        metadata=ChunkMetadata(**meta)
    )
