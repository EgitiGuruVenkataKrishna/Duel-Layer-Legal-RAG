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


def test_temporal_truth_table():
    # Case 1: Offence pre-transition, FIR pre-transition
    c1 = TemporalLegalityEngine.evaluate(date(2024, 5, 10), date(2024, 6, 1))
    assert c1["substantive_code"] == "IPC"
    assert c1["procedural_code"] == "CRPC"
    assert "IEA" in c1["evidence_law"]
    assert c1["status"] == "draft_pending_review"

    # Case 2: Offence pre-transition, FIR exactly transition date (1 July 2024)
    c2 = TemporalLegalityEngine.evaluate(date(2024, 6, 30), date(2024, 7, 1))
    assert c2["substantive_code"] == "IPC"
    assert c2["procedural_code"] == "BNSS"
    assert "BSA" in c2["evidence_law"]

    # Case 3: Offence pre-transition, FIR post-transition
    c3 = TemporalLegalityEngine.evaluate(date(2024, 1, 15), date(2024, 8, 20))
    assert c3["substantive_code"] == "IPC"
    assert c3["procedural_code"] == "BNSS"
    assert "BSA" in c3["evidence_law"]

    # Case 4: Offence on transition date (1 July 2024), FIR on transition date
    c4 = TemporalLegalityEngine.evaluate(date(2024, 7, 1), date(2024, 7, 1))
    assert c4["substantive_code"] == "BNS"
    assert c4["procedural_code"] == "BNSS"
    assert "BSA" in c4["evidence_law"]

    # Case 5: Offence post-transition, FIR post-transition
    c5 = TemporalLegalityEngine.evaluate(date(2024, 10, 5), date(2024, 10, 6))
    assert c5["substantive_code"] == "BNS"
    assert c5["procedural_code"] == "BNSS"
    assert "BSA" in c5["evidence_law"]

    # Case 6: Same date default (fir_date=None)
    c6_pre = TemporalLegalityEngine.evaluate(date(2024, 3, 1))
    assert c6_pre["substantive_code"] == "IPC"
    assert c6_pre["procedural_code"] == "CRPC"

    c6_post = TemporalLegalityEngine.evaluate(date(2024, 9, 1))
    assert c6_post["substantive_code"] == "BNS"
    assert c6_post["procedural_code"] == "BNSS"
