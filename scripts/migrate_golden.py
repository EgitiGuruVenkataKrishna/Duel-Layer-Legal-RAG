"""scripts/migrate_golden.py
Migrates legacy eval/golden_dev.jsonl + eval/golden_test.jsonl to the new
C1 schema: adds answerable, provenance, needs_review, expected_points fields.
Writes all rows to eval/golden/all.jsonl, then produces a hash-based 40/60
dev/test split at eval/golden/dev.jsonl and eval/golden/test.jsonl.
"""
import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = PROJECT_ROOT / "eval" / "golden"
GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

LEGACY_DEV = PROJECT_ROOT / "eval" / "golden_dev.jsonl"
LEGACY_TEST = PROJECT_ROOT / "eval" / "golden_test.jsonl"

UNANSWERABLE_TYPES = {"unanswerable", "out_of_scope", "harmful"}
DIRECT_LOOKUP_TYPES = {"direct_lookup", "section_lookup"}
TEMPORAL_TYPES = {"temporal", "temporal_applicability"}


def _answerable(row: dict) -> bool:
    rtype = row.get("type", "")
    if rtype in UNANSWERABLE_TYPES:
        return False
    ids = row.get("expected_section_ids", [])
    if ids and ids[0] == "NONE":
        return False
    return True


def _provenance(row: dict) -> str:
    rtype = row.get("type", "")
    if rtype in TEMPORAL_TYPES:
        return "draft"
    if rtype in UNANSWERABLE_TYPES:
        return "draft"
    return "auto"


def _needs_review(row: dict) -> bool:
    return _provenance(row) == "draft"


def _expected_points(row: dict) -> list[str]:
    # rename from expected_answer_key_points if present
    return row.get("expected_points") or row.get("expected_answer_key_points") or []


def _migrate_row(row: dict) -> dict:
    out = {
        "id": row.get("id", ""),
        "type": row.get("type", "direct_lookup"),
        "question": row.get("question", ""),
        "expected_ids": row.get("expected_ids") or row.get("expected_section_ids") or [],
        "expected_points": _expected_points(row),
        "answerable": _answerable(row),
        "provenance": _provenance(row),
        "needs_review": _needs_review(row),
    }
    return out


def _split_key(row_id: str) -> str:
    h = int(hashlib.md5(row_id.encode()).hexdigest(), 16)
    return "dev" if (h % 10) < 4 else "test"


def main() -> None:
    rows: list[dict] = []
    seen_ids: set[str] = set()
    for path in [LEGACY_DEV, LEGACY_TEST]:
        if not path.exists():
            print(f"SKIP {path} (not found)")
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row_id = row.get("id", "")
            if row_id in seen_ids:
                continue
            seen_ids.add(row_id)
            rows.append(_migrate_row(row))

    all_path = GOLDEN_DIR / "all.jsonl"
    all_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {all_path}")

    dev_rows = [r for r in rows if _split_key(r["id"]) == "dev"]
    test_rows = [r for r in rows if _split_key(r["id"]) == "test"]

    (GOLDEN_DIR / "dev.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in dev_rows) + "\n", encoding="utf-8"
    )
    (GOLDEN_DIR / "test.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in test_rows) + "\n", encoding="utf-8"
    )
    print(f"Split: {len(dev_rows)} dev ({len(dev_rows)/len(rows)*100:.0f}%) / {len(test_rows)} test")


if __name__ == "__main__":
    main()
