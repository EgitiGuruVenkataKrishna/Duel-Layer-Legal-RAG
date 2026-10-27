import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from sentence_transformers import CrossEncoder


def _default_reranker_model() -> str:
    """Read reranker model from configs/retrieval.yaml active mode, then env, then fallback."""
    try:
        import yaml  # type: ignore[import-untyped]
        cfg_path = Path(__file__).resolve().parents[4] / "configs" / "retrieval.yaml"
        if cfg_path.exists():
            cfg = yaml.safe_load(cfg_path.read_text())
            active = cfg.get("active", "")
            mode = cfg.get("modes", {}).get(active, {})
            reranker_cfg = mode.get("reranker", {})
            if reranker_cfg.get("model"):
                return reranker_cfg["model"]
    except Exception:
        pass
    return os.environ.get("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")


class Reranker:
    """Cross-Encoder Reranker; model ID sourced from configs/retrieval.yaml."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or _default_reranker_model()
        self.model: CrossEncoder | None = None

    def _load_model(self):
        if self.model is None:
            # Try offline local cache first with configured model, then cached fallback
            for m in [self.model_name, "cross-encoder/ms-marco-MiniLM-L-6-v2"]:
                try:
                    self.model = CrossEncoder(m, local_files_only=True)
                    break
                except Exception:
                    continue
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
            import math
            scores = self.model.predict(pairs)
            scored_candidates = []
            for idx, score in enumerate(scores):
                # Sigmoid normalization into [0.0, 1.0] for consistent similarity metrics
                try:
                    norm_score = 1.0 / (1.0 + math.exp(-float(score)))
                except OverflowError:
                    norm_score = 0.0 if float(score) < 0 else 1.0
                scored_candidates.append((candidates[idx][0], float(norm_score)))

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
