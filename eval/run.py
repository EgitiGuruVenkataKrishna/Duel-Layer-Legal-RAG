"""eval/run.py – config-driven eval harness.
Usage:
  python eval/run.py --split dev
  python eval/run.py --split test --confirm
  python eval/run.py --split dev --mode bm25 --run-id v0_baseline
  python eval/run.py --ablation
"""
import argparse
import json
import math
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "eval" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
GOLDEN_DIR = PROJECT_ROOT / "eval" / "golden"
LOG_PATH = PROJECT_ROOT / "eval" / "test_run_log.md"


# ── Retrieval helpers (lazy import to avoid heavy deps at import time) ────────

def _load_retriever(mode: str, cfg: dict):
    modes = cfg.get("modes", {})
    mc = modes.get(mode, {})
    rtype = mc.get("retriever", mode)

    if rtype == "bm25":
        from src.nyayasetu.retrieval.bm25_search import BM25SearchEngine
        return BM25SearchEngine(), mc
    if rtype == "dense":
        from src.nyayasetu.retrieval.dense_search import DenseSearchEngine
        return DenseSearchEngine(model_name=mc.get("model", "sentence-transformers/all-MiniLM-L6-v2"),
                                  index_dir=mc.get("index_dir")), mc
    if rtype == "hybrid_rrf":
        from src.nyayasetu.retrieval.bm25_search import BM25SearchEngine
        from src.nyayasetu.retrieval.dense_search import DenseSearchEngine
        from src.nyayasetu.retrieval.hybrid_rrf import HybridRRFSearchEngine
        bm25 = BM25SearchEngine()
        dense = DenseSearchEngine(model_name=mc.get("dense_model", "sentence-transformers/all-MiniLM-L6-v2"))
        return HybridRRFSearchEngine(bm25, dense, k=mc.get("rrf_k", 60)), mc
    raise ValueError(f"Unknown retriever type: {rtype}")


def _search(retriever, query: str, mc: dict) -> list[dict]:
    top_k = mc.get("final_top_k", mc.get("bm25_top_k", mc.get("dense_top_k", mc.get("top_k", 10))))
    fetch_k = max(top_k, mc.get("bm25_top_k", 20), mc.get("dense_top_k", 20))
    raw = retriever.search(query, top_k=fetch_k)
    docs = [d for d, _ in raw] if raw and isinstance(raw[0], tuple) else raw

    # Optional reranker
    reranker_cfg = mc.get("reranker")
    if reranker_cfg:
        from src.nyayasetu.retrieval.reranker import Reranker
        rr = Reranker(model_name=reranker_cfg["model"])
        pairs = [(d, 0.0) for d in docs]
        reranked = rr.rerank(query, pairs, top_k=reranker_cfg.get("top_n", top_k))
        docs = [d for d, _ in reranked]

    # Optional parent-child expansion
    if mc.get("parent_child"):
        from src.nyayasetu.retrieval.parent_child import ParentChildRetriever
        pc = ParentChildRetriever()
        expanded = []
        seen = set()
        for doc in docs:
            parent = pc.get_parent(doc)
            pid = parent.get("id", doc.get("id"))
            if pid not in seen:
                seen.add(pid)
                expanded.append(parent)
        docs = expanded

    return docs[:top_k]


# ── Metrics ───────────────────────────────────────────────────────────────────

def is_match(expected_ids: list[str], doc: dict) -> bool:
    if "NONE" in expected_ids:
        return False
    doc_id = doc.get("id", "").upper()
    doc_sec = doc.get("section_no", "").upper()
    doc_act = doc.get("act_code", "").upper()
    for exp in expected_ids:
        exp = exp.strip().upper()
        if exp == doc_id:
            return True
        if "-" in exp:
            eact, esec = exp.split("-", 1)
            ebase = esec.split("(")[0].strip()
            if eact == doc_act and ebase in (doc_sec, esec):
                return True
    return False


