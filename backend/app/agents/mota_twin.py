"""MoTA-Twin v1: deterministic discrepancy-resolution agent.

It gathers evidence, reasons step by step and PROPOSES a resolution.
It never decides: every output has requires_officer_review = True.
An LLM (e.g. local Llama via Ollama) can later be plugged in only to phrase
explanations; the decision logic stays deterministic and auditable.
"""
from app.integrations import digilocker_mock
from app.ml import fuzzy_service


def _result(issue, resolution, confidence, steps, action):
    return {
        "issue": issue,
        "proposed_resolution": resolution,
        "confidence": round(confidence, 2),
        "requires_officer_review": True,
        "recommended_action": action,
        "reasoning_steps": steps,
    }


def resolve_name_mismatch(app, details: dict, docs: list) -> dict:
    cmp = details.get("comparison", {})
    sim = cmp.get("similarity", 0)
    cert_name = cmp.get("name_b", "")
    steps = [f"RapidFuzz similarity between application name '{app.full_name}' and certificate name '{cert_name}' = {sim}"]
    corroborating = []
    for d in docs:
        n = (d.extracted_fields or {}).get("name")
        if not n or d.doc_type == details.get("doc_type"):
            continue
        c = fuzzy_service.compare_names(app.full_name, n)
        steps.append(f"Cross-checked {d.doc_type}: name '{n}' similarity {c['similarity']} ({c['interpretation']})")
        if c["interpretation"] == "MATCH":
            corroborating.append(d.doc_type)
    if cmp.get("initials_consistent"):
        steps.append("Token-level check: difference is only an abbreviated middle name / initial")
    if cmp.get("initials_consistent") and corroborating:
        conf = min(0.95, 0.75 + sim / 500 + 0.05 * len(corroborating))
        return _result("NAME_MISMATCH",
                       f"Treat as the same person: certificate uses an initial ('{cert_name}'), and {', '.join(corroborating)} "
                       f"carries the full name exactly. Accept with a note on file; no re-submission needed.",
                       conf, steps, "ACCEPT_WITH_NOTE")
    if sim >= 75 or corroborating:
        return _result("NAME_MISMATCH",
                       "Probable same person but evidence is partial. Request a self-declaration / affidavit of name variation.",
                       0.7, steps, "REQUEST_AFFIDAVIT")
    return _result("NAME_MISMATCH",
                   "Names differ substantially. Request re-issued certificate or gazette notification before any decision.",
                   0.85, steps, "REQUEST_CORRECTED_DOCUMENT")


def resolve_income_mismatch(app, details: dict, docs: list) -> dict:
    declared, cert = details.get("declared_income"), details.get("certificate_income")
    limit = details.get("income_limit")
    steps = [f"Declared income Rs {declared:,.0f} vs income certificate Rs {cert:,.0f}",
             f"Scheme income ceiling (YAML) = Rs {limit:,.0f}"]
    if cert <= limit and declared <= limit:
        steps.append("Both values are within the ceiling, so eligibility is unaffected")
        return _result("INCOME_MISMATCH",
                       f"Use the certificate value (Rs {cert:,.0f}) as authoritative and update the record. Eligibility unaffected.",
                       0.88, steps, "UPDATE_RECORD_FROM_CERTIFICATE")
    if cert > limit:
        steps.append("Certificate value exceeds the ceiling; declared value appears understated")
        return _result("INCOME_MISMATCH",
                       "Certificate income exceeds the scheme limit. Recommend rejection unless a newer valid certificate is produced.",
                       0.9, steps, "RECOMMEND_REJECT")
    steps.append("Declared value exceeds ceiling but certificate is within it")
    return _result("INCOME_MISMATCH",
                   "Declared income may be a data-entry error. Verify with issuing Tehsil office, then re-run scrutiny.",
                   0.72, steps, "VERIFY_WITH_ISSUER")


def resolve_missing_document(app, details: dict, docs: list) -> dict:
    doc_type = details.get("doc_type")
    steps = [f"Mandatory document {doc_type} not uploaded", f"Querying DigiLocker (mock) for applicant {app.applicant_id}"]
    found = digilocker_mock.has_document(app.applicant_id or "", doc_type)
    if found:
        steps.append(f"Found issuer-verified record: {found['uri']} from {found['issuer']}")
        return _result("MISSING_DOCUMENT",
                       f"Pull {doc_type} from DigiLocker (issuer-verified) instead of asking the student to re-upload.",
                       0.9, steps, "FETCH_FROM_DIGILOCKER")
    steps.append("Not available in DigiLocker")
    return _result("MISSING_DOCUMENT",
                   f"Send deficiency notice to applicant requesting {doc_type} within 15 days (NSP defect window).",
                   0.8, steps, "SEND_DEFICIENCY_NOTICE")


def resolve_possible_duplicate(app, details: dict, docs: list) -> dict:
    match = details.get("match", {})
    steps = [f"{details.get('doc_type')} has pHash Hamming distance {match.get('hamming_distance')} "
             f"to document #{match.get('document_id')} of application #{match.get('application_id')}"]
    if match.get("applicant_id") and match.get("applicant_id") == app.applicant_id:
        steps.append("Matched document belongs to the SAME applicant - likely a re-submission / renewal")
        return _result("POSSIBLE_DUPLICATE", "Same applicant's earlier document. Link applications; no fraud indicated.",
                       0.85, steps, "LINK_AS_RESUBMISSION")
    steps.append("Matched document belongs to a DIFFERENT applicant")
    steps.append("pHash similarity is evidence of a reused image, not proof of fraud")
    return _result("POSSIBLE_DUPLICATE",
                   "Hold both applications and verify the certificate number with the issuing authority before approval.",
                   0.78, steps, "HOLD_AND_VERIFY_WITH_ISSUER")


def resolve_anomaly(app, details: dict, docs: list) -> dict:
    devs = details.get("top_deviations", [])
    steps = [f"Isolation Forest score {details.get('anomaly_score')} (negative = unusual)"]
    steps += [f"{d['feature']}={d['value']:,.1f} is {d['z_score']:+} SD from typical applicants" for d in devs]
    return _result("ANOMALY",
                   "Unusual combination of values. Verify the highlighted fields against source documents; "
                   "anomaly alone is not a ground for rejection.",
                   0.65, steps, "MANUAL_VERIFICATION")


def resolve_rule_failure(app, details: dict, docs: list) -> dict:
    failed = details.get("failed_rules", [])
    steps = [f"Rule {r['rule']}: {r['reason']}" for r in failed]
    return _result("ELIGIBILITY_FAILURE",
                   "Deterministic scheme rules failed. Recommend rejection with the listed reasons unless the officer "
                   "finds the underlying data incorrect.", 0.95, steps, "RECOMMEND_REJECT")


HANDLERS = {
    "NAME_MISMATCH": resolve_name_mismatch,
    "INCOME_MISMATCH": resolve_income_mismatch,
    "MISSING_DOCUMENT": resolve_missing_document,
    "POSSIBLE_DUPLICATE": resolve_possible_duplicate,
    "ANOMALY": resolve_anomaly,
    "ELIGIBILITY_FAILURE": resolve_rule_failure,
}


def resolve(issue_type: str, app, details: dict, docs: list) -> dict:
    handler = HANDLERS.get(issue_type)
    if not handler:
        return _result(issue_type, "No automated playbook; route to officer.", 0.5, ["Unknown issue type"], "MANUAL_REVIEW")
    return handler(app, details, docs)

