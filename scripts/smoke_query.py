"""CLI smoke test for the dual-tier pipeline. Usage:
    python scripts/smoke_query.py "What is BNS 103?"
    python scripts/smoke_query.py --compare "What is BNS 103?"
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from src.nyayasetu.compare.chatgpt import ChatGPTBaseline
from src.nyayasetu.pipeline.dual_tier import DualTierPipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="?", default="What is BNS 103?")
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()

    pipe = DualTierPipeline()
    result = pipe.run(args.query)
    slim = {
        "tier": result["tier"],
        "route_type": result["route_type"],
        "metrics": result["metrics"],
        "answer": result["answer"][:1200],
        "retrieved_ids": [d.get("id") for d in result["retrieved_sections"]],
    }
    print(json.dumps(slim, indent=2, default=str))

    if args.compare:
        gpt = ChatGPTBaseline().ask(args.query)
        print("\n--- ChatGPT ---")
        print(json.dumps({k: gpt.get(k) for k in ("model", "available", "error", "answer")}, indent=2)[:2000])


if __name__ == "__main__":
    main()
