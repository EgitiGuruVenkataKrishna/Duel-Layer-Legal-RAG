from src.nyayasetu.offence.schedule_store import OffenceClassificationStore


def test_murder_classification():
    store = OffenceClassificationStore()
    off = store.get_offence("103(1)")
    assert off is not None
    assert off["cognizable"] == "Cognizable"
    assert off["bailable"] == "Non-bailable"
    assert "Court of Session" in off["triable_by"]


def test_theft_classification():
    store = OffenceClassificationStore()
    off = store.get_offence("303(2)")
    assert off is not None
    assert off["bailable"] == "Non-bailable"
    assert "Magistrate" in off["triable_by"]


def test_missing_offence_classification():
    store = OffenceClassificationStore()
    off = store.get_offence("999")
    assert off is None


def test_offence_classification_table_schema_and_view():
    import sqlite3
    store = OffenceClassificationStore()
    conn = sqlite3.connect(store.db_path)
    cur = conn.cursor()
    # Check view or table exists and has 5 representative records
    cur.execute("SELECT section, cognizable, bailable, compoundable, triable_by, punishment_text FROM offence_classification LIMIT 5")
    rows = cur.fetchall()
    assert len(rows) == 5
    for r in rows:
        assert r[0] is not None  # section
        assert r[1] in ("Cognizable", "Non-cognizable", "According as offence abetted")
        assert r[2] in ("Bailable", "Non-bailable", "According as offence abetted")
    conn.close()


def test_offence_formatting():
    store = OffenceClassificationStore()
    off = store.get_offence("103(1)")
    summary = store.format_summary(off)
    assert "Section 103(1)" in summary
    assert "Cognizable" in summary
    assert "Non-bailable" in summary
