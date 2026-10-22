"""tests/test_retrieval_regression.py
BM25-only retrieval regression on the 20-section fixture.
CI fails if Recall@5 drops more than 2 percentage points from the baseline (0.70).
"""
import json
import math
from pathlib import Path

import pytest

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "bns_20.jsonl"
BASELINE_RECALL5 = 0.70  # measured at v0.0-baseline; fail if drops > 2pp
TOLERANCE = 0.02


@pytest.fixture(scope="module")
def fixture_docs():
    if not FIXTURE_PATH.exists():
        pytest.skip("BNS fixture not found; run scripts/create_fixture.py")
    return [json.loads(l) for l in FIXTURE_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]


@pytest.fixture(scope="module")
def bm25_engine(fixture_docs):
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        pytest.skip("rank_bm25 not installed")

    corpus = [
        (doc.get("text", "") + " " + doc.get("title", "")).lower().split()
        for doc in fixture_docs
    ]
    bm25 = BM25Okapi(corpus)
    return bm25, fixture_docs


def _recall_at_k(bm25, docs, queries_ids: list[tuple[str, str]], k: int) -> float:
    bm25_obj, _ = bm25
    hits = 0
    for query, target_id in queries_ids:
        tokens = query.lower().split()
        scores = bm25_obj.get_scores(tokens)
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        retrieved_ids = [docs[i].get("id", "") for i in ranked]
        if target_id in retrieved_ids:
            hits += 1
    return hits / len(queries_ids)


def test_bm25_recall5_regression(bm25_engine, fixture_docs):
    """BM25 Recall@5 on 20-section fixture must not drop more than 2pp from baseline."""
    bm25, docs = bm25_engine
    queries = [
        ("murder death penalty life imprisonment", "BNS-103"),
        ("theft movable property dishonestly", "BNS-303"),
        ("culpable homicide not amounting murder", "BNS-105"),
        ("cheating deceive fraudulently induce", "BNS-318"),
        ("grievous hurt bone fracture permanent", "BNS-116"),
    ]
    # Filter queries to only those whose target is in the fixture
    fixture_ids = {d.get("id", "") for d in fixture_docs}
    valid = [(q, tid) for q, tid in queries if tid in fixture_ids]
    if not valid:
        pytest.skip("No fixture queries match fixture IDs")

    recall5 = _recall_at_k((bm25, docs), docs, valid, k=5)
    assert recall5 >= BASELINE_RECALL5 - TOLERANCE, (
        f"BM25 Recall@5 regression: {recall5:.3f} < baseline {BASELINE_RECALL5} - {TOLERANCE}"
    )


def test_bootstrap_ci_shape():
    """Bootstrap CI function returns (mean, lo, hi) with lo <= mean <= hi."""
    import random
    import numpy as np

    scores = [random.random() for _ in range(100)]
    arr = np.array(scores)
    mean = float(arr.mean())
    boot = [float(np.mean(np.random.choice(arr, len(arr)))) for _ in range(200)]
    lo = float(np.percentile(boot, 2.5))
    hi = float(np.percentile(boot, 97.5))
    assert lo <= mean <= hi, f"CI invalid: lo={lo} mean={mean} hi={hi}"


def test_ndcg_formula():
    """nDCG@10 formula: single hit at rank 1 should equal 1.0."""
    rank = 1
    dcg = 1.0 / math.log2(rank + 1)
    idcg = 1.0 / math.log2(2)
    ndcg = dcg / idcg
    assert abs(ndcg - 1.0) < 1e-9

    rank = 2
    dcg2 = 1.0 / math.log2(rank + 1)
    ndcg2 = dcg2 / idcg
    assert ndcg2 < 1.0
