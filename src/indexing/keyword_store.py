import pickle
import os
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from src.config import BM25_INDEX_PATH, BM25_DOCS_PATH
from src.schema import Chunk

class KeywordStore:
    def __init__(self):
        self.bm25 = None
        self.docs = {} # mapping from chunk_id to dict with text and metadata
        self._load()
        
    def _load(self):
        if BM25_DOCS_PATH.exists():
            with open(BM25_DOCS_PATH, 'rb') as f:
                self.docs = pickle.load(f)
        
        if BM25_INDEX_PATH.exists():
            with open(BM25_INDEX_PATH, 'rb') as f:
                self.bm25 = pickle.load(f)
        elif self.docs:
            self._rebuild_index()

    def _save(self):
        with open(BM25_DOCS_PATH, 'wb') as f:
            pickle.dump(self.docs, f)
        if self.bm25:
            with open(BM25_INDEX_PATH, 'wb') as f:
                pickle.dump(self.bm25, f)
                
    def _rebuild_index(self):
        if not self.docs:
            self.bm25 = None
            return
            
        corpus = [doc["text"] for doc in self.docs.values()]
        tokenized_corpus = [doc.split(" ") for doc in corpus] # simple whitespace tokenization for BM25
        self.bm25 = BM25Okapi(tokenized_corpus)
        self._save()

    def upsert_chunks(self, chunks: List[Chunk]):
        """Adds or updates chunks in the BM25 corpus."""
        updated = False
        for chunk in chunks:
            # We index the raw text for keyword search
            if chunk.chunk_id not in self.docs or self.docs[chunk.chunk_id]["text"] != chunk.text:
                self.docs[chunk.chunk_id] = {
                    "text": chunk.text,
                    "metadata": chunk.metadata.model_dump(exclude_none=True)
                }
                updated = True
                
        if updated:
            self._rebuild_index()

    def search(self, query: str, n_results: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.bm25 or not self.docs:
            return []
            
        tokenized_query = query.split(" ")
        scores = self.bm25.get_scores(tokenized_query)
        
        # We need to map scores back to chunk_ids
        chunk_ids = list(self.docs.keys())
        
        results = []
        for i, score in enumerate(scores):
            if score > 0:
                chunk_id = chunk_ids[i]
                doc_meta = self.docs[chunk_id]["metadata"]
                
                # Apply naive filtering
                match = True
                if filters:
                    for k, v in filters.items():
                        if doc_meta.get(k) != v:
                            match = False
                            break
                            
                if match:
                    results.append({
                        "chunk_id": chunk_id,
                        "score": float(score),
                        "metadata": doc_meta,
                        "text": self.docs[chunk_id]["text"]
                    })
                    
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:n_results]