def compute_row(expected_ids: list[str], docs: list[dict], latency_ms: float, answerable: bool) -> dict:
    if not answerable:
        refused = len(docs) == 0
        v = 1.0 if refused else 0.0
        return {"r5": v, "r10": v, "mrr": v, "ndcg10": v, "latency_ms": latency_ms}
    r5 = r10 = mrr = dcg = 0.0
    for rank, doc in enumerate(docs[:10], 1):
        if is_match(expected_ids, doc):
            if rank <= 5:
                r5 = 1.0
            r10 = 1.0
            if mrr == 0.0:
                mrr = 1.0 / rank
            dcg += 1.0 / math.log2(rank + 1)
            break
    ndcg = dcg / (1.0 / math.log2(2))
    return {"r5": r5, "r10": r10, "mrr": mrr, "ndcg10": ndcg, "latency_ms": latency_ms}


def bootstrap_ci(scores: list[float], b: int = 1000) -> tuple[float, float, float]:
    if not scores:
        return 0.0, 0.0, 0.0
    arr = np.array(scores, dtype=float)
    mean = float(arr.mean())
    boot = [np.mean(np.random.choice(arr, len(arr))) for _ in range(b)]
    lo = float(np.percentile(boot, 2.5))
    hi = float(np.percentile(boot, 97.5))
    return mean, lo, hi


# ── Runner ────────────────────────────────────────────────────────────────────

def load_golden(split: str) -> list[dict]:
    """Load from eval/golden/{split}.jsonl (new schema) or fall back to legacy."""
    new_path = GOLDEN_DIR / f"{split}.jsonl"
    if new_path.exists():
        rows = [json.loads(l) for l in new_path.read_text().splitlines() if l.strip()]
        # Normalize field names
        out = []
        for r in rows:
            out.append({
                "id": r.get("id", ""),
                "type": r.get("type", "direct_lookup"),
                "question": r.get("question", ""),
                "expected_ids": r.get("expected_ids") or r.get("expected_section_ids") or [],
                "answerable": r.get("answerable", True),
                "provenance": r.get("provenance", "auto"),
                "needs_review": r.get("needs_review", False),
            })
        return out
    # Legacy fallback
    legacy = PROJECT_ROOT / "eval" / f"golden_{split}.jsonl"
    if legacy.exists():
        return [json.loads(l) for l in legacy.read_text().splitlines() if l.strip()]
    raise FileNotFoundError(f"No golden set found for split '{split}'")


def run_eval(mode: str, rows: list[dict], cfg: dict) -> dict:
    retriever, mc = _load_retriever(mode, cfg)
    row_results = []
    for row in rows:
        t0 = time.time()
        docs = _search(retriever, row["question"], mc)
        lat = (time.time() - t0) * 1000
        expected = row.get("expected_ids") or row.get("expected_section_ids") or []
        answerable = row.get("answerable", "NONE" not in expected)
        m = compute_row(expected, docs, lat, answerable)
        m["id"] = row["id"]
        m["type"] = row.get("type", "direct_lookup")
        m["provenance"] = row.get("provenance", "auto")
        row_results.append(m)
    return row_results


def summarise(row_results: list[dict]) -> dict:
    all_r5 = [r["r5"] for r in row_results]
    all_r10 = [r["r10"] for r in row_results]
    all_mrr = [r["mrr"] for r in row_results]
    all_ndcg = [r["ndcg10"] for r in row_results]
    lats = [r["latency_ms"] for r in row_results]

    def stat(scores):
        m, lo, hi = bootstrap_ci(scores)
        return {"mean": round(m, 4), "ci95_lo": round(lo, 4), "ci95_hi": round(hi, 4)}

    # Per-provenance breakdown
    by_prov: dict[str, list] = {}
    for r in row_results:
        p = r.get("provenance", "auto")
        by_prov.setdefault(p, []).append(r)

    return {
        "recall_at_5": stat(all_r5),
        "recall_at_10": stat(all_r10),
        "mrr": stat(all_mrr),
        "ndcg_at_10": stat(all_ndcg),
        "latency_p50_ms": round(float(np.percentile(lats, 50)), 1),
        "latency_p95_ms": round(float(np.percentile(lats, 95)), 1),
        "n": len(row_results),
        "by_provenance": {
            p: {
                "n": len(rs),
                "recall_at_5": stat([r["r5"] for r in rs]),
                "mrr": stat([r["mrr"] for r in rs]),
            }
            for p, rs in by_prov.items()
        },
    }


