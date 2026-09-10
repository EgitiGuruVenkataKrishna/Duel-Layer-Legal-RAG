import numpy as np
import os
import pickle
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

class DualHybridStore:
    """
    Manages separated dense (FAISS) and sparse (BM25) indexes for
    Statutes and Precedents to avoid context cross-contamination.
    Uses Reciprocal Rank Fusion (RRF) to combine results.
    """
    def __init__(self, embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)
        
        # Separate stores
        self.statutes_faiss = None
        self.statutes_bm25 = None
        
        self.precedents_faiss = None
        self.precedents_bm25 = None

    def ingest_statutes(self, chunks: List[Dict[str, Any]]):
        docs = [
            Document(
                page_content=chunk["text"],
                metadata={k: v for k, v in chunk.items() if k != "text"}
            )
            for chunk in chunks
        ]
        self.statutes_faiss = FAISS.from_documents(docs, self.embeddings)
        self.statutes_bm25 = BM25Retriever.from_documents(docs)

    def ingest_precedents(self, chunks: List[Dict[str, Any]]):
        docs = [
            Document(
                page_content=chunk["text"],
                metadata={k: v for k, v in chunk.items() if k != "text"}
            )
            for chunk in chunks
        ]
        self.precedents_faiss = FAISS.from_documents(docs, self.embeddings)
        self.precedents_bm25 = BM25Retriever.from_documents(docs)

    def _rrf(self, dense_results: List[Document], sparse_results: List[Document], k: int = 60) -> List[Document]:
        """
        Reciprocal Rank Fusion formula: RRF_score(doc) = sum(1 / (k + rank(doc)))
        """
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}
        
        def add_to_scores(results: List[Document]):
            for rank, doc in enumerate(results):
                # Use page_content as unique key to fuse duplicates between dense and sparse
                doc_key = doc.page_content 
                doc_map[doc_key] = doc
                if doc_key not in rrf_scores:
                    rrf_scores[doc_key] = 0.0
                rrf_scores[doc_key] += 1.0 / (k + rank + 1)
                
        add_to_scores(dense_results)
        add_to_scores(sparse_results)
        
        # Sort by RRF score descending
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [doc_map[key] for key, score in sorted_docs]

    def retrieve(self, query: str, domain: str = "statutes", top_k: int = 5) -> List[Document]:
        """
        Retrieve documents using Hybrid Search (FAISS + BM25) and RRF.
        domain: 'statutes' or 'precedents'
        """
        if domain == "statutes":
            faiss_store = self.statutes_faiss
            bm25_store = self.statutes_bm25
        elif domain == "precedents":
            faiss_store = self.precedents_faiss
            bm25_store = self.precedents_bm25
        else:
            raise ValueError("Domain must be either 'statutes' or 'precedents'")
            
        if not faiss_store or not bm25_store:
            return []
            
        # Get dense results
        dense_results = faiss_store.similarity_search(query, k=top_k * 2)
        
        # Get sparse results
        bm25_store.k = top_k * 2
        sparse_results = bm25_store.invoke(query)
        
        # Fuse
        fused = self._rrf(dense_results, sparse_results)
        
        return fused[:top_k]

    def save_local(self, folder_path: str):
        """Save FAISS and BM25 indices to disk."""
        os.makedirs(folder_path, exist_ok=True)
        if self.statutes_faiss:
            self.statutes_faiss.save_local(os.path.join(folder_path, "statutes_faiss"))
        if self.precedents_faiss:
            self.precedents_faiss.save_local(os.path.join(folder_path, "precedents_faiss"))
            
        with open(os.path.join(folder_path, "bm25_indices.pkl"), "wb") as f:
            pickle.dump({
                "statutes_bm25": self.statutes_bm25,
                "precedents_bm25": self.precedents_bm25
            }, f)

    def load_local(self, folder_path: str):
        """Load FAISS and BM25 indices from disk."""
        statutes_faiss_path = os.path.join(folder_path, "statutes_faiss")
        if os.path.exists(statutes_faiss_path):
            self.statutes_faiss = FAISS.load_local(statutes_faiss_path, self.embeddings, allow_dangerous_deserialization=True)
            
        precedents_faiss_path = os.path.join(folder_path, "precedents_faiss")
        if os.path.exists(precedents_faiss_path):
            self.precedents_faiss = FAISS.load_local(precedents_faiss_path, self.embeddings, allow_dangerous_deserialization=True)
            
        bm25_path = os.path.join(folder_path, "bm25_indices.pkl")
        if os.path.exists(bm25_path):
            with open(bm25_path, "rb") as f:
                data = pickle.load(f)
                self.statutes_bm25 = data.get("statutes_bm25")
                self.precedents_bm25 = data.get("precedents_bm25")
