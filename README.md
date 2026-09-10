# NyayaRAG: Zero-Hallucination Legal RAG System for Indian Law ⚖️

![NyayaRAG Architecture](https://img.shields.io/badge/Architecture-Dual--Tier%20LangGraph-blue)
![LLM](https://img.shields.io/badge/LLM-Qwen%2027B%20(Groq)-orange)
![Retrieval](https://img.shields.io/badge/Retrieval-FAISS%20%2B%20BM25%20RRF-green)

NyayaRAG is a production-grade, zero-cost Retrieval-Augmented Generation (RAG) system engineered specifically for the modern Indian Legal Framework (BNS, BNSS, BSA, Constitution of India, and Supreme Court Precedents). 

Built to combat the fatal flaw of LLM hallucinations in the legal domain, NyayaRAG utilizes a custom **Dual-Tier State Machine** powered by LangGraph, strictly preserving statutory metadata and employing rigorous G-Eval verification gates.

## 🌟 Core Features

- **Structural Legal Parser:** Employs PyMuPDF and specialized regex to preserve absolute hierarchical boundaries (`Act`, `Chapter`, `Section`, `Subsection`), overcoming the semantic destruction caused by naive chunkers.
- **Dual-Tier Query Routing:**
  - **Tier 1 (Direct Lookup):** Optimized for high-speed, exact statutory mapping.
  - **Tier 2 (Scenario Deconstruction):** Translates complex human narratives into structured legal parameters for multi-hop precedent matching.
- **Nyaya Hybrid Retrieval:** Isolates Statutes from Precedents to prevent cross-contamination. Employs Reciprocal Rank Fusion (RRF) across Dense (FAISS) and Sparse (BM25) vector indices.
- **G-Eval Hallucination Firewall:** An aggressive internal LLM judge evaluates the retrieved context prior to generation. If the context relevance falls below an absolute threshold (0.8), execution is aborted to a verified fallback response.

## 🛠️ Technology Stack

- **Orchestration:** LangGraph, LangChain
- **Vector Search:** FAISS (Dense), Rank-BM25 (Sparse), Sentence-Transformers (`all-MiniLM-L6-v2`)
- **LLM Engine:** Groq API (`qwen/qwen3.8-27b`)
- **Document Processing:** PyMuPDF
- **Interface:** FastAPI, Streamlit

## 🚀 Quick Start Guide

### 1. Environment Setup

Ensure you have Python 3.10+ installed.

```bash
# Clone the repository
git clone https://github.com/your-username/NyayaRAG.git
cd NyayaRAG

# Set up a virtual environment
python -m venv venv

# Activate the environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials
Set your Groq API key in your environment variables:
```bash
# Windows
set GROQ_API_KEY="your_api_key_here"
```

### 3. Ingest Legal Documents
Place your source PDFs in the designated raw directories to maintain strict retrieval isolation:
- **Statutes:** `data/raw/statutes/` (BNS, BNSS, BSA, Constitution)
- **Precedents:** `data/raw/judgments/` (Supreme Court Rulings)

Execute the ingestion pipeline to parse the PDFs and build the FAISS/BM25 indices:
```bash
python -m legal_rag.ingest
```

### 4. Launch the System
The system is divided into a backend API and a frontend dashboard. You will need two terminal windows.

**Terminal 1 (FastAPI Backend):**
```bash
uvicorn legal_rag.app.main:app --reload --port 8000
```

**Terminal 2 (Streamlit UI):**
```bash
streamlit run legal_rag/app/ui.py
```
Navigate to `http://localhost:8501` to begin testing.

## 📝 License
This project is open-source and available under the MIT License.
