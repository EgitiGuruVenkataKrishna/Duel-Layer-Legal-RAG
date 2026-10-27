import time
from typing import Any, Dict, List, Optional, Tuple

from src.nyayasetu.generation.generator import LegalAnswerGenerator
from src.nyayasetu.offence.schedule_store import OffenceClassificationStore
from src.nyayasetu.retrieval.exact_router import ExactMatchRouter
from src.nyayasetu.retrieval.keyword_lookup import KeywordLookup
from src.nyayasetu.routing.tier_router import DualTierClassifier, TierDecision
from src.nyayasetu.temporal.classifier import TemporalLegalityEngine
from src.nyayasetu.transition.mapper import StatutoryTransitionMapper
from src.nyayasetu.verify.verifier import CitationVerifier

ABSTAIN_TEXT = (
    "Insufficient verified statutory support in the corpus for a reliable answer. "
    "The system abstained rather than returning unchecked claims. "
    "Review the retrieved sections below, or rephrase as a direct section lookup."
)

# Minimum similarity score thresholds for chunk filtering
# Chunks below these thresholds are dropped before passing to the LLM
TIER2_MIN_SIMILARITY = 0.005  # RRF scores are small; keep only meaningful matches
TIER1_MIN_SIMILARITY = 0.0    # Tier-1 uses exact/keyword — no filtering needed


def _compact_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    keep = [
        "id",
        "act",
        "act_code",
        "chapter",
        "section_no",
        "title",
        "text",
        "page",
        "effective_date",
        "status",
        "source_url",
        "route_type",
        "retrieval_score",
        "score_type",
    ]
    return {k: doc.get(k) for k in keep if k in doc}


