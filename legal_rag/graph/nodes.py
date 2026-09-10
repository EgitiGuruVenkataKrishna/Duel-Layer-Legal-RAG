import json
import re
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from legal_rag.retrieval.hybrid_store import DualHybridStore
from legal_rag.graph.state import LegalState

class LegalGraphNodes:
    def __init__(self, store: DualHybridStore, model_name: str = "qwen/qwen3.8-27b"):
        self.store = store
        self.llm = ChatGroq(model=model_name, temperature=0.0)

    def gateway_router(self, state: LegalState) -> LegalState:
        """
        Classifies query into Tier 1 (direct lookup) or Tier 2 (situational analysis).
        """
        query = state["user_query"]
        sys_prompt = "You are a legal routing assistant. Your job is to classify queries."
        prompt = f"""
        Classify the following user query as either "tier1" (simple direct statutory lookups, definitions, section checks) 
        or "tier2" (advanced situational judgment, multi-hop scenario analysis, complex human narratives).
        Output ONLY the exact string "tier1" or "tier2", and nothing else.
        
        Query: {query}
        """
        response = self.llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=prompt)])
        tier = "tier1" if "tier1" in response.content.lower() else "tier2"
        return {"tier": tier}

    def scenario_decomposer(self, state: LegalState) -> LegalState:
        """
        Deconstructs complex human narratives into clean legal parameters.
        """
        query = state["user_query"]
        sys_prompt = "You are a legal scenario decomposer. Respond ONLY with valid JSON."
        prompt = f"""
        Deconstruct this user narrative into clear legal facts, potentially involved acts, and triggers.
        Respond ONLY in JSON format with keys: "legal_facts", "acts_involved", "triggers". Do not include markdown code blocks.
        
        Query: {query}
        """
        response = self.llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=prompt)])
        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            decomposed = json.loads(content)
        except Exception:
            decomposed = {"legal_facts": query, "acts_involved": [], "triggers": []}
            
        return {"decomposed_params": decomposed}

    def statute_retriever(self, state: LegalState) -> LegalState:
        query = json.dumps(state.get("decomposed_params")) if state.get("tier") == "tier2" else state["user_query"]
        docs = self.store.retrieve(query, domain="statutes", top_k=5)
        return {"statute_docs": docs}

    def precedent_retriever(self, state: LegalState) -> LegalState:
        query = json.dumps(state.get("decomposed_params")) if state.get("tier") == "tier2" else state["user_query"]
        docs = self.store.retrieve(query, domain="precedents", top_k=5)
        return {"precedent_docs": docs}

    def geval_judge(self, state: LegalState) -> LegalState:
        """
        Evaluates retrieved context relevance against the query. Returns a score 0.0 - 1.0.
        """
        query = state["user_query"]
        context_texts = [d.page_content for d in state.get("statute_docs", [])] + \
                        [d.page_content for d in state.get("precedent_docs", [])]
        context = "\n\n".join(context_texts)
        
        if not context.strip():
            return {"geval_score": 0.0}
            
        sys_prompt = "You are an evaluator. You output ONLY a float score between 0.0 and 1.0."
        prompt = f"""
        Evaluate the relevance of the following legal context to the user's query.
        Provide a relevance score from 0.0 to 1.0, where 1.0 is perfectly relevant and sufficient to answer the query,
        and 0.0 is completely irrelevant or hallucinated.
        Output ONLY the float number.
        
        Query: {query}
        Context: {context}
        """
        response = self.llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=prompt)])
        try:
            match = re.search(r'0\.\d+|1\.0', response.content)
            score = float(match.group()) if match else 0.0
        except Exception:
            score = 0.0
            
        return {"geval_score": score}

    def fallback_node(self, state: LegalState) -> LegalState:
        return {"final_response": "Insufficient legal precedent or statutory clarity to ground an accurate answer."}

    def legal_generator(self, state: LegalState) -> LegalState:
        """
        Synthesizes the final output, enforcing strict metadata citations.
        """
        query = state["user_query"]
        statutes = state.get("statute_docs", [])
        precedents = state.get("precedent_docs", [])
        
        context_parts = []
        for doc in statutes + precedents:
            meta = doc.metadata
            act = meta.get("Act", "Unknown")
            chap = meta.get("Chapter", "")
            sec = meta.get("Section", "")
            subsec = meta.get("Sub_section", "")
            page = meta.get("Page", "")
            
            cite_parts = [act]
            if chap: cite_parts.append(f"Chapter {chap}")
            if sec:
                sec_str = f"Section {sec}"
                if subsec: sec_str += f"{subsec}"
                cite_parts.append(sec_str)
            if page: cite_parts.append(f"Page {page}")
            
            cite = "[" + ", ".join(cite_parts) + "]"
            context_parts.append(f"Source {cite}:\n{doc.page_content}")
            
        context = "\n\n".join(context_parts)
        
        sys_prompt = "You are a highly precise Indian Law Legal Assistant. You must formulate answers strictly based on the provided context. Append exact citation strings like [Act, Chapter, Section X(Y), Page Z] to your claims based on the source context provided. DO NOT hallucinate."
        user_prompt = f"Query: {query}\n\nContext:\n{context}\n\nAnswer the query."
        
        response = self.llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        return {"final_response": response.content}
