import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from legal_rag.retrieval.hybrid_store import DualHybridStore
import os
from legal_rag.graph.workflow import build_workflow
from legal_rag.graph.state import LegalState

app = FastAPI(title="Dual-Tier Legal RAG API", version="1.0.0")

# Initialize system
store = DualHybridStore()
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "db")
store.load_local(db_path)

workflow_app = build_workflow(store)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    tier: str
    geval_score: float
    final_response: str
    latency_sec: float
    context_used: str

@app.post("/api/v1/query", response_model=QueryResponse)
def execute_query(request: QueryRequest):
    start_time = time.time()
    
    initial_state = LegalState(
        user_query=request.query,
        tier=None,
        decomposed_params=None,
        statute_docs=[],
        precedent_docs=[],
        geval_score=0.0,
        final_response="",
        error=None
    )
    
    try:
        final_state = workflow_app.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    latency = round(time.time() - start_time, 2)
    
    context_parts = []
    for doc in final_state.get("statute_docs", []) + final_state.get("precedent_docs", []):
        meta = doc.metadata
        act = meta.get("Act", "")
        sec = meta.get("Section", "")
        context_parts.append(f"[{act} Sec {sec}] {doc.page_content}")
        
    return QueryResponse(
        tier=final_state.get("tier", "unknown"),
        geval_score=final_state.get("geval_score", 0.0),
        final_response=final_state.get("final_response", ""),
        latency_sec=latency,
        context_used="\n\n".join(context_parts)
    )