def write_markdown_table(summary: dict, run_id: str, split: str, mode: str) -> str:
    s = summary
    r5 = s["recall_at_5"]
    r10 = s["recall_at_10"]
    mrr = s["mrr"]
    nd = s["ndcg_at_10"]
    lines = [
        f"# Eval Results: {run_id}",
        f"- Split: **{split}** | Mode: **{mode}** | N: **{s['n']}**",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "| Metric | Mean | 95% CI |",
        "| :--- | :---: | :---: |",
        f"| Recall@5 | {r5['mean']:.4f} | [{r5['ci95_lo']:.4f}, {r5['ci95_hi']:.4f}] |",
        f"| Recall@10 | {r10['mean']:.4f} | [{r10['ci95_lo']:.4f}, {r10['ci95_hi']:.4f}] |",
        f"| MRR | {mrr['mean']:.4f} | [{mrr['ci95_lo']:.4f}, {mrr['ci95_hi']:.4f}] |",
        f"| nDCG@10 | {nd['mean']:.4f} | [{nd['ci95_lo']:.4f}, {nd['ci95_hi']:.4f}] |",
        f"| Latency p50 ms | {s['latency_p50_ms']} | — |",
        f"| Latency p95 ms | {s['latency_p95_ms']} | — |",
        "",
        "## By Provenance",
        "| Provenance | N | Recall@5 | MRR |",
        "| :--- | :---: | :---: | :---: |",
    ]
    for prov, ps in s.get("by_provenance", {}).items():
        lines.append(
            f"| {prov} | {ps['n']} | {ps['recall_at_5']['mean']:.4f} | {ps['mrr']['mean']:.4f} |"
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], default="dev")
    ap.add_argument("--confirm", action="store_true", help="Required for --split test")
    ap.add_argument("--mode", default=None, help="Retrieval mode from configs/retrieval.yaml; defaults to active")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--ablation", action="store_true", help="Run all ablation modes on dev split")
    args = ap.parse_args()

    if args.split == "test" and not args.confirm:
        print("ERROR: --split test requires --confirm to prevent accidental test-set leakage.")
        raise SystemExit(1)

    import yaml
    cfg_path = PROJECT_ROOT / "configs" / "retrieval.yaml"
    cfg = yaml.safe_load(cfg_path.read_text()) if cfg_path.exists() else {}
    active_mode = args.mode or cfg.get("active", "hybrid_rrf")

    rows = load_golden(args.split)
    print(f"Loaded {len(rows)} rows from split='{args.split}'")

    modes_to_run = cfg.get("ablation_order", [active_mode]) if args.ablation else [active_mode]
    ablation_rows = []

    for mode in modes_to_run:
        run_id = args.run_id if (not args.ablation and args.run_id) else f"{mode}_{args.split}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
        print(f"Running mode={mode} run_id={run_id} ...")
        try:
            rr = run_eval(mode, rows, cfg)
            summary = summarise(rr)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        result = {
            "run_id": run_id,
            "mode": mode,
            "split": args.split,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": summary,
        }
        result_path = RESULTS_DIR / f"{run_id}.json"
        result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        md = write_markdown_table(summary, run_id, args.split, mode)
        (RESULTS_DIR / f"{run_id}.md").write_text(md)
        print(f"  Recall@5={summary['recall_at_5']['mean']:.4f}  MRR={summary['mrr']['mean']:.4f}")
        print(f"  Results: {result_path}")

        ablation_rows.append(
            f"| {mode} | {summary['recall_at_5']['mean']:.4f} | {summary['recall_at_10']['mean']:.4f} "
            f"| {summary['mrr']['mean']:.4f} | {summary['ndcg_at_10']['mean']:.4f} "
            f"| {summary['latency_p50_ms']} | {summary['latency_p95_ms']} |"
        )

    if args.ablation and ablation_rows:
        abl_md = [
            "# Ablation Results",
            f"Split: {args.split} | Generated: {datetime.now(timezone.utc).isoformat()}",
            "",
            "| Mode | Recall@5 | Recall@10 | MRR | nDCG@10 | p50ms | p95ms |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        ] + ablation_rows
        (RESULTS_DIR / "ablation.md").write_text("\n".join(abl_md))
        print(f"Ablation table → {RESULTS_DIR / 'ablation.md'}")

    if args.split == "test":
        ts = datetime.now(timezone.utc).isoformat()
        entry = f"\n## {ts} | split=test | mode={active_mode} | run_id={args.run_id or 'auto'}\n"
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(entry)


if __name__ == "__main__":
    main()
