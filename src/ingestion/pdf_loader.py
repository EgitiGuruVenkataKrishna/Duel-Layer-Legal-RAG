import os
import pdfplumber
from pathlib import Path
from typing import List, Dict, Any

from src.schema import Chunk
from src.ingestion.cleaner import clean_text
from src.ingestion.chunker import chunk_statute, chunk_judgment

def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extracts raw text from a PDF file."""
    text_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_pages.append(page_text)
    return "\n\n".join(text_pages)

def process_pdf(pdf_path: str | Path, doc_type: str, metadata_override: Dict[str, Any] = None) -> List[Chunk]:
    """
    Extracts text, cleans it, and chunks it according to document type.
    """
    pdf_path = Path(pdf_path)
    
    # Extract
    raw_text = extract_text_from_pdf(pdf_path)
    
    # Clean
    cleaned_text = clean_text(raw_text)
    
    # Base metadata
    metadata = {
        "source_doc": pdf_path.name,
        "jurisdiction": "India", # Default, can be overridden
        "act_or_court": "Unknown", # Should be extracted or provided
        "section_or_citation": "Unknown",
        "doc_type": doc_type
    }
    if metadata_override:
        metadata.update(metadata_override)
        
    # Chunk
    if doc_type == "statute":
        chunks = chunk_statute(cleaned_text, metadata)
    elif doc_type == "judgment":
        chunks = chunk_judgment(cleaned_text, metadata)
    else:
        raise ValueError(f"Unknown doc_type: {doc_type}")
        
    return chunks
