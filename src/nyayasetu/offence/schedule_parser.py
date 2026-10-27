import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List
import fitz


class BNSSScheduleParser:
    """
    Parses the First Schedule of BNSS (Classification of Offences) into SQLite.
    Captures: section, offence, punishment, cognizable, bailable, triable_by, compoundable.
    """

    def __init__(self, project_root: str | None = None):
        if project_root is None:
            project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
        self.project_root = Path(project_root)
        self.pdf_path = self.project_root / "data" / "raw" / "statutes" / "Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023.pdf"
        self.db_path = self.project_root / "data" / "processed" / "nyayasetu.db"

    def init_table(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS offences (
                section TEXT PRIMARY KEY,
                act TEXT NOT NULL,
                offence TEXT NOT NULL,
                punishment TEXT,
                cognizable TEXT,
                bailable TEXT,
                compoundable TEXT,
                triable_by TEXT
            )
        """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_offence_bailable ON offences(bailable)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_offence_cognizable ON offences(cognizable)")
        cur.execute(
            """
            CREATE VIEW IF NOT EXISTS offence_classification AS
            SELECT section, cognizable, bailable, compoundable, triable_by, punishment AS punishment_text
            FROM offences
            """
        )
        conn.commit()
        conn.close()

    def parse_schedule(self) -> List[Dict[str, Any]]:
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"BNSS PDF not found at {self.pdf_path}")

        doc = fitz.open(str(self.pdf_path))
        records: Dict[str, Dict[str, Any]] = {}

        # First Schedule begins around page 158 and extends to page 225
        for pno in range(157, min(226, len(doc))):
            text = doc[pno].get_text("text")
            lines = [l.strip() for l in text.split("\n") if l.strip()]

            for idx, line in enumerate(lines):
                # Match section pattern like 103, 103(1), 303(2), etc.
                m = re.match(r"^(\d+[A-Z]?(?:\([a-z0-9]+\))?)$", line)
                if m and line not in ["1", "2", "3", "4", "5", "6"]:
                    sec = m.group(1)
                    end_idx = min(len(lines), idx + 25)
                    for j in range(idx + 1, end_idx):
                        if (
                            re.match(r"^\d+[A-Z]?(?:\([a-z0-9]+\))?$", lines[j])
                            and lines[j] not in ["1", "2", "3", "4", "5", "6"]
                        ):
                            end_idx = j
                            break

                    chunk = lines[idx + 1 : end_idx]
                    chunk_str = " ".join(chunk)

                    cog = "Cognizable"
                    if "Non-cognizable" in chunk_str:
                        cog = "Non-cognizable"
                    elif "Cognizable" in chunk_str:
                        cog = "Cognizable"

                    bail = "Non-bailable"
                    if "Non-bailable" in chunk_str:
                        bail = "Non-bailable"
                    elif "Bailable" in chunk_str:
                        bail = "Bailable"

                    court = "Any Magistrate"
                    if "Court of Session" in chunk_str:
                        court = "Court of Session"
                    elif "Magistrate of the first class" in chunk_str:
                        court = "Magistrate of the first class"

                    # Parse offence & punishment fragments
                    offence = "Offence under Section " + sec
                    punish = "As prescribed under BNS"
                    parts = re.split(r"(?:Cognizable|Non-cognizable|Bailable|Non-bailable)", chunk_str)
                    if parts and len(parts[0].strip()) > 3:
                        offence_punish = parts[0].strip()
                        # Often sentence 1 is offence, sentence 2 is punishment
                        split_sentences = offence_punish.split(". ")
                        if len(split_sentences) > 1:
                            offence = split_sentences[0].strip()
                            punish = ". ".join(split_sentences[1:]).strip()
                        else:
                            offence = offence_punish

                    # Compoundability: check BNS Section 359 / Section 320 equivalent
                    # Petty thefts, simple hurt, defamation are compoundable; heinous are non-compoundable
                    sec_base = re.findall(r"\d+", sec)[0] if re.findall(r"\d+", sec) else ""
                    compoundable = "Non-compoundable"
                    if sec_base in ["115", "116", "303", "305", "351", "356", "352"]:
                        compoundable = "Compoundable"

                    if sec not in records:
                        records[sec] = {
                            "section": sec,
                            "act": "BNS",
                            "offence": offence,
                            "punishment": punish,
                            "cognizable": cog,
                            "bailable": bail,
                            "compoundable": compoundable,
                            "triable_by": court,
                        }

        doc.close()
        return list(records.values())

    def save_to_db(self, records: List[Dict[str, Any]]):
        self.init_table()
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        for r in records:
            cur.execute(
                """
                INSERT OR REPLACE INTO offences (
                    section, act, offence, punishment, cognizable,
                    bailable, compoundable, triable_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    r["section"],
                    r["act"],
                    r["offence"],
                    r["punishment"],
                    r["cognizable"],
                    r["bailable"],
                    r["compoundable"],
                    r["triable_by"],
                ),
            )
        conn.commit()
        conn.close()

    def run(self) -> int:
        records = self.parse_schedule()
        self.save_to_db(records)
        print(f"BNSS First Schedule parsed: {len(records)} offences indexed into SQLite.")
        return len(records)


if __name__ == "__main__":
    parser = BNSSScheduleParser()
    parser.run()
