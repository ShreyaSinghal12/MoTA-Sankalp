"""MOCK DigiLocker adapter returning synthetic, 'issuer-verified' document metadata."""
import hashlib

ISSUED = {
    "ST_CERTIFICATE": "Revenue Department (demo)",
    "INCOME_CERTIFICATE": "Tehsil Office (demo)",
    "MARKSHEET": "University Examination Board (demo)",
    "ADMISSION_LETTER": "Foreign University via MEA (demo)",
}


def fetch_documents(applicant_id: str) -> dict:
    h = int(hashlib.sha256(applicant_id.encode()).hexdigest(), 16)
    docs = []
    for i, (doc_type, issuer) in enumerate(ISSUED.items()):
        # deterministic: some applicants lack some docs in DigiLocker
        available = doc_type != "ADMISSION_LETTER" or (h % 3 != 0)
        if not available:
            continue
        docs.append({
            "doc_type": doc_type,
            "issuer": issuer,
            "uri": f"in.gov.digilocker.demo/{applicant_id}/{doc_type.lower()}",
            "verified": True,
            "issued_on": f"20{22 + (h >> i) % 3}-0{1 + (h >> (i + 3)) % 9}-15",
        })
    return {"gateway": "DIGILOCKER_MOCK", "applicant_id": applicant_id, "documents": docs}


def has_document(applicant_id: str, doc_type: str) -> dict | None:
    return next((d for d in fetch_documents(applicant_id)["documents"] if d["doc_type"] == doc_type), None)
