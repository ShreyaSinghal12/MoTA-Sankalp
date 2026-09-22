from app.services import rule_engine


def test_nfst_eligible():
    out = rule_engine.evaluate("NFST", {"category": "ST", "annual_income": 500000, "marks_percentage": 70, "age": 26})
    assert out["eligible"] is True
    assert all(r["result"] == "PASS" for r in out["rules"])


def test_nfst_income_failure():
    out = rule_engine.evaluate("NFST", {"category": "ST", "annual_income": 950000, "marks_percentage": 70, "age": 26})
    assert out["eligible"] is False
    failed = [r for r in out["rules"] if r["result"] == "FAIL"]
    assert failed[0]["rule"] == "INCOME_LIMIT"
    assert "violates" in failed[0]["reason"]


def test_missing_documents():
    out = rule_engine.evaluate("NOS", {"category": "ST", "annual_income": 1, "marks_percentage": 80, "age": 25,
                                       "documents": ["ST_CERTIFICATE"]})
    assert "ADMISSION_LETTER" in out["missing_documents"]
