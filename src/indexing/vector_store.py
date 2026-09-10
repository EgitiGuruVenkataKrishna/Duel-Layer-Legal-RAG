import chromadb
from typing import List, Dict, Any, Optional
from src.config import CHROMA_DB_DIR
from src.schema import Chunk

class VectorStore:
    def __init__(self, collection_name: str = "legalground_chunks"):
        self.client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        self.collection = self.client.get_or_create_collection(name=collection_name)
        
    def upsert_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]):
        """Upserts chunks and their embeddings into ChromaDB."""
        if not chunks:
            return
            
        ids = [chunk.chunk_id for chunk in chunks]
        texts = [chunk.contextual_text for chunk in chunks] # We store contextual text
        
        # Chroma requires metadata values to be str, int, float, or bool
        metadatas = []
        for chunk in chunks:
            meta = chunk.metadata.model_dump(exclude_none=True)
            # Ensure all values are primitives
            for k, v in meta.items():
                if not isinstance(v, (str, int, float, bool)):
                    meta[k] = str(v)
            # Add raw text for retrieval purposes if needed, though usually we can fetch it elsewhere.
            # We'll include raw text in metadata so it's retrievable from Chroma directly.
            meta["raw_text"] = chunk.text
            metadatas.append(meta)
            
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

    def search(self, query_embedding: List[float], n_results: int = 5, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Searches the vector store."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["metadatas", "documents", "distances"]
        )
        
        # Format results
        formatted_results = []
        if results and results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "chunk_id": results["ids"][0][i],
                    "score": 1.0 - results["distances"][0][i], # Convert distance to similarity score
                    "metadata": results["metadatas"][0][i],
                    "contextual_text": results["documents"][0][i],
                    "text": results["metadatas"][0][i].get("raw_text", "")
                })
                
        return formatted_results
