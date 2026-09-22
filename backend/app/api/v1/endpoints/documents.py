import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.services.fraud_detection_service import fraud_detection_service
from app.services.ocr_service import ocr_service
from app.services.yolo_service import yolo_service

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_BYTES = 5 * 1024 * 1024

# Words the OCR text of each document type should normally contain
EXPECTED_KEYWORDS = {
    "CASTE_CERTIFICATE": ["caste", "tribe", "tehsildar"],
    "INCOME_CERTIFICATE": ["income", "annual", "tehsildar"],
    "MARK_SHEET": ["marks", "examination"],
}


def save_upload(application_id, file, content):
    """Store the file under a random name to avoid collisions and path tricks."""
    ext = Path(file.filename or "").suffix.lower()
    folder = Path(settings.UPLOAD_DIR) / f"app_{application_id}"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4().hex}{ext}"
    path.write_bytes(content)
    return path


@router.post("/analyze")
async def analyze_document(
    application_id: int = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Only {sorted(ALLOWED_EXTENSIONS)} images are supported")
    content = await file.read()
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail="File larger than 5 MB")

    image_path = save_upload(application_id, file, content)

    # 1. Visual elements (seal, signature, boxes, QR) from the YOLO model
    detection = yolo_service.detect(image_path)
    elements = yolo_service.check_expected_elements(document_type, detection["detections"])

    # 2. Text from OCR
    text, ocr_confidence = ocr_service.extract_text(str(image_path))
    detected_type, type_score = ocr_service.detect_document_type(text)
    keyword_check = fraud_detection_service.detect_document_tampering(
        text, EXPECTED_KEYWORDS.get(document_type, [])
    )

    # 3. Flags for the officer. The system recommends; the officer decides.
    flags = []
    if not detection["available"]:
        flags.append("Detector model not loaded - visual checks were not performed")
    for element in elements["missing"]:
        flags.append(f"Expected element not detected: {element}")
    if EXPECTED_KEYWORDS.get(document_type) and keyword_check["is_suspicious"]:
        flags.append("Expected keywords missing from OCR text")
    if detected_type not in ("UNKNOWN", document_type):
        flags.append(f"Declared type {document_type} but text looks like {detected_type}")

    return {
        "application_id": application_id,
        "declared_document_type": document_type,
        "stored_file": image_path.name,
        "yolo_detection": detection,
        "expected_elements": elements,
        "ocr": {
            "text": text,
            "confidence": round(float(ocr_confidence), 4),
            "detected_document_type": detected_type,
            "type_match_score": round(float(type_score), 4),
        },
        "keyword_check": keyword_check,
        "flags": flags,
        "recommendation": "NEEDS_REVIEW" if flags else "NO_ISSUES_FOUND",
    }
