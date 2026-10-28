import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.nyayasetu.pipeline.dual_tier import DualTierPipeline

pipeline = DualTierPipeline()

test_cases = [
    {
        "category": "Direct Question (Tier 1)",
        "query": "What is BNS 103?",
        "expected_tier": "tier1"
    },
    {
        "category": "Direct Question (Tier 1)",
        "query": "what is the thief related section",
        "expected_tier": "tier1"
    },
    {
        "category": "Direct Question (Tier 1)",
        "query": "Punishment under Section 302 IPC",
        "expected_tier": "tier1"
    },
    {
        "category": "Scenario Question (Tier 2)",
        "query": "Yesterday police registered an FIR after a phone was snatched from a parked scooter. What provisions may be attracted?",
        "expected_tier": "tier2"
    },
    {
        "category": "Scenario Question (Tier 2)",
        "query": "A group of five persons attacked and beat a person to death in broad daylight over a dispute. What offences are made out?",
        "expected_tier": "tier2"
    },
    {
        "category": "Scenario Question (Tier 2)",
        "query": "Suppose someone cheated an elderly person of their life savings through a fraudulent investment scheme. What legal provisions apply?",
        "expected_tier": "tier2"
    }
]

results = []
for tc in test_cases:
    t0 = time.time()
    res = pipeline.run(tc["query"])
    dur = round((time.time() - t0) * 1000, 2)
    results.append({
        "category": tc["category"],
        "query": tc["query"],
        "expected_tier": tc["expected_tier"],
        "classified_tier": res["tier"],
        "tier_passed": tc["expected_tier"] == res["tier"],
        "route_type": res["route_type"],
        "latency_ms": res.get("latency_ms", dur),
        "model": res.get("model"),
        "top_similarity": res["metrics"].get("top_retrieval_score"),
        "avg_similarity": res["metrics"].get("avg_retrieval_score"),
        "citation_validity": res["metrics"].get("citation_validity"),
        "groundedness": res["metrics"].get("groundedness"),
        "status": res["verification"].get("status"),
        "retrieved_sections": [f"{s.get('act_code')} {s.get('section_no')}: {s.get('title')}" for s in res.get("retrieved_sections", [])[:3]],
        "answer_excerpt": res.get("answer", "")[:350].strip()
    })

print(f"Executed {len(results)} queries successfully.")
with open("data/test_execution_benchmark.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print("Saved benchmark results to data/test_execution_benchmark.json")