class DualTierPipeline:
    def __init__(self):
        self.exact_router = ExactMatchRouter()
        self.keyword = KeywordLookup()
        self.classifier = DualTierClassifier(exact_router=self.exact_router)
        self.generator = LegalAnswerGenerator()
        self.verifier = CitationVerifier()
        self.offence_store = OffenceClassificationStore()
        self._hybrid = None
        self._reranker = None
        self._parent_child = None

    @property
    def hybrid(self):
        if self._hybrid is None:
            from src.nyayasetu.retrieval.hybrid_rrf import HybridRRFSearchEngine

            self._hybrid = HybridRRFSearchEngine()
        return self._hybrid

    @property
    def reranker(self):
        if self._reranker is None:
            from src.nyayasetu.retrieval.reranker import Reranker

            self._reranker = Reranker()
        return self._reranker

    @property
    def parent_child(self):
        if self._parent_child is None:
            from src.nyayasetu.retrieval.parent_child import ParentChildRetriever

            self._parent_child = ParentChildRetriever()
        return self._parent_child

    def _transition_for(self, query: str, exact_hit: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if exact_hit:
            hit = StatutoryTransitionMapper.lookup_transition(
                exact_hit.get("act_code", ""), exact_hit.get("section_no", "")
            )
            if hit:
                return hit
        for token in query.replace(",", " ").split():
            digits = "".join(ch for ch in token if ch.isdigit() or ch.isalpha())
            if any(ch.isdigit() for ch in token):
                for code in ("IPC", "CRPC", "IEA", "BNS", "BNSS", "BSA"):
                    hit = StatutoryTransitionMapper.lookup_transition(code, token.strip("()."))
                    if hit:
                        return hit
                if digits:
                    hit = StatutoryTransitionMapper.lookup_transition("IPC", digits)
                    if hit:
                        return hit
        lowered = query.lower()
        for kw in ("theft", "murder", "cheating", "rape", "snatching"):
            if kw in lowered:
                found = StatutoryTransitionMapper.search_transitions(kw)
                if found:
                    return found[0]
        return None

    def _offence_for(self, exact_hit, transition_hit) -> Optional[Dict[str, Any]]:
        if exact_hit:
            rec = self.offence_store.get_offence(str(exact_hit.get("section_no", "")))
            if rec:
                return rec
        if transition_hit:
            return self.offence_store.get_offence(str(transition_hit.get("new_sec", "")))
        return None

    def _tier1_retrieve(self, query: str, top_k: int) -> Tuple[List[Dict[str, Any]], str]:
        exact_hit = self.exact_router.route(query)
        if exact_hit:
            exact_hit = dict(exact_hit)
            exact_hit["retrieval_score"] = 1.0
            exact_hit["score_type"] = "exact"
            return [exact_hit], "exact_match_router"

        kw_hits = self.keyword.search(query, top_k=top_k)
        if kw_hits:
            return kw_hits, "keyword_title_lookup"

        raw = self.hybrid.bm25_engine.search(query, top_k=top_k)
        docs = []
        for doc, score in raw:
            d = dict(doc)
            d["retrieval_score"] = float(score)
            d["score_type"] = "bm25"
            docs.append(d)
        return docs, "tier1_bm25"

    def _tier2_retrieve(self, query: str, top_k: int) -> Tuple[List[Dict[str, Any]], str]:
        """
        Enhanced Tier-2 retrieval:
        1. Wider initial retrieval (top_k * 3 for hybrid, top_k * 2 for parent-child)
        2. RRF fusion of hybrid + parent-child results
        3. Cross-encoder reranking
        4. Similarity threshold filtering — drop low-quality chunks
        5. Only the best, most relevant chunks are passed to the LLM
        """
        parent_hits = self.parent_child.search(query, top_k=max(top_k * 2, 10))
        hybrid_hits = self.hybrid.search(query, top_k=top_k * 3)

        fused: Dict[str, Tuple[Dict[str, Any], float]] = {}
        for rank, (doc, score) in enumerate(hybrid_hits):
            fused[doc["id"]] = (dict(doc), float(score) + 1.0 / (60 + rank + 1))
        for rank, (doc, score) in enumerate(parent_hits):
            d = dict(doc)
            prev = fused.get(d["id"])
            extra = float(score) if isinstance(score, (int, float)) else 1.0 / (60 + rank + 1)
            if prev:
                fused[d["id"]] = (prev[0], prev[1] + extra)
            else:
                fused[d["id"]] = (d, extra)

        candidates = [(doc, score) for doc, score in fused.values()]

        # Rerank with a wider window, then take top_k
        reranked = self.reranker.rerank(query, candidates, top_k=max(top_k, 8))

        docs = []
        for doc, score in reranked:
            # Apply similarity threshold — drop chunks that are too low quality
            if float(score) < TIER2_MIN_SIMILARITY:
                continue
            d = dict(doc)
            d["retrieval_score"] = float(score)
            d["score_type"] = "hybrid_rrf_rerank_parent_child"
            docs.append(d)

        # Ensure we always return at least top_k docs (even if some are below threshold)
        if len(docs) < top_k and len(reranked) >= top_k:
            for doc, score in reranked:
                d = dict(doc)
                d_id = d.get("id")
                if d_id and d_id not in {dd.get("id") for dd in docs}:
                    d["retrieval_score"] = float(score)
                    d["score_type"] = "hybrid_rrf_rerank_parent_child"
                    docs.append(d)
                if len(docs) >= top_k:
                    break

        return docs[:top_k], "tier2_hybrid_rerank_parent_child"

    def _metrics(
        self,
        decision: TierDecision,
        route_type: str,
        verification: Dict[str, Any],
        docs: List[Dict[str, Any]],
        gen: Dict[str, Any],
        latency_ms: float,
        llm_used: bool,
        abstained: bool,
    ) -> Dict[str, Any]:
        retrieved_ids = [d.get("id") for d in docs if d.get("id")]
        cited = verification.get("citations_found") or []
        cited_ids = []
        for act, sec in cited:
            cited_ids.append(f"{act}-{str(sec).split('(')[0]}")
        grounded = 0
        for cid in cited_ids:
            if cid in retrieved_ids:
                grounded += 1
        groundedness = (grounded / len(cited_ids)) if cited_ids else (1.0 if docs else 0.0)
        scores = [d.get("retrieval_score") for d in docs if d.get("retrieval_score") is not None]

        # Evidence quality metrics
        avg_score = sum(scores) / len(scores) if scores else 0.0
        min_score = min(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0

        return {
            "tier": decision.tier,
            "tier_reason": decision.reason,
            "tier_signals": decision.signals,
            "route_type": route_type,
            "computation": "low" if decision.tier == "tier1" else "high",
            "llm_used": llm_used,
            "abstained": abstained,
            "citation_validity": verification.get("citation_validity"),
            "valid_citations": verification.get("valid_citations"),
            "total_citations": verification.get("total_citations"),
            "verification_status": verification.get("status"),
            "groundedness": round(groundedness, 4),
            "retrieved_ids": retrieved_ids,
            "top_retrieval_score": max_score,
            "avg_retrieval_score": round(avg_score, 4),
            "min_retrieval_score": round(min_score, 4),
            "n_chunks_used": len(docs),
            "tokens_used": gen.get("tokens_used", 0),
            "latency_ms": round(latency_ms, 2),
            "model": gen.get("model"),
        }

    def run(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        start = time.time()
        query = (query or "").strip()
        decision = self.classifier.classify(query)
        exact_hit = self.exact_router.route(query)
        temporal_hit = TemporalLegalityEngine.analyze_query(query)
        transition_hit = self._transition_for(query, exact_hit)
        offence_hit = self._offence_for(exact_hit, transition_hit)

        if decision.tier == "tier1":
            docs, route_type = self._tier1_retrieve(query, top_k)
            use_llm = False
        else:
            docs, route_type = self._tier2_retrieve(query, top_k)
            use_llm = True

        strict_ids = [d.get("id") for d in docs if d.get("id")]
        gen = self.generator.generate(
            query=query,
            retrieved_docs=docs,
            temporal_info=temporal_hit,
            offence_info=offence_hit,
            transition_info=transition_hit,
            use_llm=use_llm,
            strict_ids=strict_ids,
        )
        verification = self.verifier.verify_answer(query, gen["answer"], docs)
        llm_used = use_llm and gen.get("model") != "deterministic-evidence-synthesizer"
        abstained = False

        if verification.get("should_abstain") and use_llm:
            gen = self.generator.generate(
                query=query + " Cite only ids present in the evidence. Do not invent sections.",
                retrieved_docs=docs,
                temporal_info=temporal_hit,
                offence_info=offence_hit,
                transition_info=transition_hit,
                use_llm=True,
                strict_ids=strict_ids,
            )
            verification = self.verifier.verify_answer(query, gen["answer"], docs)
            llm_used = True

        if verification.get("should_abstain") or (
            llm_used and verification.get("citation_validity", 0) < 0.70
        ):
            fallback = self.generator.generate(
                query=query,
                retrieved_docs=docs,
                temporal_info=temporal_hit,
                offence_info=offence_hit,
                transition_info=transition_hit,
                use_llm=False,
                strict_ids=strict_ids,
            )
            fallback_ver = self.verifier.verify_answer(query, fallback["answer"], docs)
            if fallback_ver.get("citation_validity", 0) >= verification.get("citation_validity", 0):
                gen = fallback
                verification = fallback_ver
                llm_used = False
            if verification.get("should_abstain"):
                gen = {
                    "answer": ABSTAIN_TEXT,
                    "model": gen.get("model"),
                    "tokens_used": gen.get("tokens_used", 0),
                    "grounded": False,
                }
                verification = self.verifier.verify_answer(query, gen["answer"], docs)
                abstained = True

        latency_ms = (time.time() - start) * 1000
        metrics = self._metrics(
            decision, route_type, verification, docs, gen, latency_ms, llm_used, abstained
        )
        return {
            "query": query,
            "answer": gen["answer"],
            "tier": decision.tier,
            "route_type": route_type,
            "retrieved_sections": [_compact_doc(d) for d in docs],
            "temporal_analysis": temporal_hit,
            "offence_classification": offence_hit,
            "transition_analysis": transition_hit,
            "verification": verification,
            "metrics": metrics,
            "latency_ms": round(latency_ms, 2),
            "model": gen.get("model"),
            "disclaimer": "Informational research output only. Not legal advice.",
        }
