# ==========================================
# NyayaSetu Automation Makefile
# ==========================================

PYTHON ?= python

.PHONY: help install lint test ingest index eval eval-dev eval-test run docker-build docker-up manifest

help:
	@echo "Available commands:"
	@echo "  make install      Install Python dependencies"
	@echo "  make lint         Run Ruff linter and formatter checks"
	@echo "  make test         Execute pytest test suite (unit + parser + BM25 regression)"
	@echo "  make ingest       Parse statute PDFs to JSONL + parse BNSS First Schedule"
	@echo "  make index        Build FAISS + BM25 indices (run after ingest)"
	@echo "  make manifest     Regenerate data/MANIFEST.json with SHA-256 hashes"
	@echo "  make eval-dev     Run eval harness on dev set (safe to run anytime)"
	@echo "  make eval-test    Run eval harness on TEST set (requires --confirm flag)"
	@echo "  make eval         Alias for eval-dev"
	@echo "  make run          Launch FastAPI backend and Streamlit UI"
	@echo "  make docker-build Build unified Docker image"
	@echo "  make docker-up    Start full stack with docker compose"

install:
	$(PYTHON) -m pip install -r requirements.txt

lint:
	ruff check .

test:
	pytest tests/ -q -x --tb=short 2>&1 | tail -30

ingest:
	$(PYTHON) -m src.nyayasetu.ingest.parser
	$(PYTHON) -m src.nyayasetu.offence.schedule_parser

index:
	$(PYTHON) -m src.nyayasetu.retrieval.indexer

manifest:
	$(PYTHON) scripts/make_manifest.py

eval-dev:
	$(PYTHON) eval/run.py --split dev

eval-test:
	$(PYTHON) eval/run.py --split test --confirm

# Legacy alias
eval:
	$(PYTHON) eval/run.py --split dev

run:
	$(PYTHON) -m src.nyayasetu.api.main &
	streamlit run app/main.py

docker-build:
	docker compose build

docker-up:
	docker compose up -d
