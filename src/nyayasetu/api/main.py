import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.nyayasetu.compare.chatgpt import ChatGPTBaseline
from src.nyayasetu.pipeline.dual_tier import DualTierPipeline
from src.nyayasetu.transition.mapper import StatutoryTransitionMapper
from src.nyayasetu.verify.verifier import CitationVerifier

app = FastAPI(
    title="NyayaSetu API",
    description="Dual-tier evidence-based Indian criminal-law research engine",
    version="0.6.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = DualTierPipeline()
exact_router = pipeline.exact_router
offence_store = pipeline.offence_store
chatgpt = ChatGPTBaseline()
verifier = CitationVerifier()


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    retrieval_mode: str = "auto"


class QueryResponse(BaseModel):
    query: str
    answer: str
    tier: str = "tier1"
    route_type: str
    retrieved_sections: List[Dict[str, Any]]
    temporal_analysis: Optional[Dict[str, Any]] = None
    offence_classification: Optional[Dict[str, Any]] = None
    transition_analysis: Optional[Dict[str, Any]] = None
    verification: Dict[str, Any]
    metrics: Dict[str, Any] = {}
    latency_ms: float
    model: str
    disclaimer: str = "Informational research output only. Not legal advice."


def _audit_chatgpt(answer: Optional[str]) -> Dict[str, Any]:
    if not answer:
        return {
            "citations_mentioned": 0,
            "exist_in_corpus": 0,
            "invented_or_unknown": [],
            "corpus_hit_rate": None,
            "note": "No ChatGPT answer to audit.",
        }
    cites = chatgpt.extract_loose_citations(answer)
    details = []
    valid = 0
    for act, sec in cites:
        exists = verifier.verify_section_exists(act, sec)
        if exists:
            valid += 1
        details.append({"act_code": act, "section_no": sec, "exists_in_corpus": exists})
    invented = [d for d in details if not d["exists_in_corpus"]]
    return {
        "citations_mentioned": len(cites),
        "exist_in_corpus": valid,
        "invented_or_unknown": invented,
        "corpus_hit_rate": round(valid / len(cites), 4) if cites else None,
        "citations": details,
        "note": (
            "ChatGPT is unaudited general knowledge. Citations that do not exist in the "
            "NyayaSetu statute database are listed under invented_or_unknown."
        ),
    }


@app.get("/api/v1/health")
def health():
    return {
        "status": "healthy",
        "version": "0.6.0",
        "engine": "NyayaSetu",
        "model": pipeline.generator.model_name,
        "database": "operational",
        "dual_tier": True,
        "chatgpt_compare_ready": chatgpt.available(),
    }


@app.post("/api/v1/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    result = pipeline.run(query, top_k=req.top_k)
    result["disclaimer"] = "Informational research output only. Not legal advice."
    return QueryResponse(**result)


@app.post("/api/v1/compare")
def compare_endpoint(req: QueryRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    start = time.time()
    ours = pipeline.run(query, top_k=req.top_k)
    gpt = chatgpt.ask(query)
    chatgpt_audit = _audit_chatgpt(gpt.get("answer"))
    return {
        "query": query,
        "disclaimer": "Informational research output only. Not legal advice.",
        "nyayasetu": {
            "answer": ours["answer"],
            "tier": ours["tier"],
            "route_type": ours["route_type"],
            "metrics": ours["metrics"],
            "verification": ours["verification"],
            "retrieved_sections": ours["retrieved_sections"],
            "model": ours["model"],
        },
        "chatgpt": {
            "model": gpt.get("model"),
            "available": gpt.get("available"),
            "answer": gpt.get("answer"),
            "error": gpt.get("error"),
            "tokens_used": gpt.get("tokens_used"),
            "corpus_audit": chatgpt_audit,
        },
        "contrast": {
            "nyayasetu_citation_validity": ours["metrics"].get("citation_validity"),
            "chatgpt_corpus_hit_rate": chatgpt_audit.get("corpus_hit_rate"),
            "nyayasetu_grounded_in_retrieved_statutes": True,
            "chatgpt_grounded_in_retrieved_statutes": False,
            "nyayasetu_abstained": ours["metrics"].get("abstained"),
        },
        "latency_ms": round((time.time() - start) * 1000, 2),
    }


@app.get("/api/v1/lookup")
def lookup_endpoint(
    act: str = Query(..., description="Act code: BNS, BNSS, BSA, IPC, CRPC, IEA"),
    section: str = Query(..., description="Section number"),
):
    hit = exact_router._lookup(act.upper().strip(), section.strip())
    if not hit:
        raise HTTPException(status_code=404, detail=f"Section {section} under {act} not found.")
    return hit


@app.get("/api/v1/transition")
def transition_endpoint(
    code: str = Query(..., description="Old or new code, e.g. IPC, CRPC, BNS"),
    section: str = Query(..., description="Section number"),
):
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
