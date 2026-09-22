"""Document storage, field extraction and per-document AI processing."""
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.ml import detector_service, duplicate_service, ocr_service

DOC_TYPES = {"ST_CERTIFICATE", "INCOME_CERTIFICATE", "MARKSHEET", "ADMISSION_LETTER", "ID_PROOF", "OTHER"}
CONTENT_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".pdf": "application/pdf"}


async def save_upload(application_id: int, doc_type: str, file: UploadFile) -> dict:
    doc_type = (doc_type or "OTHER").upper()
    if doc_type not in DOC_TYPES:
        raise HTTPException(400, f"doc_type must be one of {sorted(DOC_TYPES)}")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type {ext or '?'} not allowed. Allowed: {sorted(settings.ALLOWED_EXTENSIONS)}")
    data = await file.read()
    if len(data) == 0:
        raise HTTPException(400, "Empty file")
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(400, "File exceeds 5 MB limit")
    folder = settings.UPLOAD_DIR / str(application_id)
    folder.mkdir(parents=True, exist_ok=True)
    safe_name = f"{doc_type.lower()}_{uuid.uuid4().hex[:8]}{ext}"
    path = folder / safe_name
    path.write_bytes(data)
    return {"doc_type": doc_type, "filename": file.filename, "file_path": str(path),
            "content_type": CONTENT_TYPES.get(ext, "application/octet-stream"), "size_bytes": len(data)}


def _num(s: str) -> float | None:
    s = re.sub(r"[^\d.]", "", s or "")
    try:
        return float(s) if s else None
    except ValueError:
        return None


def extract_fields(text: str) -> dict:
    t = text or ""
    fields = {}
    m = re.search(r"(?:name(?: of (?:applicant|candidate|student))?|naam)\s*[:\-]\s*([A-Za-z .]+)", t, re.I)
    if m:
        fields["name"] = re.sub(r"\s+", " ", m.group(1)).strip(" .")
    m = re.search(r"annual\s+(?:family\s+)?income[^\d\n]*([\d,]+(?:\.\d+)?)", t, re.I)
    if m:
        fields["annual_income"] = _num(m.group(1))
    m = re.search(r"(?:certificate|cert\.?|serial|roll)\s*(?:no\.?|number)\s*[:\-]?\s*([A-Z0-9/\-]+)", t, re.I)
    if m:
        fields["certificate_number"] = m.group(1).strip()
    m = re.search(r"category\s*[:\-]\s*([A-Za-z ()]+)", t, re.I)
    if m:
        fields["category"] = m.group(1).strip()
    elif re.search(r"scheduled\s+tribe", t, re.I):
        fields["category"] = "ST"
    m = re.search(r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b", t)
    if m:
        fields["date"] = m.group(1)
    m = re.search(r"(?:percentage|aggregate|marks)\s*[:\-]?\s*(\d{1,3}(?:\.\d+)?)\s*%?", t, re.I)
    if m:
        fields["marks_percentage"] = _num(m.group(1))
    return fields


def process_document(doc, other_docs: list[dict]) -> dict:
    """Runs OCR -> field extraction -> visual detection -> pHash on one Document row (mutates it)."""
    ocr = ocr_service.extract_text(doc.file_path)
    fields = extract_fields(ocr["raw_text"])
    detection = detector_service.detect(doc.file_path, ocr["raw_text"])
    phash = duplicate_service.compute_phash(doc.file_path) if not doc.file_path.lower().endswith(".pdf") else None
    # compare only against documents that already existed before this one (earlier submissions)
    earlier = [o for o in other_docs if o["document_id"] < doc.id]
    dup = duplicate_service.find_matches(phash, earlier) if phash else {"checked": 0, "nearest": [], "possible_duplicate": False}

    doc.ocr_text = ocr["raw_text"]
    doc.ocr_confidence = ocr["confidence"]
    doc.ocr_engine = ocr["engine"]
    doc.extracted_fields = fields
    doc.detection = detection
    doc.phash = phash
    doc.processed = True
    return {"document_id": doc.id, "doc_type": doc.doc_type, "ocr": ocr, "fields": fields,
            "detection": detection, "phash": phash, "duplicate_check": dup}
