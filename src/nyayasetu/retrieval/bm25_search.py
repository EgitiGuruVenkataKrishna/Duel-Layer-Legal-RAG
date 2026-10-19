import os
import pickle
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple
from rank_bm25 import BM25Okapi


class BM25SearchEngine:
    """
    Deterministic sparse BM25 retrieval over Indian statutory sections.
    """

    def __init__(self, index_path: str | None = None, db_path: str | None = None):
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        if index_path is None:
            index_path = str(project_root / "data" / "processed" / "bm25_index.pkl")
        if db_path is None:
            db_path = str(project_root / "data" / "processed" / "nyayasetu.db")
        self.index_path = index_path
        self.db_path = db_path
        self.bm25: BM25Okapi | None = None
        self.doc_ids: List[str] = []
        self.doc_metadata: List[Dict[str, Any]] = []

    @staticmethod
    def tokenize(text: str) -> List[str]:
        # Preserve section numbers like 103, 302, 376A, 420
        clean = text.lower()
        tokens = re.findall(r"\b[a-z0-9]+(?:[a-z])?\b", clean)
        return tokens

    def build_index(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM sections")
        rows = cur.fetchall()
        conn.close()

        corpus = []
        self.doc_ids = []
        self.doc_metadata = []

        for row in rows:
            d = dict(row)
            self.doc_ids.append(d["id"])
            self.doc_metadata.append(d)
            # Combine act, section number, title, and text for rich tokenization
            full_content = f"{d['act_code']} {d['act']} Section {d['section_no']} {d['title']} {d['text']}"
            corpus.append(self.tokenize(full_content))

        self.bm25 = BM25Okapi(corpus)
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({
                "bm25": self.bm25,
                "doc_ids": self.doc_ids,
                "doc_metadata": self.doc_metadata
            }, f)
        print(f"BM25 index built with {len(self.doc_ids)} sections and saved to {self.index_path}")

    def load_index(self):
        if not os.path.exists(self.index_path):
            self.build_index()
            return
        with open(self.index_path, "rb") as f:
            data = pickle.load(f)
            self.bm25 = data["bm25"]
            self.doc_ids = data["doc_ids"]
            self.doc_metadata = data["doc_metadata"]

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        if not self.bm25:
            self.load_index()

        tokens = self.tokenize(query)
        scores = self.bm25.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            results.append((self.doc_metadata[idx], float(scores[idx])))
        return results


if __name__ == "__main__":
    searcher = BM25SearchEngine()
    searcher.build_index()
    res = searcher.search("murder punishment death penalty", top_k=3)
    print("Top BM25 results:")
    for doc, score in res:
        print(f"[{doc['id']}] {doc['title']} (score: {score:.3f})")
