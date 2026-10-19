from src.nyayasetu.retrieval.bm25_search import BM25SearchEngine
from src.nyayasetu.retrieval.dense_search import DenseSearchEngine


def build_all_indices():
    print("Building BM25 sparse index...")
    bm25 = BM25SearchEngine()
    bm25.build_index()

    print("Building Dense FAISS index (sentence-transformers/all-MiniLM-L6-v2)...")
    dense = DenseSearchEngine(model_name="sentence-transformers/all-MiniLM-L6-v2")
    dense.build_index()

    print("All retrieval indices built successfully!")


if __name__ == "__main__":
    build_all_indices()
