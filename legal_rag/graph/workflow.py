from langgraph.graph import StateGraph, END
from legal_rag.graph.state import LegalState
from legal_rag.graph.nodes import LegalGraphNodes
from legal_rag.retrieval.hybrid_store import DualHybridStore

def build_workflow(store: DualHybridStore):
    nodes = LegalGraphNodes(store)
    workflow = StateGraph(LegalState)
    
    # Add nodes
    workflow.add_node("gateway_router", nodes.gateway_router)
    workflow.add_node("scenario_decomposer", nodes.scenario_decomposer)
    workflow.add_node("statute_retriever", nodes.statute_retriever)
    workflow.add_node("precedent_retriever", nodes.precedent_retriever)
    workflow.add_node("geval_judge", nodes.geval_judge)
    workflow.add_node("legal_generator", nodes.legal_generator)
    workflow.add_node("fallback_node", nodes.fallback_node)
    
    # Routing logic
    workflow.set_entry_point("gateway_router")
    
    def route_after_gateway(state: LegalState):
        if state.get("tier") == "tier1":
            return "statute_retriever"
        return "scenario_decomposer"
        
    workflow.add_conditional_edges(
        "gateway_router",
        route_after_gateway,
        {
            "statute_retriever": "statute_retriever",
            "scenario_decomposer": "scenario_decomposer"
        }
    )
    
    workflow.add_edge("scenario_decomposer", "statute_retriever")
    
    def route_after_statute(state: LegalState):
        if state.get("tier") == "tier1":
            return "geval_judge"
        return "precedent_retriever"

    workflow.add_conditional_edges(
        "statute_retriever",
        route_after_statute,
        {
            "geval_judge": "geval_judge",
            "precedent_retriever": "precedent_retriever"
        }
    )
    
    workflow.add_edge("precedent_retriever", "geval_judge")
    
    def route_after_geval(state: LegalState):
        if state.get("geval_score", 0.0) < 0.8:
            return "fallback_node"
        return "legal_generator"
        
    workflow.add_conditional_edges(
        "geval_judge",
        route_after_geval,
        {
            "fallback_node": "fallback_node",
            "legal_generator": "legal_generator"
        }
    )
    
    workflow.add_edge("legal_generator", END)
    workflow.add_edge("fallback_node", END)
    
    return workflow.compile()
