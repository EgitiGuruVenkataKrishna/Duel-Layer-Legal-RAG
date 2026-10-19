from src.nyayasetu.retrieval.exact_router import ExactMatchRouter
from src.nyayasetu.retrieval.bm25_search import BM25SearchEngine
from src.nyayasetu.retrieval.dense_search import DenseSearchEngine
from src.nyayasetu.retrieval.hybrid_rrf import HybridRRFSearchEngine
from src.nyayasetu.retrieval.parent_child import ParentChildRetriever


def test_exact_match_router():
    router = ExactMatchRouter()
    # Direct lookups
    hit1 = router.route("What is BNS 103?")
    assert hit1 is not None
    assert hit1["id"] == "BNS-103"
    assert hit1["section_no"] == "103"

    hit2 = router.route("Punishment under Section 302 IPC")
    assert hit2 is not None
    assert hit2["id"] == "IPC-302"

    hit3 = router.route("Article 21 of Constitution")
    assert hit3 is not None
    assert hit3["act_code"] == "COI"


def test_bm25_search():
    bm25 = BM25SearchEngine()
    results = bm25.search("theft movable property without consent", top_k=5)
    assert len(results) > 0
    top_ids = [doc["id"] for doc, _ in results]
    assert any("303" in tid or "378" in tid for tid in top_ids)


def test_dense_search():
    dense = DenseSearchEngine()
    results = dense.search("unlawful killing and murder punishment", top_k=5)
    assert len(results) > 0


def test_hybrid_rrf():
    hybrid = HybridRRFSearchEngine()
    results = hybrid.search("mob lynching by five or more persons on caste grounds", top_k=5)
    assert len(results) > 0
    top_ids = [doc["id"] for doc, _ in results]
    assert "BNS-103" in top_ids


def test_parent_child_retrieval():
    retriever = ParentChildRetriever()
    results = retriever.search("snatching phone on street rider", top_k=5)
    assert len(results) > 0
    top_ids = [doc["id"] for doc, _ in results]
    assert "BNS-304" in top_ids
