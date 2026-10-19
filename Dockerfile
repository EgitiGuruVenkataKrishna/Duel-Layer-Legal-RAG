# Unified Multi-Stage Dockerfile for NyayaSetu
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies (build-essential, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency requirements
COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source code, apps, configs, and manifests
COPY src/ ./src/
COPY app/ ./app/
COPY eval/ ./eval/
COPY data/MANIFEST.json ./data/MANIFEST.json
COPY data/ ./data/
COPY docs/ ./docs/
COPY tests/ ./tests/
COPY .env.example ./.env

EXPOSE 8000 8501

# Entrypoint script to start API and Streamlit
CMD ["sh", "-c", "python -m src.nyayasetu.api.main & streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0"]
