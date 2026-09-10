from typing import List, Dict, Any, Optional
from src.indexing.vector_store import VectorStore
from src.indexing.keyword_store import KeywordStore
from src.embeddings.embedder import default_embedder

class HybridSearcher:
    def __init__(self):
        self.vector_store = VectorStore()
        self.keyword_store = KeywordStore()
        self.embedder = default_embedder
        
    def search(self, query: str, filters: Optional[Dict[str, Any]] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        # 1. Dense query
        query_embedding = self.embedder.embed([query])[0]
        dense_results = self.vector_store.search(query_embedding, n_results=top_k * 2, where=filters)
        
        # 2. Sparse query
        sparse_results = self.keyword_store.search(query, n_results=top_k * 2, filters=filters)
        
        # 3. Merge with RRF (Reciprocal Rank Fusion)
        rrf_scores = {}
        merged_results = {}
        
        # Helper to apply RRF
        def apply_rrf(results, weight=60):
            for rank, res in enumerate(results):
                chunk_id = res["chunk_id"]
                if chunk_id not in rrf_scores:
                    rrf_scores[chunk_id] = 0.0
                    merged_results[chunk_id] = res
                # RRF score formula: 1 / (weight + rank)
                rrf_scores[chunk_id] += 1.0 / (weight + rank + 1)

        apply_rrf(dense_results)
        apply_rrf(sparse_results)
        
        # Sort by RRF score descending
        sorted_results = sorted(
            [{"chunk_id": k, "rrf_score": v, **merged_results[k]} for k, v in rrf_scores.items()],
            key=lambda x: x["rrf_score"],
            reverse=True
        )
        
        return sorted_results[:top_k]
