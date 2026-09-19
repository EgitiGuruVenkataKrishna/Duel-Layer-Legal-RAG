# Production Deployment Architecture: Zero-Hallucination Legal RAG

The objective is to transition NyayaRAG from a local prototype to a highly scalable, production-grade cloud architecture using the best-in-class free-tier resources. This guarantees zero-hallucination legal analysis with high concurrency support, distinguishing our system from generic LLMs through strict hybrid-retrieval and structured metadata mapping.

## User Review Required

> [!CAUTION]
> Moving from local FAISS/BM25 files to a production database will require us to **re-ingest** the PDFs once the new cloud database code is written.

## Open Questions

> [!IMPORTANT]
> **Q1: Database Platform:** I strongly recommend migrating to **Qdrant Cloud** (generous 1GB free tier). Qdrant natively supports Hybrid Search (combining Dense and Sparse vectors). This allows us to replace both FAISS and Rank-BM25 with a single, highly concurrent cloud database. Are you comfortable creating a free Qdrant Cloud account to get an API key?
> 
> **Q2: Application Hosting:** For the backend API, I recommend **Render.com** (Free tier). For the frontend, **Streamlit Community Cloud** (100% free and connects directly to your GitHub). Do you have accounts ready for these platforms?
>
> **Q3: Caching & Rate Limiting:** To protect our Groq API budget and guarantee zero costs, I recommend adding **Upstash Serverless Redis** (generous free tier). We will cache identical queries so they return instantly without querying Groq. Should I include Redis in this implementation?

## Proposed Changes

### 1. Unified Cloud Vector Database (Qdrant)
Local FAISS files lock up under multiple users and Rank-BM25 loads the entire corpus into RAM. We will fix this by migrating to Qdrant.
- **[DELETE]** `legal_rag/retrieval/hybrid_store.py`
- **[NEW]** `legal_rag/retrieval/qdrant_store.py`
  - Connect to Qdrant Cloud.
  - Configure a collection supporting both `dense` (all-MiniLM) and `sparse` (BM25/SPLADE-like) vectors.
  - Implement native Reciprocal Rank Fusion (RRF) for retrieval.
- **[MODIFY]** `legal_rag/ingest.py` & `legal_rag/ingestion/parser.py`
  - Update ingestion logic to push embedded chunks to Qdrant Cloud instead of local disk.

### 2. Containerization (Zero Environment Drift)
- **[NEW]** `Dockerfile` - Optimized Python 3.10 image for the FastAPI backend.
- **[NEW]** `docker-compose.yml` - For local testing of the production image.
- **[NEW]** `.dockerignore` - To prevent uploading PDFs and `venv` to the Docker context.

### 3. API Hardening (Backend)
- **[MODIFY]** `legal_rag/app/main.py`
  - Implement Redis caching (via Upstash) for exact query matching.
  - Setup CORS middleware securely for Streamlit Cloud.
- **[MODIFY]** `requirements.txt`
  - Add `qdrant-client`, `redis`, `fastapi-limiter`.

### 4. CI/CD & Frontend Configuration
- **[NEW]** `render.yaml` - Infrastructure-as-code to automatically deploy the backend to Render on Git push.
- **[MODIFY]** `legal_rag/app/ui.py`
  - Configure the frontend to dynamically switch between `localhost:8000` (for local testing) and the Render Cloud URL (for production).

## Verification Plan

1. **Docker Validation:** Spin up the `docker-compose` stack locally and verify the FastAPI server runs flawlessly in a containerized environment.
2. **Cloud Database Test:** Execute the modified `ingest.py` to populate Qdrant Cloud, verifying dense and sparse vectors are stored.
3. **End-to-End Staging Test:** Run our rigorous `test_cases.md` (e.g., Section 103 BNS, Hallucination checks) against the Dockerized backend connected to Qdrant to definitively prove the G-Eval gating and hybrid retrieval maintain their superiority over standard ChatGPT.
