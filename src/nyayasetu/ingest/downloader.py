import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Dict, Any, List


class ManifestDownloader:
    """
    Validates and manages official statute PDFs based on data/MANIFEST.json.
    Ensures that only official India Code and Gazette sources are ingested.
    """

    def __init__(self, project_root: str | None = None):
        if project_root is None:
            project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
        self.project_root = Path(project_root)
        self.manifest_path = self.project_root / "data" / "MANIFEST.json"

    def load_manifest(self) -> Dict[str, Any]:
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found at {self.manifest_path}")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest().upper()

    def verify_all(self) -> List[Dict[str, Any]]:
        manifest = self.load_manifest()
        results = []
        entries = manifest.get("statutes", []) + manifest.get("judgments", [])

        for entry in entries:
            rel_path = entry.get("relative_path")
            full_path = self.project_root / rel_path
            expected_hash = entry.get("sha256")
            status = {
                "id": entry.get("id"),
                "file": rel_path,
                "exists": full_path.exists(),
                "hash_valid": False,
                "expected_hash": expected_hash,
                "actual_hash": None,
            }

            if full_path.exists() and expected_hash:
                actual_hash = self.calculate_sha256(full_path)
                status["actual_hash"] = actual_hash
                status["hash_valid"] = (actual_hash == expected_hash)
            results.append(status)

        return results

    def download_if_missing(self, entry: Dict[str, Any]) -> bool:
        rel_path = entry.get("relative_path")
        full_path = self.project_root / rel_path
        source_url = entry.get("source_url")

        if full_path.exists():
            return True

        if not source_url:
            return False

        full_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            req = urllib.request.Request(
                source_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp, open(full_path, "wb") as f:
                f.write(resp.read())
            return True
        except Exception as e:
            print(f"Error downloading {entry.get('id')} from {source_url}: {e}")
            return False


if __name__ == "__main__":
    downloader = ManifestDownloader()
    print("Verifying files against MANIFEST.json...")
    for res in downloader.verify_all():
        print(f"[{res['id']}] Exists: {res['exists']}, Hash Valid: {res['hash_valid']}")
