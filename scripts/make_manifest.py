"""scripts/make_manifest.py – regenerate data/MANIFEST.json from data/sources.yaml + SHA-256."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCES_PATH = PROJECT_ROOT / "data" / "sources.yaml"
MANIFEST_PATH = PROJECT_ROOT / "data" / "MANIFEST.json"


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> None:
    sources = yaml.safe_load(SOURCES_PATH.read_text(encoding="utf-8"))
    statutes = []
    for s in sources.get("statutes", []):
        rel = PROJECT_ROOT / s["relative_path"]
        entry = {k: v for k, v in s.items() if k != "relative_path"}
        entry["relative_path"] = s["relative_path"]
        entry["sha256"] = sha256_file(rel)
        entry["manifest_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        statutes.append(entry)

    judgments = []
    for j in sources.get("judgments", []):
        rel = PROJECT_ROOT / j["relative_path"]
        entry = {k: v for k, v in j.items() if k != "relative_path"}
        entry["relative_path"] = j["relative_path"]
        entry["sha256"] = sha256_file(rel)
        entry["manifest_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        judgments.append(entry)

    manifest = {
        "version": "2.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "statutes": statutes,
        "judgments": judgments,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"MANIFEST written to {MANIFEST_PATH}")
    missing = [s["file_name"] for s in statutes if s["sha256"] is None]
    if missing:
        print("WARNING – PDFs not found locally (SHA-256 = null):")
        for f in missing:
            print(f"  {f}")


if __name__ == "__main__":
    main()
