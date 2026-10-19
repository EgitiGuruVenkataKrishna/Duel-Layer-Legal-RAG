from fastapi.testclient import TestClient
from src.nyayasetu.api.main import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["engine"] == "NyayaSetu"


def test_lookup_endpoint():
    resp = client.get("/api/v1/lookup?act=BNS&section=103")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "BNS-103"
    assert "murder" in data["title"].lower()


def test_transition_endpoint():
    resp = client.get("/api/v1/transition?code=IPC&section=302")
    assert resp.status_code == 200
    data = resp.json()
    assert data["new_code"] == "BNS"
    assert data["new_sec"] == "103(1)"


def test_offence_endpoint():
    resp = client.get("/api/v1/offence?section=103(1)")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cognizable"] == "Cognizable"
    assert data["bailable"] == "Non-bailable"


def test_query_exact_match():
    resp = client.post("/api/v1/query", json={"query": "What is BNS 103?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["route_type"] == "exact_match_router"
    assert len(data["retrieved_sections"]) > 0
    assert data["retrieved_sections"][0]["id"] == "BNS-103"
