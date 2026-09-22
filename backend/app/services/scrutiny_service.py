"""Unified scrutiny pipeline:
documents -> OCR -> field extraction -> visual detector -> RapidFuzz -> pHash
-> Isolation Forest -> rule engine -> rule/risk results -> discrepancies -> MoTA-Twin.
AI extracts / detects / compares / flags / explains. Rules check policy. Officer decides.
"""
from sqlalchemy.orm import Session

from app.agents import mota_twin
from app.core.config import settings
from app.ml import anomaly_service, fuzzy_service
from app.models.models import (AgentResolution, Application, Discrepancy, Document, RiskResult, RuleResult)
from app.schemas.schemas import row_to_dict
from app.services import audit_service, document_service, rule_engine

NAME_DOCS = ("ST_CERTIFICATE", "INCOME_CERTIFICATE", "MARKSHEET")


def _clear_previous(db: Session, app_id: int):
    for model in (AgentResolution, Discrepancy, RiskResult, RuleResult):
        db.query(model).filter(model.application_id == app_id).delete()
    db.flush()


def run_scrutiny(db: Session, app: Application, actor: str) -> dict:
    _clear_previous(db, app.id)
    app.status = "UNDER_SCRUTINY"
    audit_service.log(db, app.id, "SCRUTINY_STARTED", actor, {}, commit=False)

    docs = db.query(Document).filter(Document.application_id == app.id).all()
    other_docs = [
        {"document_id": d.id, "application_id": d.application_id, "doc_type": d.doc_type,
         "phash": d.phash, "applicant_id": a.applicant_id}
        for d, a in db.query(Document, Application).join(Application, Document.application_id == Application.id)
        .filter(Document.application_id != app.id).all()
    ]

    # 1-4. OCR, extraction, visual detection, pHash per document
    doc_reports = []
    for d in docs:
        doc_reports.append(document_service.process_document(d, other_docs))
    db.flush()

    discrepancies: list[dict] = []
    risks: list[dict] = []

    # OCR quality risk
    if docs:
        avg_conf = sum(d.ocr_confidence or 0 for d in docs) / len(docs)
        risks.append({"check_type": "OCR", "score": round(avg_conf, 3),
                      "level": "PASS" if avg_conf >= 0.6 else "REVIEW",
                      "details": {"engines": sorted({d.ocr_engine for d in docs}), "documents": len(docs)}})

    # 5. Visual detection risk (seal/signature on certificates)
    visual_issues = []
    for d in docs:
        if d.doc_type in ("ST_CERTIFICATE", "INCOME_CERTIFICATE") and d.detection:
            det = d.detection.get("detections", {})
            for must in ("official_seal", "signature"):
                if not det.get(must, {}).get("detected"):
                    visual_issues.append(f"{d.doc_type}: {must} not detected")
    modes = sorted({(d.detection or {}).get("mode", "N/A") for d in docs})
    risks.append({"check_type": "DOCUMENT_VISUAL", "score": 0.0 if visual_issues else 1.0,
                  "level": "REVIEW" if visual_issues else "PASS",
                  "details": {"issues": visual_issues, "detector_modes": modes}})

    # 6. RapidFuzz name comparison
    name_checks = []
    for d in docs:
        n = (d.extracted_fields or {}).get("name")
        if d.doc_type in NAME_DOCS and n:
            cmp = fuzzy_service.compare_names(app.full_name, n)
            name_checks.append({"doc_type": d.doc_type, "document_id": d.id, **cmp})
            if cmp["interpretation"] != "MATCH":
                discrepancies.append({
                    "issue_type": "NAME_MISMATCH",
                    "severity": "MEDIUM" if cmp["interpretation"] == "PROBABLE_MATCH_REVIEW" else "HIGH",
                    "description": f"Name on {d.doc_type} ('{n}') differs from application ('{app.full_name}'), similarity {cmp['similarity']}",
                    "details": {"doc_type": d.doc_type, "comparison": cmp},
                })
    worst = min((c["similarity"] for c in name_checks), default=None)
    risks.append({"check_type": "NAME_MATCH", "score": worst,
                  "level": "PASS" if worst is None or worst >= settings.NAME_MATCH_THRESHOLD else "REVIEW",
                  "details": {"comparisons": name_checks}})

    # 7. Income cross-check (declared vs certificate)
    scheme = rule_engine.get_scheme(app.scheme_id)
    income_limit = next((r["value"] for r in scheme["eligibility_rules"] if r["id"] == "INCOME_LIMIT"), None)
    for d in docs:
        cert_income = (d.extracted_fields or {}).get("annual_income")
        if d.doc_type == "INCOME_CERTIFICATE" and cert_income and app.annual_income is not None:
            diff = abs(cert_income - app.annual_income) / max(app.annual_income, 1)
            if diff > settings.INCOME_TOLERANCE:
                discrepancies.append({
                    "issue_type": "INCOME_MISMATCH", "severity": "HIGH",
                    "description": f"Declared income Rs {app.annual_income:,.0f} vs certificate Rs {cert_income:,.0f} ({diff:.0%} difference)",
                    "details": {"declared_income": app.annual_income, "certificate_income": cert_income,
                                "difference_ratio": round(diff, 3), "income_limit": income_limit},
                })

    # 8. pHash duplicates
    dup_hits = []
    for rep in doc_reports:
        dc = rep["duplicate_check"]
        if dc.get("possible_duplicate"):
            match = dc["nearest"][0]
            dup_hits.append({"doc_type": rep["doc_type"], "match": match})
            discrepancies.append({
                "issue_type": "POSSIBLE_DUPLICATE", "severity": "HIGH",
                "description": f"{rep['doc_type']} is near-identical (Hamming {match['hamming_distance']}) to a document in application #{match['application_id']}",
                "details": {"doc_type": rep["doc_type"], "match": match},
            })
    risks.append({"check_type": "DUPLICATE", "score": float(min((h["match"]["hamming_distance"] for h in dup_hits), default=64)),
                  "level": "FLAG" if dup_hits else "PASS",
                  "details": {"per_document": [{"doc_type": r["doc_type"], **r["duplicate_check"]} for r in doc_reports]}})

    # 9. Isolation Forest anomaly
    anomaly = anomaly_service.score({"annual_income": app.annual_income, "marks_percentage": app.marks_percentage,
                                     "age": app.age, "claimed_fee": app.claimed_fee})
    risks.append({"check_type": "ANOMALY", "score": anomaly["anomaly_score"],
                  "level": "FLAG" if anomaly["label"] == "NEEDS_REVIEW" else "PASS", "details": anomaly})
    if anomaly["label"] == "NEEDS_REVIEW":
        discrepancies.append({"issue_type": "ANOMALY", "severity": "MEDIUM",
                              "description": "Isolation Forest marked this record as statistically unusual",
                              "details": anomaly})

    # 10. Rule engine (policy)
    evaluation = rule_engine.evaluate(app.scheme_id, {
        "category": app.category, "annual_income": app.annual_income, "marks_percentage": app.marks_percentage,
        "age": app.age, "gender": app.gender, "is_pvtg": app.is_pvtg, "documents": [d.doc_type for d in docs],
    })
    for r in evaluation["rules"]:
        db.add(RuleResult(application_id=app.id, scheme_id=app.scheme_id, rule_id=r["rule"], description=r["description"],
                          field=r["field"], actual_value=str(r["actual_value"]), expected=r["expected"],
                          passed=r["result"] == "PASS", reason=r["reason"]))
    for md in evaluation["missing_documents"]:
        discrepancies.append({"issue_type": "MISSING_DOCUMENT", "severity": "MEDIUM",
                              "description": f"Mandatory document {md} not uploaded", "details": {"doc_type": md}})
    failed = [r for r in evaluation["rules"] if r["result"] == "FAIL"]
    if failed:
        discrepancies.append({"issue_type": "ELIGIBILITY_FAILURE", "severity": "HIGH",
                              "description": "; ".join(r["reason"] for r in failed),
                              "details": {"failed_rules": failed}})

    for r in risks:
        db.add(RiskResult(application_id=app.id, **r))

    # 11. Discrepancies + MoTA-Twin resolutions
    disc_out = []
    for d in discrepancies:
        row = Discrepancy(application_id=app.id, **d)
        db.add(row)
        db.flush()
        audit_service.log(db, app.id, "DISCREPANCY_CREATED", "AI_PIPELINE",
                          {"discrepancy_id": row.id, "issue_type": row.issue_type, "description": row.description}, commit=False)
        res = mota_twin.resolve(row.issue_type, app, d["details"], docs)
        ar = AgentResolution(application_id=app.id, discrepancy_id=row.id, issue=res["issue"],
                             proposed_resolution=res["proposed_resolution"], confidence=res["confidence"],
                             requires_officer_review=res["requires_officer_review"],
                             reasoning={"steps": res["reasoning_steps"], "recommended_action": res["recommended_action"]})
        db.add(ar)
        db.flush()
        audit_service.log(db, app.id, "RESOLUTION_PROPOSED", "MoTA-Twin",
                          {"discrepancy_id": row.id, "resolution_id": ar.id, "action": res["recommended_action"],
                           "confidence": res["confidence"]}, commit=False)
        disc_out.append({**row_to_dict(row), "resolution": res})

    # 12. Recommendation + status (AI recommends; officer decides)
    flags = [r for r in risks if r["level"] in ("FLAG", "REVIEW")]
    if failed:
        recommendation, risk_level = "RECOMMEND_REJECT", "HIGH"
    elif discrepancies:
        recommendation = "NEEDS_OFFICER_REVIEW"
        risk_level = "HIGH" if any(d["severity"] == "HIGH" for d in discrepancies) else "MEDIUM"
    else:
        recommendation, risk_level = "RECOMMEND_APPROVE", "LOW" if not flags else "MEDIUM"

    app.ai_recommendation = recommendation
    app.risk_level = risk_level
    app.eligibility_score = evaluation["rank_score"]
    app.status = "AI_FLAGGED" if discrepancies else "SCRUTINY_COMPLETED"
    audit_service.log(db, app.id, "SCRUTINY_COMPLETED", actor,
                      {"recommendation": recommendation, "risk_level": risk_level,
                       "discrepancies": len(discrepancies), "status": app.status}, commit=False)
    db.commit()

    return {
        "application_id": app.id,
        "status": app.status,
        "ai_recommendation": recommendation,
        "risk_level": risk_level,
        "documents": doc_reports,
        "rule_evaluation": evaluation,
        "risks": risks,
        "discrepancies": disc_out,
        "principle": "AI extracts, detects, compares, flags and explains. Rule engine checks policy. Officer decides.",
    }
