import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple
from rank_bm25 import BM25Okapi
from src.nyayasetu.retrieval.bm25_search import BM25SearchEngine


class ParentChildRetriever:
    """
    Parent-Child Retrieval Engine:
    Indexes fine-grained child nodes (subsections, illustrations, explanations, exceptions, provisos)
    so queries match specific legal conditions or narrative examples.
    When a child node matches, it resolves and returns the complete PARENT section with all child nodes,
    preventing legal context fragmentation.
    """

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            db_path = str(project_root / "data" / "processed" / "nyayasetu.db")
        self.db_path = db_path
        self.child_nodes: List[Dict[str, Any]] = []
        self.parent_cache: Dict[str, Dict[str, Any]] = {}
        self.bm25: BM25Okapi | None = None
        self._load_data()

    def _load_data(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM sections")
        rows = cur.fetchall()
        conn.close()

        corpus = []
        self.child_nodes = []
        self.parent_cache = {}

        for row in rows:
            d = dict(row)
            parent_id = d["id"]
            self.parent_cache[parent_id] = d

            # 1. Parent body chunk
            parent_chunk = {
                "parent_id": parent_id,
                "node_type": "parent_section",
                "text": f"{d['act_code']} Section {d['section_no']} {d['title']}: {d['text']}",
            }
            self.child_nodes.append(parent_chunk)
            corpus.append(BM25SearchEngine.tokenize(parent_chunk["text"]))

            # 2. Subsections
            subsections = json.loads(d.get("subsections_json") or "[]")
            for idx, sub in enumerate(subsections):
                chunk = {
                    "parent_id": parent_id,
                    "node_type": "subsection",
                    "text": f"{d['act_code']} Section {d['section_no']} subsection: {sub}",
                }
                self.child_nodes.append(chunk)
                corpus.append(BM25SearchEngine.tokenize(chunk["text"]))

            # 3. Illustrations
            illustrations = json.loads(d.get("illustrations_json") or "[]")
            for idx, ill in enumerate(illustrations):
                chunk = {
                    "parent_id": parent_id,
                    "node_type": "illustration",
                    "text": f"{d['act_code']} Section {d['section_no']} illustration: {ill}",
                }
                self.child_nodes.append(chunk)
                corpus.append(BM25SearchEngine.tokenize(chunk["text"]))

            # 4. Explanations
            explanations = json.loads(d.get("explanations_json") or "[]")
            for idx, exp in enumerate(explanations):
                chunk = {
                    "parent_id": parent_id,
                    "node_type": "explanation",
                    "text": f"{d['act_code']} Section {d['section_no']} explanation: {exp}",
                }
                self.child_nodes.append(chunk)
                corpus.append(BM25SearchEngine.tokenize(chunk["text"]))

            # 5. Exceptions
            exceptions = json.loads(d.get("exceptions_json") or "[]")
            for idx, exc in enumerate(exceptions):
                chunk = {
                    "parent_id": parent_id,
                    "node_type": "exception",
                    "text": f"{d['act_code']} Section {d['section_no']} exception: {exc}",
                }
                self.child_nodes.append(chunk)
                corpus.append(BM25SearchEngine.tokenize(chunk["text"]))

            # 6. Provisos
            provisos = json.loads(d.get("provisos_json") or "[]")
            for idx, pro in enumerate(provisos):
                chunk = {
                    "parent_id": parent_id,
                    "node_type": "proviso",
                    "text": f"{d['act_code']} Section {d['section_no']} proviso: {pro}",
                }
                self.child_nodes.append(chunk)
                corpus.append(BM25SearchEngine.tokenize(chunk["text"]))

        if corpus:
            self.bm25 = BM25Okapi(corpus)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        if not self.bm25:
            return []

        tokens = BM25SearchEngine.tokenize(query)
        scores = self.bm25.get_scores(tokens)

        # Aggregate child scores into parent sections
        parent_scores: Dict[str, float] = {}
        matched_reasons: Dict[str, List[str]] = {}

        top_child_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[: top_k * 4]

        for idx in top_child_indices:
            score = float(scores[idx])
            if score <= 0.0:
                continue
            child = self.child_nodes[idx]
            pid = child["parent_id"]
            node_type = child["node_type"]

            # Boost parent score with max or cumulative child match
            if pid not in parent_scores:
                parent_scores[pid] = score
                matched_reasons[pid] = [node_type]
            else:
                parent_scores[pid] = max(parent_scores[pid], score) + 0.1 * score
                if node_type not in matched_reasons[pid]:
                    matched_reasons[pid].append(node_type)

        sorted_parents = sorted(parent_scores.keys(), key=lambda pid: parent_scores[pid], reverse=True)

        results = []
        for pid in sorted_parents[:top_k]:
            parent_doc = dict(self.parent_cache[pid])
            parent_doc["matched_child_nodes"] = matched_reasons.get(pid, [])
            results.append((parent_doc, parent_scores[pid]))

        return results

    def get_parent(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a doc or child node to its full parent section."""
        doc_id = doc.get("id") or doc.get("parent_id")
        if doc_id and doc_id in self.parent_cache:
            parent = dict(self.parent_cache[doc_id])
            if "matched_child_nodes" in doc:
                parent["matched_child_nodes"] = doc["matched_child_nodes"]
            return parent
        return doc


if __name__ == "__main__":
    retriever = ParentChildRetriever()
    print("Testing child node matching: 'mob lynching group five race'")
    res = retriever.search("mob lynching group five race", top_k=2)
    for doc, score in res:
        print(f"[{doc['id']}] {doc['title']} (score: {score:.3f}, matched: {doc.get('matched_child_nodes')})")
