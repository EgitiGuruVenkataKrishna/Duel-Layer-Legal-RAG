import os
import pickle
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class DenseSearchEngine:
    """
    Dense semantic retrieval using SentenceTransformers and FAISS vector indices.
    Supports both baseline MiniLM (v0) and advanced dense models (bge-m3/bge-small).
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        index_dir: str | None = None,
        db_path: str | None = None,
    ):
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        model_slug = model_name.split("/")[-1].replace("-", "_")
        if index_dir is None:
            index_dir = str(project_root / "data" / "processed" / f"faiss_{model_slug}")
        if db_path is None:
            db_path = str(project_root / "data" / "processed" / "nyayasetu.db")

        self.model_name = model_name
        self.index_dir = Path(index_dir)
        self.db_path = db_path
        self.model: SentenceTransformer | None = None
        self.index: faiss.IndexFlatIP | None = None
        self.doc_ids: List[str] = []
        self.doc_metadata: List[Dict[str, Any]] = []

    def _load_model(self):
        if self.model is None:
            print(f"Loading dense embedding model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)

    def build_index(self):
        self._load_model()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM sections")
        rows = cur.fetchall()
        conn.close()

        self.doc_ids = []
        self.doc_metadata = []
        texts_to_embed = []

        for row in rows:
            d = dict(row)
            self.doc_ids.append(d["id"])
            self.doc_metadata.append(d)
            # Embed structured semantic representation: Act + Section + Title + first 500 chars of body
            summary = f"[{d['act_code']} Section {d['section_no']}] {d['title']}: {d['text'][:400]}"
            texts_to_embed.append(summary)

        print(f"Encoding {len(texts_to_embed)} sections with {self.model_name}...")
        embeddings = self.model.encode(
            texts_to_embed,
            batch_size=64,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(np.array(embeddings, dtype=np.float32))

        self.index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_dir / "index.faiss"))
        with open(self.index_dir / "meta.pkl", "wb") as f:
            pickle.dump({
                "doc_ids": self.doc_ids,
                "doc_metadata": self.doc_metadata,
            }, f)
        print(f"Dense FAISS index built and saved to {self.index_dir}")

    def load_index(self):
        if not (self.index_dir / "index.faiss").exists():
            self.build_index()
            return

        self._load_model()
        self.index = faiss.read_index(str(self.index_dir / "index.faiss"))
        with open(self.index_dir / "meta.pkl", "rb") as f:
            data = pickle.load(f)
            self.doc_ids = data["doc_ids"]
            self.doc_metadata = data["doc_metadata"]

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        if self.index is None:
            self.load_index()

        q_embed = self.model.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(np.array(q_embed, dtype=np.float32), top_k)

        results = []
        for rank in range(top_k):
            idx = indices[0][rank]
            if idx >= 0 and idx < len(self.doc_metadata):
                results.append((self.doc_metadata[idx], float(scores[0][rank])))
        return results


if __name__ == "__main__":
    dense = DenseSearchEngine()
    dense.build_index()
    res = dense.search("penalty for murder and mob lynching", top_k=3)
    print("Top Dense results:")
    for doc, score in res:
        print(f"[{doc['id']}] {doc['title']} (score: {score:.3f})")
