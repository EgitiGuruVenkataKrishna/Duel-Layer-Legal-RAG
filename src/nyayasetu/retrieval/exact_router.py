import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional


class ExactMatchRouter:
    """
    Exact-Match Routing Engine:
    Detects direct section lookups (e.g., 'BNS 103', 'Section 302 IPC', 'Sec 173 BNSS', 'Article 21')
    and routes directly to SQLite lookup, bypassing vector latency and search distortion.
    """

    PATTERNS = [
        # Match 'BNS 103', 'BNS Section 103', 'Section 103 BNS', 'Sec 103(1) of BNS'
        re.compile(r"\b(?:section|sec\.?)?\s*(\d+[A-Z]?(?:\([a-z0-9]+\))?)\s*(?:of\s+)?(BNS|BNSS|BSA|IPC|CRPC|IEA)\b", re.IGNORECASE),
        re.compile(r"\b(BNS|BNSS|BSA|IPC|CRPC|IEA)\s*(?:section|sec\.?)?\s*(\d+[A-Z]?(?:\([a-z0-9]+\))?)\b", re.IGNORECASE),
        # Constitution articles: 'Article 21', 'Art 19(1)(a)'
        re.compile(r"\b(?:article|art\.?)\s*(\d+[A-Z]?(?:\([a-z0-9]+\))?)\b", re.IGNORECASE),
    ]

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            db_path = str(project_root / "data" / "processed" / "nyayasetu.db")
        self.db_path = db_path

    def route(self, query: str) -> Optional[Dict[str, Any]]:
        clean_query = query.strip()

        for pattern in self.PATTERNS:
            m = pattern.search(clean_query)
            if m:
                groups = m.groups()
                if len(groups) == 1:
                    # Article in Constitution
                    art_no = groups[0]
                    return self._lookup("COI", art_no)
                elif groups[0].upper() in ["BNS", "BNSS", "BSA", "IPC", "CRPC", "IEA"]:
                    act_code = groups[0].upper()
                    sec_no = groups[1]
                    return self._lookup(act_code, sec_no)
                else:
                    sec_no = groups[0]
                    act_code = groups[1].upper()
                    return self._lookup(act_code, sec_no)

        return None

    def _lookup(self, act_code: str, sec_no: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Clean section number (e.g. 103(1) -> base 103 for table lookup)
        base_sec = sec_no.split("(")[0].strip()

        # 1. Exact match on section id
        sec_id = f"{act_code}-{base_sec}"
        cur.execute("SELECT * FROM sections WHERE id = ?", (sec_id,))
        row = cur.fetchone()

        if not row:
            cur.execute("SELECT * FROM sections WHERE act_code = ? AND section_no = ?", (act_code, base_sec))
            row = cur.fetchone()

        conn.close()
        if row:
            d = dict(row)
            d["route_type"] = "exact_match"
            return d
        return None


if __name__ == "__main__":
    router = ExactMatchRouter()
    print("Testing BNS 103:", router.route("What is BNS 103?"))
    print("Testing Section 302 IPC:", router.route("Punishment in Section 302 IPC"))
    print("Testing Article 21:", router.route("Explain Article 21"))
