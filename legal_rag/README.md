# Zero-Hallucination Dual-Tier Legal RAG System for Indian Law

A production-grade, zero-cost RAG architecture designed specifically for the Indian Legal Framework (BNS, BNSS, BSA, Constitution, SC Precedents).

## Key Features

1. **Precision Ingestion**: PyMuPDF + Regex boundary preservation to map exact `Act`, `Chapter`, `Section`, and `Subsection` metadata instead of using generic chunkers.
2. **Dual-Tier Architecture**:
   - **Tier 1**: Direct Statutory Lookups
   - **Tier 2**: Advanced Situational Scenario Deconstruction
3. **Dual-Store Hybrid Indexing**: Separate indices for statutes vs. precedents using FAISS (dense) and BM25 (sparse) with Reciprocal Rank Fusion (RRF).
4. **Zero-Hallucination G-Eval**: Strict execution gating. If context relevance score falls below 0.8, the system triggers a verified fallback instead of hallucinating an answer.
5. **Agentic State Machine**: Powered by LangGraph for robust defensive validation and routing.
6. **Zero-Cost Local Ready**: Uses `all-MiniLM-L6-v2` for low-compute embeddings and `llama-3.1-8b-instant` via Groq for high-speed, cost-effective LLM execution.

## Setup Instructions

1. Install requirements:
   ```bash
   pip install -r ../requirements.txt
   ```
2. Set your Groq API Key:
   ```bash
   export GROQ_API_KEY="your_api_key_here"
   # On Windows: set GROQ_API_KEY=your_api_key_here
   # Or using PowerShell: $env:GROQ_API_KEY="your_api_key_here"
   ```
3. Run the FastAPI Backend:
   Ensure you run this from the project root (`e:/LegalGround`).
   ```bash
   uvicorn legal_rag.app.main:app --reload --port 8000
   ```
4. Run the Streamlit Dashboard (in a new terminal):
   ```bash
   streamlit run legal_rag/app/ui.py
   ```
