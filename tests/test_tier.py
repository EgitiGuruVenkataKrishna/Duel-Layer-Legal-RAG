from fastapi.testclient import TestClient

from src.nyayasetu.api.main import app
from src.nyayasetu.routing.tier_router import DualTierClassifier

client = TestClient(app)
classifier = DualTierClassifier()


def test_tier1_named_section():
    d = classifier.classify("What is BNS 103?")
    assert d.tier == "tier1"


def test_tier1_theft_keyword():
    d = classifier.classify("what is the thief related section")
    assert d.tier == "tier1"


def test_tier2_scenario():
    q = (
        "Yesterday my neighbour accused my friend of taking a phone from a parked scooter "
        "and the police came and asked whether an FIR can be registered. "
        "What offence is made out in this case?"
    )
    d = classifier.classify(q)
    assert d.tier == "tier2"


def test_query_returns_metrics():
    resp = client.post("/api/v1/query", json={"query": "What is BNS 103?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "tier1"
    assert data["route_type"] == "exact_match_router"
    assert "metrics" in data
    assert data["metrics"]["citation_validity"] is not None
    assert data["metrics"]["computation"] == "low"
    assert data["retrieved_sections"][0]["id"] == "BNS-103"


def test_keyword_theft_query():
    resp = client.post("/api/v1/query", json={"query": "what is the thief related section"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "tier1"
    ids = [s["id"] for s in data["retrieved_sections"]]
    assert any("303" in i or "theft" in (s.get("title") or "").lower() for i, s in zip(ids, data["retrieved_sections"]))


def test_compare_without_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from src.nyayasetu.api import main as api_main

    api_main.chatgpt.api_key = None
    resp = client.post("/api/v1/compare", json={"query": "What is BNS 103?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["nyayasetu"]["route_type"] == "exact_match_router"
    assert data["chatgpt"]["available"] is False
    assert data["contrast"]["nyayasetu_grounded_in_retrieved_statutes"] is True
