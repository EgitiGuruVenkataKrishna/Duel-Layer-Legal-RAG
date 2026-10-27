from src.nyayasetu.verify.verifier import CitationVerifier


def test_valid_citation():
    verifier = CitationVerifier()
    answer = "Under [BNS, Section 103], murder is defined and penalised."
    res = verifier.verify_answer("What is murder?", answer, [{"id": "BNS-103"}])
    assert res["total_citations"] == 1
    assert res["valid_citations"] == 1
    assert res["citation_validity"] == 1.0
    assert not res["should_abstain"]
    assert res["status"] == "verified"


def test_fake_statutory_identifier():
    verifier = CitationVerifier()
    answer = "Under [BNS, Section 999], fictional offence applies."
    res = verifier.verify_answer("What is section 999?", answer, [])
    assert res["total_citations"] == 1
    assert res["valid_citations"] == 0
    assert res["citation_validity"] == 0.0
    assert res["should_abstain"] is True
    assert res["status"] == "abstained"


def test_altered_quotation():
    verifier = CitationVerifier()
    # Section 103 BNS text does not contain "completely fabricated imaginary quote"
    answer = 'According to [BNS, Section 103], the law says "completely fabricated imaginary quote that never existed in statute".'
    res = verifier.verify_answer("Murder text", answer, [{"id": "BNS-103"}])
    assert res["claims"][0]["is_valid"] is True
    assert res["claims"][0]["quote_matched"] is False
    assert res["valid_citations"] == 0
    assert res["should_abstain"] is True


def test_thirty_percent_abstention_rule():
    verifier = CitationVerifier()
    # 1 valid citation, 3 fake citations -> validity = 1/4 = 0.25 (< 0.30)
    answer = (
        "Relevant provisions include [BNS, Section 103], [BNS, Section 991], "
        "[BNS, Section 992], and [BNS, Section 993]."
    )
    res = verifier.verify_answer("Provisions", answer, [])
    assert res["total_citations"] == 4
    assert res["valid_citations"] == 1
    assert res["citation_validity"] == 0.25
    assert res["should_abstain"] is True
    assert res["status"] == "abstained"


def test_near_miss_citation():
    verifier = CitationVerifier()
    # Section 302 IPC exists
    answer = "As per [IPC, Section 302], punishment for murder is prescribed."
    res = verifier.verify_answer("IPC 302", answer, [])
    assert res["valid_citations"] == 1
    assert res["citation_validity"] == 1.0
