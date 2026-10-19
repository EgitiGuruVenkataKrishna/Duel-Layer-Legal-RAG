from typing import Any, Dict, List, Tuple
from sentence_transformers import CrossEncoder


class Reranker:
    """
    Cross-Encoder Reranker for re-scoring retrieved candidates based on deep query-document interaction.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model: CrossEncoder | None = None

    def _load_model(self):
        if self.model is None:
            try:
                self.model = CrossEncoder(self.model_name)
            except Exception as e:
                print(f"Warning: Could not load CrossEncoder {self.model_name}: {e}. Falling back to pass-through.")
                self.model = None

    def rerank(
        self, query: str, candidates: List[Tuple[Dict[str, Any], float]], top_k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        if not candidates:
            return []

        self._load_model()
        if self.model is None:
            return candidates[:top_k]

        pairs = []
        for doc, _ in candidates:
            doc_text = f"Section {doc.get('section_no', '')} {doc.get('title', '')}: {doc.get('text', '')[:500]}"
            pairs.append([query, doc_text])

        try:
            scores = self.model.predict(pairs)
            scored_candidates = []
            for idx, score in enumerate(scores):
                scored_candidates.append((candidates[idx][0], float(score)))

            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            return scored_candidates[:top_k]
        except Exception as e:
            print(f"Reranking error: {e}. Returning original candidates.")
            return candidates[:top_k]


if __name__ == "__main__":
    reranker = Reranker()
    sample_candidates = [
        ({"id": "BNS-103", "section_no": "103", "title": "Murder", "text": "Whoever commits murder..."}, 0.05),
        ({"id": "BNS-303", "section_no": "303", "title": "Theft", "text": "Whoever intends to take dishonestly..."}, 0.04),
    ]
    reranked = reranker.rerank("What is the penalty for murder?", sample_candidates)
    print("Reranked output:", [(doc["id"], score) for doc, score in reranked])
