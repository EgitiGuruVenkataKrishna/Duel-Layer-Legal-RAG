import sys
import os
from pathlib import Path

# Add the project root to sys.path so we can import src
sys.path.append(str(Path(__file__).resolve().parent.parent))

from tqdm import tqdm
from src.config import RAW_DIR, PROCESSED_DIR
from src.ingestion.pdf_loader import process_pdf
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def run_ingestion():
    stats = {
        "statutes_processed": 0,
        "judgments_processed": 0,
        "total_chunks": 0
    }
    
    # Process statutes
    statutes_dir = RAW_DIR / "statutes"
    statute_files = list(statutes_dir.glob("*.pdf"))
    for pdf_path in tqdm(statute_files, desc="Processing Statutes"):
        try:
            chunks = process_pdf(pdf_path, doc_type="statute", metadata_override={"act_or_court": "Indian Penal Code"})
            _save_chunks(chunks, pdf_path.stem)
            stats["statutes_processed"] += 1
            stats["total_chunks"] += len(chunks)
        except Exception as e:
            logging.error(f"Failed to process statute {pdf_path.name}: {e}")

    # Process judgments
    judgments_dir = RAW_DIR / "judgments"
    judgment_files = list(judgments_dir.glob("*.pdf"))
    for pdf_path in tqdm(judgment_files, desc="Processing Judgments"):
        try:
            chunks = process_pdf(pdf_path, doc_type="judgment", metadata_override={"act_or_court": "Supreme Court of India"})
            _save_chunks(chunks, pdf_path.stem)
            stats["judgments_processed"] += 1
            stats["total_chunks"] += len(chunks)
        except Exception as e:
            logging.error(f"Failed to process judgment {pdf_path.name}: {e}")

    logging.info(f"Ingestion Complete. Stats: {stats}")

def _save_chunks(chunks, stem_name):
    # We save chunks as JSON for intermediate review and indexing
    if not chunks:
        return
        
    out_path = PROCESSED_DIR / f"{stem_name}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        # Pydantic 2.x
        import json
        json.dump([c.model_dump() for c in chunks], f, indent=2)

if __name__ == "__main__":
    run_ingestion()
