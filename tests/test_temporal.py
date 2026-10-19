from datetime import date
from src.nyayasetu.temporal.classifier import TemporalLegalityEngine


def test_offence_before_july_2024():
    # Incident on 30 June 2024, FIR on 5 July 2024
    res = TemporalLegalityEngine.evaluate(date(2024, 6, 30), date(2024, 7, 5))
    assert res["substantive_code"] == "IPC"
    assert res["procedural_code"] == "BNSS"
    assert "Article 20(1)" in res["constitutional_basis"]


def test_offence_after_july_2024():
    # Incident on 2 July 2024, FIR on 3 July 2024
    res = TemporalLegalityEngine.evaluate(date(2024, 7, 2), date(2024, 7, 3))
    assert res["substantive_code"] == "BNS"
    assert res["procedural_code"] == "BNSS"
    assert res["evidence_law"] == "Bharatiya Sakshya Adhiniyam (BSA), 2023"


def test_analyze_query_string():
    query = "offence occurred on 30 June 2024, FIR filed on 5 July 2024: which law applies?"
    res = TemporalLegalityEngine.analyze_query(query)
    assert res is not None
    assert res["substantive_code"] == "IPC"
    assert res["procedural_code"] == "BNSS"
