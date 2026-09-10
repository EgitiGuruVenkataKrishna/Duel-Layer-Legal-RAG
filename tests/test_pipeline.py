import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.ingestion.chunker import chunk_statute, generate_chunk_id
from src.embeddings.contextualizer import contextualize
from src.indexing.keyword_store import KeywordStore

def test_generate_chunk_id_determinism():
    id1 = generate_chunk_id("doc1.pdf", "Section 1", 0)
    id2 = generate_chunk_id("doc1.pdf", "Section 1", 0)
    id3 = generate_chunk_id("doc1.pdf", "Section 2", 0)
    
    assert id1 == id2
    assert id1 != id3

def test_contextualize():
    metadata = {
        "act_or_court": "IPC",
        "section_or_citation": "Section 420",
        "jurisdiction": "India"
    }
    text = "Whoever cheats and thereby dishonestly induces..."
    result = contextualize(metadata, text)
    
    assert "[IPC, Section 420, Jurisdiction: India]" in result
    assert "Whoever cheats" in result

def test_chunk_statute():
    text = "Section 1. Short title.\nThis act may be called IPC.\nSection 2. Punishment.\nEvery person..."
    metadata = {
        "source_doc": "test.pdf",
        "jurisdiction": "India",
        "act_or_court": "IPC",
        "doc_type": "statute",
        "section_or_citation": "Unknown"
    }
    
    chunks = chunk_statute(text, metadata)
    assert len(chunks) == 2
    assert chunks[0].metadata.section_or_citation == "Section 1."
    assert "Short title." in chunks[0].text
    assert chunks[1].metadata.section_or_citation == "Section 2."
    assert "Every person" in chunks[1].text
    assert chunks[0].chunk_id != chunks[1].chunk_id

def test_keyword_store_mock():
    # To avoid writing to disk in test, we can mock or just create a temporary one, 
    # but the simplest test is just checking schema.
    pass
