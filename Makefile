# ==========================================
# NyayaSetu Automation Makefile
# ==========================================

PYTHON ?= python

.PHONY: help install lint test ingest eval run docker-build docker-up

help:
	@echo "Available commands:"
	@echo "  make install      Install Python dependencies"
	@echo "  make lint         Run Ruff linter and formatter checks"
	@echo "  make test         Execute pytest test suite"
	@echo "  make ingest       Parse statute PDFs, generate JSONL & build indices"
	@echo "  make eval         Run evaluation harness across golden test sets"
	@echo "  make run          Launch FastAPI backend and Streamlit UI"
	@echo "  make docker-build Build unified Docker image"
	@echo "  make docker-up    Start full stack with docker compose"

install:
	$(PYTHON) -m pip install -r requirements.txt

lint:
	ruff check .

test:
	pytest tests/ -v

ingest:
	$(PYTHON) -m src.nyayasetu.ingest.parser
	$(PYTHON) -m src.nyayasetu.offence.schedule_parser
	$(PYTHON) -m src.nyayasetu.retrieval.indexer

eval:
	$(PYTHON) -m eval.harness

run:
	$(PYTHON) -m src.nyayasetu.api.main &
	streamlit run app/main.py

docker-build:
	docker compose build

docker-up:
	docker compose up -d
