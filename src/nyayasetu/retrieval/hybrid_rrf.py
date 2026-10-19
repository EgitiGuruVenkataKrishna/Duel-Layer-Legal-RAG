from typing import Any, Dict, List, Tuple
from src.nyayasetu.retrieval.bm25_search import BM25SearchEngine
from src.nyayasetu.retrieval.dense_search import DenseSearchEngine


class HybridRRFSearchEngine:
    """
    Reciprocal Rank Fusion (RRF) combining Sparse BM25 and Dense FAISS retrieval.
    Formula: RRF_score(d) = sum( 1 / (60 + rank_m(d)) )
    """

    def __init__(
        self,
        bm25_engine: BM25SearchEngine | None = None,
        dense_engine: DenseSearchEngine | None = None,
        k: int = 60,
    ):
        self.bm25_engine = bm25_engine or BM25SearchEngine()
        self.dense_engine = dense_engine or DenseSearchEngine()
        self.k = k

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        # Retrieve candidates from both systems
        bm25_results = self.bm25_engine.search(query, top_k=top_k * 2)
        dense_results = self.dense_engine.search(query, top_k=top_k * 2)

        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        # Process BM25 ranks
        for rank, (doc, _) in enumerate(bm25_results):
            doc_id = doc["id"]
            doc_map[doc_id] = doc
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (self.k + rank + 1))

        # Process Dense ranks
        for rank, (doc, _) in enumerate(dense_results):
            doc_id = doc["id"]
            doc_map[doc_id] = doc
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (self.k + rank + 1))

        # Sort descending by fused score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda doc_id: rrf_scores[doc_id], reverse=True)

        results = []
        for doc_id in sorted_ids[:top_k]:
            results.append((doc_map[doc_id], rrf_scores[doc_id]))

        return results


if __name__ == "__main__":
    hybrid = HybridRRFSearchEngine()
    res = hybrid.search("theft punishment community service under BNS", top_k=3)
    print("Top Hybrid RRF results:")
    for doc, score in res:
        print(f"[{doc['id']}] {doc['title']} (RRF: {score:.5f})")
