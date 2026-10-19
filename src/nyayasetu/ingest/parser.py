import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List
import fitz


class StatuteParser:
    """
    Parses official gazette and India Code PDFs into structured JSONL records
    with full legal hierarchy: parent sections and child nodes (subsections,
    illustrations, explanations, exceptions, provisos).
    """

    def __init__(self, project_root: str | None = None):
        if project_root is None:
            project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
        self.project_root = Path(project_root)
        self.manifest_path = self.project_root / "data" / "MANIFEST.json"
        self.processed_dir = self.project_root / "data" / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.processed_dir / "nyayasetu.db"

    @staticmethod
    def extract_child_nodes(text: str) -> Dict[str, List[str]]:
        """
        Extracts subsections, illustrations, explanations, exceptions, and provisos.
        All child nodes remain bound to the parent section id.
        """
        subsections = []
        illustrations = []
        explanations = []
        exceptions = []
        provisos = []

        # Subsections: e.g. (1) ..., (2) ...
        sub_matches = list(
            re.finditer(
                r"(?:^|\n)\s*(\(\d+\))\s+(.*?)(?=(?:\n\s*\(\d+\)|\n\s*(?:Explanation|Illustration|Exception|Provided)|\Z))",
                text,
                re.DOTALL,
            )
        )
        for m in sub_matches:
            subsections.append(f"{m.group(1)} {m.group(2).strip()}")

        # Illustrations
        ill_matches = list(
            re.finditer(
                r"(?:^|\n)\s*(?:Illustrations?\.?)\s*(.*?)(?=(?:\n\s*(?:Explanation|Exception|Provided|\d+\.)|\Z))",
                text,
                re.DOTALL | re.IGNORECASE,
            )
        )
        for m in ill_matches:
            illustrations.append(m.group(1).strip())

        # Explanations
        exp_matches = list(
            re.finditer(
                r"(?:^|\n)\s*(Explanation\s*\d*[\.—\-]?)\s*(.*?)(?=(?:\n\s*(?:Explanation|Illustration|Exception|Provided|\d+\.)|\Z))",
                text,
                re.DOTALL | re.IGNORECASE,
            )
        )
        for m in exp_matches:
            explanations.append(f"{m.group(1)} {m.group(2).strip()}")

        # Exceptions
        exc_matches = list(
            re.finditer(
                r"(?:^|\n)\s*(Exception\s*\d*[\.—\-]?)\s*(.*?)(?=(?:\n\s*(?:Explanation|Illustration|Exception|Provided|\d+\.)|\Z))",
                text,
                re.DOTALL | re.IGNORECASE,
            )
        )
        for m in exc_matches:
            exceptions.append(f"{m.group(1)} {m.group(2).strip()}")

        # Provisos
        pro_matches = list(
            re.finditer(
                r"(?:^|\n)\s*(Provided\s+(?:further\s+)?that\b.*?)(?=(?:\n\s*(?:Provided|Explanation|Illustration|Exception|\d+\.)|\Z))",
                text,
                re.DOTALL | re.IGNORECASE,
            )
        )
        for m in pro_matches:
            provisos.append(m.group(1).strip())

        return {
            "subsections": subsections,
            "illustrations": illustrations,
            "explanations": explanations,
            "exceptions": exceptions,
            "provisos": provisos,
        }

    def parse_pdf(
        self, pdf_path: Path, act_code: str, act_name: str, effective_date: str, source_url: str
    ) -> List[Dict[str, Any]]:
        """
        Extracts sections, titles, and children from the official PDF.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found at {pdf_path}")

        doc = fitz.open(str(pdf_path))
        sections: Dict[str, Dict[str, Any]] = {}
        current_sec: str | None = None
        current_chapter: str = "CHAPTER I"

        for pno in range(len(doc)):
            page = doc[pno]
            blocks = page.get_text("blocks")
            margin_titles: List[tuple[float, str]] = []
            main_blocks: List[tuple[float, str]] = []

            for b in blocks:
                if b[6] != 0:
                    continue
                x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4].strip()
                if y1 < 75 or y0 > 768:
                    continue

                # Marginal note on left (even page) or right (odd page)
                if x1 < 115 or x0 > 480:
                    clean_title = " ".join(text.split())
                    if not re.match(r"^\d+(\s+of\s+\d+)?\.?$", clean_title):
                        margin_titles.append((y0, clean_title))
                else:
                    main_blocks.append((y0, text))

            main_blocks.sort(key=lambda m: m[0])

            for y0, btext in main_blocks:
                chap_match = re.search(r"\b(CHAPTER\s+[IVXLCDM]+[^\n]*)", btext, re.IGNORECASE)
                if chap_match:
                    current_chapter = chap_match.group(1).strip()

                lines = btext.split("\n")
                block_consumed = False

                for line_idx, line in enumerate(lines):
                    line_str = line.strip()
                    m_sec = re.match(r"^(\d+[A-Z]?)\.\s*(.*)", line_str)
                    if m_sec:
                        sec_no = m_sec.group(1)
                        best_title = ""
                        if margin_titles:
                            closest = min(margin_titles, key=lambda m: abs(m[0] - y0))
                            if abs(closest[0] - y0) < 75:
                                best_title = closest[1]

                        pre_text = "\n".join(lines[:line_idx]).strip()
                        if pre_text and current_sec and current_sec in sections:
                            sections[current_sec]["text"] += "\n" + pre_text

                        post_text = "\n".join(lines[line_idx:]).strip()
                        current_sec = sec_no
                        sections[sec_no] = {
                            "id": f"{act_code}-{sec_no}",
                            "act": act_name,
                            "act_code": act_code,
                            "chapter": current_chapter,
                            "section_no": sec_no,
                            "title": best_title or f"Section {sec_no}",
                            "text": post_text,
                            "effective_date": effective_date,
                            "status": "In Force" if effective_date <= "2024-07-01" else "Pending",
                            "source_url": source_url,
                            "page": pno + 1,
                        }
                        block_consumed = True
                        break

                if not block_consumed and current_sec and current_sec in sections:
                    sections[current_sec]["text"] += "\n" + btext

        doc.close()

        # Attach child nodes and clean up text
        result = []
        # Sort numerically if digit, else alphanumerically
        sorted_keys = sorted(
            sections.keys(),
            key=lambda k: (int(re.findall(r"\d+", k)[0]) if re.findall(r"\d+", k) else 999999, k),
        )

        for k in sorted_keys:
            sec_data = sections[k]
            children = self.extract_child_nodes(sec_data["text"])
            sec_data.update(children)
            result.append(sec_data)

        return result

    def export_jsonl(self, records: List[Dict[str, Any]], output_path: Path):
        with open(output_path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def init_sqlite_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sections (
                id TEXT PRIMARY KEY,
                act TEXT NOT NULL,
                act_code TEXT NOT NULL,
                chapter TEXT,
                section_no TEXT NOT NULL,
                title TEXT,
                text TEXT NOT NULL,
                subsections_json TEXT,
                illustrations_json TEXT,
                explanations_json TEXT,
                exceptions_json TEXT,
                provisos_json TEXT,
                effective_date TEXT,
                status TEXT,
                source_url TEXT,
                page INTEGER
            )
        """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sections_act ON sections(act_code)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sections_no ON sections(section_no)")
        conn.commit()
        conn.close()

    def save_to_sqlite(self, records: List[Dict[str, Any]]):
        self.init_sqlite_db()
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        for r in records:
            cur.execute(
                """
                INSERT OR REPLACE INTO sections (
                    id, act, act_code, chapter, section_no, title, text,
                    subsections_json, illustrations_json, explanations_json,
                    exceptions_json, provisos_json, effective_date, status,
                    source_url, page
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    r["id"],
                    r["act"],
                    r["act_code"],
                    r["chapter"],
                    r["section_no"],
                    r["title"],
                    r["text"],
                    json.dumps(r.get("subsections", [])),
                    json.dumps(r.get("illustrations", [])),
                    json.dumps(r.get("explanations", [])),
                    json.dumps(r.get("exceptions", [])),
                    json.dumps(r.get("provisos", [])),
                    r.get("effective_date"),
                    r.get("status"),
                    r.get("source_url"),
                    r.get("page"),
                ),
            )
        conn.commit()
        conn.close()

    def process_all_statutes(self) -> Dict[str, int]:
        manifest_path = self.manifest_path
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest missing at {manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        counts = {}
        for item in manifest.get("statutes", []):
            code = item["id"].split("-")[0]
            rel_path = item.get("relative_path")
            full_path = self.project_root / rel_path
            if not full_path.exists():
                print(f"Skipping {item['id']}: file {full_path} not found.")
                continue

            print(f"Parsing {item['act_name']} from {rel_path}...")
            records = self.parse_pdf(
                pdf_path=full_path,
                act_code=code,
                act_name=item["act_name"],
                effective_date=item.get("effective_date", "2024-07-01"),
                source_url=item.get("source_url", ""),
            )

            out_jsonl = self.processed_dir / f"{code.lower()}_sections.jsonl"
            self.export_jsonl(records, out_jsonl)
            self.save_to_sqlite(records)
            counts[code] = len(records)
            print(f"-> Extracted {len(records)} sections for {code} saved to {out_jsonl.name}")

        return counts


if __name__ == "__main__":
    parser = StatuteParser()
    results = parser.process_all_statutes()
    print("Statute parsing complete:", results)
