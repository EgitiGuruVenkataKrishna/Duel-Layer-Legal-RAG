import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.nyayasetu.generation.generator import LegalAnswerGenerator
from src.nyayasetu.offence.schedule_store import OffenceClassificationStore
from src.nyayasetu.retrieval.exact_router import ExactMatchRouter
from src.nyayasetu.retrieval.hybrid_rrf import HybridRRFSearchEngine
from src.nyayasetu.retrieval.parent_child import ParentChildRetriever
from src.nyayasetu.retrieval.reranker import Reranker
from src.nyayasetu.temporal.classifier import TemporalLegalityEngine
from src.nyayasetu.transition.mapper import StatutoryTransitionMapper
from src.nyayasetu.verify.verifier import CitationVerifier

app = FastAPI(
    title="NyayaSetu API",
    description="Evidence-based Indian Legal Information & Verification Engine",
    version="0.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine singletons
exact_router = ExactMatchRouter()
hybrid_engine = HybridRRFSearchEngine()
parent_child = ParentChildRetriever()
reranker = Reranker()
generator = LegalAnswerGenerator()
verifier = CitationVerifier()
offence_store = OffenceClassificationStore()


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    retrieval_mode: str = "hybrid_rerank"  # 'bm25', 'dense', 'hybrid_rrf', 'hybrid_rerank', 'parent_child'


class QueryResponse(BaseModel):
    query: str
    answer: str
    route_type: str
    retrieved_sections: List[Dict[str, Any]]
    temporal_analysis: Optional[Dict[str, Any]] = None
    offence_classification: Optional[Dict[str, Any]] = None
    transition_analysis: Optional[Dict[str, Any]] = None
    verification: Dict[str, Any]
    latency_ms: float
    model: str


@app.get("/api/v1/health")
def health():
    return {
        "status": "healthy",
        "version": "0.5.0",
        "engine": "NyayaSetu",
        "model": generator.model_name,
        "database": "operational",
    }


@app.post("/api/v1/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest):
    start_time = time.time()
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Exact Match Routing Check (BNS 103, Section 302 IPC, etc.)
    exact_hit = exact_router.route(query)
    temporal_hit = TemporalLegalityEngine.analyze_query(query)

    # Check for transition query (e.g. 'what replaced 420 IPC' or 'IPC 302')
    transition_hit = None
    for token in query.split():
        if token.isdigit():
            transition_hit = StatutoryTransitionMapper.lookup_transition("IPC", token)
            if not transition_hit:
                transition_hit = StatutoryTransitionMapper.lookup_transition("CRPC", token)
            if transition_hit:
                break

    # Check for offence classification
    offence_hit = None
    if exact_hit:
        offence_hit = offence_store.get_offence(exact_hit.get("section_no", ""))
    elif transition_hit:
        offence_hit = offence_store.get_offence(transition_hit.get("new_sec", ""))

    # 2. Retrieval Execution
    retrieved_docs: List[Dict[str, Any]] = []
    route_type = "retrieval_pipeline"

    if exact_hit:
        retrieved_docs = [exact_hit]
        route_type = "exact_match_router"
    else:
        if req.retrieval_mode == "bm25":
            raw_hits = hybrid_engine.bm25_engine.search(query, top_k=req.top_k)
            retrieved_docs = [doc for doc, _ in raw_hits]
        elif req.retrieval_mode == "dense":
            raw_hits = hybrid_engine.dense_engine.search(query, top_k=req.top_k)
            retrieved_docs = [doc for doc, _ in raw_hits]
        elif req.retrieval_mode == "hybrid_rrf":
            raw_hits = hybrid_engine.search(query, top_k=req.top_k)
            retrieved_docs = [doc for doc, _ in raw_hits]
        elif req.retrieval_mode == "parent_child":
            raw_hits = parent_child.search(query, top_k=req.top_k)
            retrieved_docs = [doc for doc, _ in raw_hits]
        else:  # 'hybrid_rerank' (default production mode)
            candidates = hybrid_engine.search(query, top_k=req.top_k * 2)
            reranked = reranker.rerank(query, candidates, top_k=req.top_k)
            retrieved_docs = [doc for doc, _ in reranked]

    # 3. Answer Generation
    gen_result = generator.generate(
        query=query,
        retrieved_docs=retrieved_docs,
        temporal_info=temporal_hit,
        offence_info=offence_hit,
        transition_info=transition_hit,
    )

    # 4. Citation & Grounding Verification
    verification = verifier.verify_answer(query, gen_result["answer"], retrieved_docs)

    latency_ms = (time.time() - start_time) * 1000

    return QueryResponse(
        query=query,
        answer=gen_result["answer"],
        route_type=route_type,
        retrieved_sections=retrieved_docs,
        temporal_analysis=temporal_hit,
        offence_classification=offence_hit,
        transition_analysis=transition_hit,
        verification=verification,
        latency_ms=round(latency_ms, 2),
        model=gen_result["model"],
    )


@app.get("/api/v1/lookup")
def lookup_endpoint(act: str = Query(..., description="Act code: BNS, BNSS, BSA, IPC, CRPC, IEA"), section: str = Query(..., description="Section number")):
    hit = exact_router._lookup(act.upper().strip(), section.strip())
    if not hit:
        raise HTTPException(status_code=404, detail=f"Section {section} under {act} not found.")
    return hit


@app.get("/api/v1/transition")
def transition_endpoint(code: str = Query(..., description="Old or new code, e.g. IPC, CRPC, BNS"), section: str = Query(..., description="Section number")):
    hit = StatutoryTransitionMapper.lookup_transition(code, section)
    if not hit:
        raise HTTPException(status_code=404, detail=f"No transition mapping found for {code} {section}.")
    return hit


@app.get("/api/v1/offence")
def offence_endpoint(section: str = Query(..., description="BNS section number")):
    hit = offence_store.get_offence(section)
    if not hit:
        raise HTTPException(status_code=404, detail=f"Offence classification for Section {section} not found.")
    return hit


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.nyayasetu.api.main:app", host="0.0.0.0", port=8000, reload=False)
