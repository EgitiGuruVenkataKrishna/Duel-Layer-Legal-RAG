import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple


from pydantic import BaseModel, Field


class CitationClaim(BaseModel):
    act_code: str = Field(..., description="Statute code (e.g. BNS, IPC, BNSS, CRPC, BSA, IEA, COI)")
    section_no: str = Field(..., description="Section number (e.g. 103, 302, 103(1))")
    quoted_text: str | None = Field(default=None, description="Exact phrase quoted from the section")
    is_valid: bool = Field(default=False, description="Whether section exists in authoritative corpus")
    quote_matched: bool = Field(default=True, description="Whether quoted text matches statutory text")


class VerificationResult(BaseModel):
    total_citations: int
    valid_citations: int
    citation_validity: float
    is_abstention: bool
    should_abstain: bool = Field(default=False, description="True if citation validity < 0.30 threshold")
    citations_found: List[Tuple[str, str]]
    claims: List[CitationClaim] = Field(default_factory=list)
    retrieved_section_ids: List[str] = Field(default_factory=list)
    status: str = Field(default="verified")


class CitationVerifier:
    """
    Validates citation integrity and statutory grounding of generated answers.
    Ensures that every cited section exists in the statutory corpus and quoted phrases match.
    Enforces calibrated abstention when citation validity < 30%.
    """

    CITATION_PATTERN = re.compile(
        r"\[(?:Source:\s*)?(?:Act:\s*)?([A-Za-z]+)(?:,\s*)(?:Chapter\s+[IVXLCDM0-9]+,\s*)?(?:Section\s+)(\d+[A-Z]?(?:\([a-z0-9]+\))?)[^\]]*\]",
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

    def get_section_text(self, act_code: str, sec_no: str) -> str | None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        base_sec = sec_no.split("(")[0].strip()
        if act_code != "UNKNOWN":
            cur.execute(
                "SELECT text FROM sections WHERE act_code = ? AND section_no = ?",
                (act_code, base_sec),
            )
        else:
            cur.execute("SELECT text FROM sections WHERE section_no = ?", (base_sec,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None

    def verify_section_exists(self, act_code: str, sec_no: str) -> bool:
        return self.get_section_text(act_code, sec_no) is not None

    def verify_quote(self, act_code: str, sec_no: str, quote: str) -> bool:
        statute_text = self.get_section_text(act_code, sec_no)
        if not statute_text:
            return False
        clean_statute = re.sub(r"\s+", " ", statute_text.lower()).strip()
        clean_quote = re.sub(r"\s+", " ", quote.lower()).strip()
        return clean_quote in clean_statute

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
        claims = []

        # Find quotes near citations if any
        quotes = re.findall(r'"([^"]{10,})"', answer)

        for idx, (act, sec) in enumerate(citations):
            exists = self.verify_section_exists(act, sec)
            quote_matched = True
            quoted_text = None
            if idx < len(quotes):
                quoted_text = quotes[idx]
                quote_matched = self.verify_quote(act, sec, quoted_text)

            if exists and quote_matched:
                valid_citations += 1

            claims.append(
                CitationClaim(
                    act_code=act,
                    section_no=sec,
                    quoted_text=quoted_text,
                    is_valid=exists,
                    quote_matched=quote_matched,
                )
            )

        citation_validity = (valid_citations / total_citations) if total_citations > 0 else (1.0 if is_refusal else 0.5)
        # 30% abstention rule: if citations are present but validity < 0.30, model must abstain
        should_abstain = total_citations > 0 and citation_validity < 0.30

        retrieved_ids = [d.get("id") for d in retrieved_docs if isinstance(d, dict)]

        res = VerificationResult(
            total_citations=total_citations,
            valid_citations=valid_citations,
            citation_validity=round(citation_validity, 4),
            is_abstention=is_refusal,
            should_abstain=should_abstain,
            citations_found=citations,
            claims=claims,
            retrieved_section_ids=retrieved_ids,
            status="abstained" if should_abstain else ("verified" if citation_validity >= 0.70 else "unverified"),
        )
        return res.model_dump()


if __name__ == "__main__":
    verifier = CitationVerifier()
    test_ans = "Under [BNS, Section 103(1)], murder is punishable by death or life imprisonment."
    res = verifier.verify_answer("What is murder in BNS?", test_ans, [])
    print("Verification:", res)
