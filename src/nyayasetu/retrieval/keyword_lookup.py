import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


SYNONYMS = {
    "thief": "theft",
    "stolen": "theft",
    "stealing": "theft",
    "snatch": "snatching",
    "snatched": "snatching",
    "murder": "murder",
    "killed": "murder",
    "rape": "rape",
    "cheat": "cheating",
    "cheated": "cheating",
    "fraud": "cheating",
    "hurt": "hurt",
    "assault": "hurt",
    "dowry": "cruelty",
    "kidnap": "kidnapping",
    "kidnapped": "kidnapping",
    "rob": "robbery",
    "robbed": "robbery",
    "house break": "house-breaking",
    "trespass": "trespass",
    "defame": "defamation",
    "forge": "forgery",
    "intimidate": "criminal intimidation",
}


class KeywordLookup:
    """SQLite title/body search for short offence-name questions. No vectors."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            db_path = str(project_root / "data" / "processed" / "nyayasetu.db")
        self.db_path = db_path

    def extract_terms(self, query: str) -> List[str]:
        q = query.lower()
        terms: List[str] = []
        for src, dest in SYNONYMS.items():
            if src in q and dest not in terms:
                terms.append(dest)
        leftover = re.sub(r"[^a-z0-9\s-]", " ", q)
        for token in leftover.split():
            if token in SYNONYMS and SYNONYMS[token] not in terms:
                terms.append(SYNONYMS[token])
        return terms

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        terms = self.extract_terms(query)
        if not terms:
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        results: List[Dict[str, Any]] = []
        seen = set()
        for term in terms:
            like = f"%{term}%"
            cur.execute(
                """
                SELECT * FROM sections
                WHERE lower(title) LIKE ? OR lower(text) LIKE ?
                ORDER BY CASE WHEN lower(title) LIKE ? THEN 0 ELSE 1 END,
                         CASE WHEN act_code IN ('BNS','BNSS','BSA') THEN 0 ELSE 1 END
                LIMIT ?
                """,
                (like, like, like, top_k),
            )
            for row in cur.fetchall():
                d = dict(row)
                if d["id"] in seen:
                    continue
                seen.add(d["id"])
                d["route_type"] = "keyword_title_lookup"
                d["retrieval_score"] = 1.0 if term in (d.get("title") or "").lower() else 0.6
                d["score_type"] = "keyword"
                results.append(d)
                if len(results) >= top_k:
                    conn.close()
                    return results
        conn.close()
        return results
