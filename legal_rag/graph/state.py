import operator
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.documents import Document

class LegalState(TypedDict):
    """
    Represents the state of the LangGraph Legal RAG System.
    """
    user_query: str
    tier: Optional[str]
    decomposed_params: Optional[Dict[str, Any]]
    
    # Use Annotated to allow list extension/replacement if needed, 
    # but here we just replace them so we don't strictly need operator.add
    statute_docs: List[Document]
    precedent_docs: List[Document]
    
    geval_score: float
    final_response: str
    error: Optional[str]
