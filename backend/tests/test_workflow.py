from pathlib import Path

from app.core.config import settings


def _scrutiny(client, auth, app_id):
    r = client.post(f"/api/v1/applications/{app_id}/scrutiny", headers=auth)
    assert r.status_code == 200, r.text
    return r.json()


def test_clean_case_end_to_end(client, auth):
    rep = _scrutiny(client, auth, 1)
    assert rep["ai_recommendation"] == "RECOMMEND_APPROVE"
    assert client.post("/api/v1/applications/1/approve", json={"reason": "All checks passed"}, headers=auth).status_code == 200
    s = client.post("/api/v1/applications/1/sanction", headers=auth).json()
    assert s["sanction_number"].startswith("MoTA/NFST/")
    assert client.get(s["pdf_url"], headers=auth).headers["content-type"] == "application/pdf"
    p = client.post(f"/api/v1/sanctions/{s['id']}/payment", headers=auth).json()
    assert p["status"] == "PAID" and p["payment_reference"].startswith("PFMS-DEMO-")
    actions = [a["action"] for a in client.get("/api/v1/applications/1/audit", headers=auth).json()]
    for expected in ("APPLICATION_CREATED", "DOCUMENT_UPLOADED", "SCRUTINY_COMPLETED",
                     "OFFICER_APPROVE", "SANCTION_GENERATED", "PAYMENT_COMPLETED"):
        assert expected in actions


def test_income_failure(client, auth):
    rep = _scrutiny(client, auth, 2)
    assert rep["ai_recommendation"] == "RECOMMEND_REJECT"


def test_twin_name_mismatch(client, auth):
    rep = _scrutiny(client, auth, 3)
    d = [x for x in rep["discrepancies"] if x["issue_type"] == "NAME_MISMATCH"][0]
    assert d["resolution"]["recommended_action"] == "ACCEPT_WITH_NOTE"
    assert d["resolution"]["requires_officer_review"] is True
    assert d["resolution"]["confidence"] >= 0.8


def test_duplicate_anomaly_missing(client, auth):
    types4 = {d["issue_type"] for d in _scrutiny(client, auth, 4)["discrepancies"]}
    types5 = {d["issue_type"] for d in _scrutiny(client, auth, 5)["discrepancies"]}
    rep6 = _scrutiny(client, auth, 6)
    assert "POSSIBLE_DUPLICATE" in types4
    assert "ANOMALY" in types5
    miss = [d for d in rep6["discrepancies"] if d["issue_type"] == "MISSING_DOCUMENT"][0]
    assert miss["resolution"]["recommended_action"] == "FETCH_FROM_DIGILOCKER"


def test_create_upload_scrutiny(client, auth):
    body = {"full_name": "Priya Soren", "scheme_id": "NFST", "state": "Jharkhand", "age": 25,
            "annual_income": 300000, "marks_percentage": 76.5, "claimed_fee": 444000}
    app = client.post("/api/v1/applications", json=body, headers=auth).json()
    samples = Path(settings.GENERATED_DIR) / "sample_docs"
    for doc_type, fname in (("ST_CERTIFICATE", "priya_soren_st_certificate.png"),
                            ("INCOME_CERTIFICATE", "priya_soren_income_certificate.png"),
                            ("MARKSHEET", "priya_soren_marksheet.png")):
        with open(samples / fname, "rb") as f:
            r = client.post(f"/api/v1/applications/{app['id']}/documents", data={"doc_type": doc_type},
                            files={"file": (fname, f, "image/png")}, headers=auth)
        assert r.status_code == 201, r.text
    bad = client.post(f"/api/v1/applications/{app['id']}/documents", data={"doc_type": "OTHER"},
                      files={"file": ("x.exe", b"MZ", "application/octet-stream")}, headers=auth)
    assert bad.status_code == 400
    rep = _scrutiny(client, auth, app["id"])
    assert rep["ai_recommendation"] == "RECOMMEND_APPROVE"


def test_integrations_and_dashboard(client, auth):
    imp = client.post("/api/v1/integrations/nsp/import", json={"count": 2}, headers=auth).json()
    assert imp["imported"] == 2
    assert client.post("/api/v1/integrations/nsp/status-sync", headers=auth).json()["accepted"] >= 8
    assert client.get("/api/v1/integrations/digilocker/STU-JH-100001", headers=auth).json()["documents"]
    stats = client.get("/api/v1/dashboard/stats", headers=auth).json()
    assert stats["paid"] >= 1 and stats["total_applications"] >= 8
