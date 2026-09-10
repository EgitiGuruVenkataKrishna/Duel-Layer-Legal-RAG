import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from tqdm import tqdm
from src.config import PROCESSED_DIR
from src.schema import Chunk, ChunkMetadata
from src.indexing.vector_store import VectorStore
from src.indexing.keyword_store import KeywordStore
from src.embeddings.embedder import default_embedder
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def run_indexing():
    vector_store = VectorStore()
    keyword_store = KeywordStore()
    
    json_files = list(PROCESSED_DIR.glob("*.json"))
    
    total_chunks_indexed = 0
    skipped_duplicates = 0  # In a full implementation, you might track this by diffing against existing DB
    
    for json_path in tqdm(json_files, desc="Indexing Documents"):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            chunks = [Chunk(**c) for c in data]
            
            # Embed
            texts_to_embed = [c.contextual_text for c in chunks]
            embeddings = default_embedder.embed(texts_to_embed)
            
            # Upsert Vector Store
            vector_store.upsert_chunks(chunks, embeddings)
            
            # Upsert BM25 Store
            keyword_store.upsert_chunks(chunks)
            
            total_chunks_indexed += len(chunks)
            
        except Exception as e:
            logging.error(f"Failed to index {json_path.name}: {e}")

    logging.info(f"Indexing Complete. Chunks Indexed: {total_chunks_indexed}")

if __name__ == "__main__":
    run_indexing()
