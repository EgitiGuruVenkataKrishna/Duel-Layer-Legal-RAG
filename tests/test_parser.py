import json
import sqlite3
from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def db_conn():
    project_root = Path(__file__).resolve().parent.parent
    db_path = project_root / "data" / "processed" / "nyayasetu.db"
    assert db_path.exists(), f"Database not found at {db_path}. Run parser first."
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_section_counts(db_conn):
    """
    Build FAILS on count mismatch against official Gazette & India Code text:
    - BNS: exactly 358
    - BNSS: exactly 531
    - BSA: exactly 170
    - IPC: at least 511 base sections
    - CrPC: exactly 484
    - IEA: exactly 167
    """
    cur = db_conn.cursor()

    # BNS
    cur.execute("SELECT count(*) as cnt FROM sections WHERE act_code = 'BNS'")
    bns_cnt = cur.fetchone()["cnt"]
    assert bns_cnt == 358, f"BNS count mismatch: expected 358, got {bns_cnt}"

    # BNSS
    cur.execute("SELECT count(*) as cnt FROM sections WHERE act_code = 'BNSS'")
    bnss_cnt = cur.fetchone()["cnt"]
    assert bnss_cnt == 531, f"BNSS count mismatch: expected 531, got {bnss_cnt}"

    # BSA
    cur.execute("SELECT count(*) as cnt FROM sections WHERE act_code = 'BSA'")
    bsa_cnt = cur.fetchone()["cnt"]
    assert bsa_cnt == 170, f"BSA count mismatch: expected 170, got {bsa_cnt}"

    # IPC
    cur.execute("SELECT count(*) as cnt FROM sections WHERE act_code = 'IPC'")
    ipc_cnt = cur.fetchone()["cnt"]
    assert ipc_cnt >= 511, f"IPC count mismatch: expected >= 511, got {ipc_cnt}"

    # CrPC
    cur.execute("SELECT count(*) as cnt FROM sections WHERE act_code = 'CRPC'")
    crpc_cnt = cur.fetchone()["cnt"]
    assert crpc_cnt == 484, f"CrPC count mismatch: expected 484, got {crpc_cnt}"

    # IEA
    cur.execute("SELECT count(*) as cnt FROM sections WHERE act_code = 'IEA'")
    iea_cnt = cur.fetchone()["cnt"]
    assert iea_cnt == 167, f"IEA count mismatch: expected 167, got {iea_cnt}"


def test_contiguous_numbering_bns(db_conn):
    """Verify BNS has contiguous numbering from Section 1 to 358 without gaps."""
    cur = db_conn.cursor()
    cur.execute("SELECT section_no FROM sections WHERE act_code = 'BNS'")
    sec_nos = set(row["section_no"] for row in cur.fetchall())

    missing = [str(i) for i in range(1, 359) if str(i) not in sec_nos]
    assert len(missing) == 0, f"BNS has gaps in numbering: missing {missing}"


def test_contiguous_numbering_bnss(db_conn):
    """Verify BNSS has contiguous numbering from Section 1 to 531 without gaps."""
    cur = db_conn.cursor()
    cur.execute("SELECT section_no FROM sections WHERE act_code = 'BNSS'")
    sec_nos = set(row["section_no"] for row in cur.fetchall())

    missing = [str(i) for i in range(1, 532) if str(i) not in sec_nos]
    assert len(missing) == 0, f"BNSS has gaps in numbering: missing {missing}"


def test_contiguous_numbering_bsa(db_conn):
    """Verify BSA has contiguous numbering from Section 1 to 170 without gaps."""
    cur = db_conn.cursor()
    cur.execute("SELECT section_no FROM sections WHERE act_code = 'BSA'")
    sec_nos = set(row["section_no"] for row in cur.fetchall())

    missing = [str(i) for i in range(1, 171) if str(i) not in sec_nos]
    assert len(missing) == 0, f"BSA has gaps in numbering: missing {missing}"


def test_no_empty_text(db_conn):
    """Build fails if any section has empty body text."""
    cur = db_conn.cursor()
    cur.execute("SELECT id, text FROM sections WHERE trim(text) = '' OR text IS NULL")
    empty_secs = cur.fetchall()
    assert len(empty_secs) == 0, f"Found sections with empty text: {[s['id'] for s in empty_secs]}"


def test_no_section_with_title_but_no_body(db_conn):
    """Build fails if any statutory section has a title but less than 15 characters of body text."""
    cur = db_conn.cursor()
    cur.execute(
        "SELECT id, title, text FROM sections WHERE act_code IN ('BNS', 'BNSS', 'BSA', 'IPC', 'CRPC', 'IEA') AND length(trim(text)) < 15"
    )
    too_short = cur.fetchall()
    assert len(too_short) == 0, f"Found sections with empty body: {[s['id'] for s in too_short]}"


def test_child_nodes_bound_to_parent(db_conn):
    """Verify that subsections and illustrations exist as bound child nodes, not orphan chunks."""
    cur = db_conn.cursor()
    # Check Section 103 BNS (Murder) has mob lynching child clause
    cur.execute("SELECT text, subsections_json FROM sections WHERE id = 'BNS-103'")
    row = cur.fetchone()
    assert row is not None
    assert "mob" in row["text"].lower() or "group of five" in row["text"].lower()
    subs = json.loads(row["subsections_json"])
    assert len(subs) > 0, "BNS-103 must have bound subsections"
