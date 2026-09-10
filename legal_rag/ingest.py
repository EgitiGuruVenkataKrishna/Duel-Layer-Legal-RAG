import os
import glob
from legal_rag.ingestion.parser import LegalPDFParser
from legal_rag.retrieval.hybrid_store import DualHybridStore

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    data_dir = os.path.join(project_root, "data", "raw")
    
    statutes_dir = os.path.join(data_dir, "statutes")
    precedents_dir = os.path.join(data_dir, "judgments")
    
    # Ensure directories exist
    os.makedirs(statutes_dir, exist_ok=True)
    os.makedirs(precedents_dir, exist_ok=True)
    
    parser = LegalPDFParser()
    store = DualHybridStore()
    
    print(f"Scanning for statute PDFs in: {statutes_dir}")
    statute_chunks = []
    for pdf_file in glob.glob(os.path.join(statutes_dir, "*.pdf")):
        print(f"Parsing {pdf_file}...")
        chunks = parser.parse_pdf(pdf_file)
        statute_chunks.extend(chunks)
        
    print(f"Scanning for precedent PDFs in: {precedents_dir}")
    precedent_chunks = []
    for pdf_file in glob.glob(os.path.join(precedents_dir, "*.pdf")):
        print(f"Parsing {pdf_file}...")
        chunks = parser.parse_pdf(pdf_file)
        precedent_chunks.extend(chunks)
        
    if statute_chunks:
        print(f"Ingesting {len(statute_chunks)} statute chunks into FAISS/BM25...")
        store.ingest_statutes(statute_chunks)
    else:
        print("No statute PDFs found. Place your BNS, BNSS, BSA, Constitution PDFs in data/raw/statutes/")
        
    if precedent_chunks:
        print(f"Ingesting {len(precedent_chunks)} precedent chunks into FAISS/BM25...")
        store.ingest_precedents(precedent_chunks)
    else:
        print("No precedent PDFs found. Place your Supreme Court Judgment PDFs in data/raw/judgments/")
        
    if statute_chunks or precedent_chunks:
        db_path = os.path.join(base_dir, "db")
        print(f"Saving indices to {db_path}...")
        store.save_local(db_path)
        print("Ingestion complete!")

if __name__ == "__main__":
    main()
