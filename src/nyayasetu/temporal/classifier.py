import re
from datetime import date, datetime
from typing import Any, Dict, Optional


class TemporalLegalityEngine:
    """
    Evaluates temporal applicability of Indian criminal statutes (IPC vs BNS, CrPC vs BNSS, IEA vs BSA)
    under Article 20(1) of the Constitution of India and BNSS Section 531 repeal and saving clauses.
    Cutoff date: 1 July 2024 (2024-07-01).
    """

    TRANSITION_DATE = date(2024, 7, 1)

    @classmethod
    def parse_date(cls, text: str) -> Optional[date]:
        """
        Parses common date formats from queries, e.g.:
        '30 June 2024', '30-06-2024', '2024-06-30', '5 July 2024'
        """
        text = text.strip()
        # Format: DD Month YYYY
        m1 = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text)
        if m1:
            day, month_str, year = m1.groups()
            for fmt in ["%d %B %Y", "%d %b %Y"]:
                try:
                    dt = datetime.strptime(f"{day} {month_str} {year}", fmt)
                    return dt.date()
                except ValueError:
                    pass

        # Format: YYYY-MM-DD
        m2 = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
        if m2:
            try:
                return datetime.strptime(m2.group(0), "%Y-%m-%d").date()
            except ValueError:
                pass

        # Format: DD-MM-YYYY or DD/MM/YYYY
        m3 = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", text)
        if m3:
            day, month, year = m3.groups()
            try:
                return datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y").date()
            except ValueError:
                pass

        return None

    @classmethod
    def evaluate(
        cls, offence_date: date | str, fir_date: Optional[date | str] = None
    ) -> Dict[str, Any]:
        """
        Calculates governing substantive and procedural law.
        """
        if isinstance(offence_date, str):
            off_dt = cls.parse_date(offence_date)
            if not off_dt:
                raise ValueError(f"Could not parse offence date: {offence_date}")
        else:
            off_dt = offence_date

        if fir_date is not None:
            if isinstance(fir_date, str):
                f_dt = cls.parse_date(fir_date)
            else:
                f_dt = fir_date
        else:
            f_dt = off_dt

        # Substantive law (Article 20(1) Constitution of India)
        if off_dt < cls.TRANSITION_DATE:
            substantive_law = "Indian Penal Code (IPC), 1860"
            substantive_code = "IPC"
            substantive_reason = (
                f"Offence committed on {off_dt.strftime('%d %B %Y')}, prior to 1 July 2024. "
                f"Under Article 20(1) of the Constitution of India (prohibition of ex-post facto laws), "
                f"substantive criminal liability is strictly governed by the law in force at the time of the act. "
                f"Therefore, IPC applies."
            )
        else:
            substantive_law = "Bharatiya Nyaya Sanhita (BNS), 2023"
            substantive_code = "BNS"
            substantive_reason = (
                f"Offence committed on {off_dt.strftime('%d %B %Y')}, on or after 1 July 2024. "
                f"Governed by Bharatiya Nyaya Sanhita, 2023."
            )

        # Procedural law (BNSS Section 531)
        if f_dt and f_dt < cls.TRANSITION_DATE:
            procedural_law = "Code of Criminal Procedure (CrPC), 1973"
            procedural_code = "CRPC"
            procedural_reason = (
                f"FIR/Proceedings initiated on {f_dt.strftime('%d %B %Y')}, prior to 1 July 2024. "
                f"Under BNSS Section 531(2)(a), pending investigations and trials initiated prior to 1 July 2024 "
                f"continue under the Code of Criminal Procedure, 1973."
            )
        else:
            procedural_law = "Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023"
            procedural_code = "BNSS"
            if off_dt < cls.TRANSITION_DATE:
                procedural_reason = (
                    f"FIR registered on {f_dt.strftime('%d %B %Y') if f_dt else 'after 1 July 2024'}. "
                    f"Although the offence occurred prior to 1 July 2024 (charging IPC sections), the investigation, "
                    f"FIR registration, and court procedures are conducted under the procedural framework of BNSS, 2023."
                )
            else:
                procedural_reason = (
                    f"Both offence and proceedings occur on or after 1 July 2024. BNSS, 2023 applies."
                )

        evidence_law = (
            "Bharatiya Sakshya Adhiniyam (BSA), 2023"
            if (f_dt and f_dt >= cls.TRANSITION_DATE)
            else "Indian Evidence Act (IEA), 1872"
        )

        return {
            "offence_date": off_dt.isoformat(),
            "fir_date": f_dt.isoformat() if f_dt else None,
            "substantive_law": substantive_law,
            "substantive_code": substantive_code,
            "substantive_reason": substantive_reason,
            "procedural_law": procedural_law,
            "procedural_code": procedural_code,
            "procedural_reason": procedural_reason,
            "evidence_law": evidence_law,
            "constitutional_basis": "Article 20(1) Constitution of India (Bar against ex-post facto penal laws) & Section 531 BNSS",
        }

    @classmethod
    def analyze_query(cls, query: str) -> Optional[Dict[str, Any]]:
        """
        Detects if query is a temporal scenario (e.g. 'offence 30 June 2024, FIR 5 July 2024').
        """
        # Look for patterns with two dates or mentions of dates around June/July 2024
        dates_found = re.findall(
            r"(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})",
            query,
            re.IGNORECASE,
        )

        if not dates_found:
            return None

        # Clean ordinals
        clean_dates = [re.sub(r"(\d+)(st|nd|rd|th)", r"\1", d) for d in dates_found]
        parsed_dates = [cls.parse_date(d) for d in clean_dates]
        valid_dates = [d for d in parsed_dates if d is not None]

        if not valid_dates:
            return None

        if len(valid_dates) == 1:
            return cls.evaluate(valid_dates[0])
        else:
            # Assume first is offence date, second is FIR/reporting date
            return cls.evaluate(valid_dates[0], valid_dates[1])


if __name__ == "__main__":
    test_query = "offence occurred on 30 June 2024, FIR filed on 5 July 2024: which law applies?"
    res = TemporalLegalityEngine.analyze_query(test_query)
    print("Temporal Analysis Result:")
    for k, v in res.items():
        print(f"  {k}: {v}")
