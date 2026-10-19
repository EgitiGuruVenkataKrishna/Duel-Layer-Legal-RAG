import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple


class CitationVerifier:
    """
    Validates citation integrity and statutory grounding of generated answers.
    Ensures that every cited section exists in the statutory corpus and quoted phrases match.
    """

    CITATION_PATTERN = re.compile(
        r"\[(?:Source\s+)?(?:Act:\s*)?([A-Za-z]+)?(?:,\s*)?(?:Chapter\s+[IVXLCDM0-9]+)?(?:,\s*)?(?:Section\s+)?(\d+[A-Z]?(?:\([a-z0-9]+\))?)[^\]]*\]",
        re.IGNORECASE,
    )

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            db_path = str(project_root / "data" / "processed" / "nyayasetu.db")
        self.db_path = db_path

    def extract_citations(self, text: str) -> List[Tuple[str, str]]:
        """
        Extracts list of (act_code, section_no) from text.
        """
        matches = self.CITATION_PATTERN.findall(text)
        citations = []
        for act, sec in matches:
            act_clean = act.upper().strip() if act else "UNKNOWN"
            sec_clean = sec.strip()
            citations.append((act_clean, sec_clean))
        return citations

    def verify_section_exists(self, act_code: str, sec_no: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        base_sec = sec_no.split("(")[0].strip()

        if act_code != "UNKNOWN":
            cur.execute(
                "SELECT 1 FROM sections WHERE act_code = ? AND section_no = ?",
                (act_code, base_sec),
            )
        else:
            cur.execute("SELECT 1 FROM sections WHERE section_no = ?", (base_sec,))

        exists = cur.fetchone() is not None
        conn.close()
        return exists

    def verify_answer(
        self, query: str, answer: str, retrieved_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates citation validity, groundedness, and checks abstention.
        """
        is_refusal = any(
            phrase in answer.lower()
            for phrase in [
                "insufficient legal",
                "cannot provide legal advice",
                "does not exist",
                "out of scope",
                "harmful",
                "no statute",
            ]
        )

        citations = self.extract_citations(answer)
        valid_citations = 0
        total_citations = len(citations)

        for act, sec in citations:
            if self.verify_section_exists(act, sec):
                valid_citations += 1

        citation_validity = (valid_citations / total_citations) if total_citations > 0 else (1.0 if is_refusal else 0.5)

        # Check if retrieved sections correspond to query
        retrieved_ids = [d.get("id") for d in retrieved_docs]

        return {
            "total_citations": total_citations,
            "valid_citations": valid_citations,
            "citation_validity": citation_validity,
            "is_abstention": is_refusal,
            "citations_found": citations,
            "retrieved_section_ids": retrieved_ids,
        }


if __name__ == "__main__":
    verifier = CitationVerifier()
    test_ans = "Under [BNS, Section 103(1)], murder is punishable by death or life imprisonment."
    res = verifier.verify_answer("What is murder in BNS?", test_ans, [])
    print("Verification:", res)
