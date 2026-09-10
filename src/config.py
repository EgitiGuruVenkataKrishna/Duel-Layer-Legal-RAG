import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EVAL_DIR = DATA_DIR / "eval"

# Index paths
INDEX_DIR = BASE_DIR / "indexes"
CHROMA_DB_DIR = INDEX_DIR / "chroma"
BM25_INDEX_PATH = INDEX_DIR / "bm25_index.pkl"
BM25_DOCS_PATH = INDEX_DIR / "bm25_docs.pkl"

# Model settings
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# Chunking settings
# We try to split at section/clause boundaries. These token limits are guidelines.
TARGET_CHUNK_TOKENS = 150
MAX_CHUNK_TOKENS = 400

# Ensure directories exist
for path in [RAW_DIR / "statutes", RAW_DIR / "judgments", PROCESSED_DIR, EVAL_DIR, CHROMA_DB_DIR]:
    path.mkdir(parents=True, exist_ok=True)
