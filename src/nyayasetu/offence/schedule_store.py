import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional


class OffenceClassificationStore:
    """
    Interface for querying statutory offence classifications from the BNSS First Schedule:
    bailable, cognizable, court triable, compoundable, punishment.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            db_path = str(project_root / "data" / "processed" / "nyayasetu.db")
        self.db_path = db_path

    def get_offence(self, section_str: str) -> Optional[Dict[str, Any]]:
        clean_sec = section_str.replace("BNS", "").replace("Section", "").replace("Sec", "").strip()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Try exact match, then base section match
        cur.execute("SELECT * FROM offences WHERE section = ?", (clean_sec,))
        row = cur.fetchone()

        if not row:
            base_sec = clean_sec.split("(")[0].strip()
            cur.execute("SELECT * FROM offences WHERE section LIKE ? LIMIT 1", (f"{base_sec}%",))
            row = cur.fetchone()

        conn.close()
        if row:
            return dict(row)
        return None

    def format_summary(self, offence_data: Dict[str, Any]) -> str:
        return (
            f"**Section {offence_data['section']} {offence_data['act']}**\n"
            f"- **Offence**: {offence_data['offence']}\n"
            f"- **Punishment**: {offence_data['punishment']}\n"
            f"- **Cognizable**: {offence_data['cognizable']}\n"
            f"- **Bailable**: {offence_data['bailable']}\n"
            f"- **Compoundable**: {offence_data['compoundable']}\n"
            f"- **Triable By**: {offence_data['triable_by']}"
        )


if __name__ == "__main__":
    store = OffenceClassificationStore()
    sample = store.get_offence("103(1)")
    if sample:
        print(store.format_summary(sample))
    else:
        print("Section not found.")
