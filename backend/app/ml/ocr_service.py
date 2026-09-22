"""OCR service.

Engine order:
  1. EasyOCR (English + Hindi) when installed (pip install -r requirements-ml.txt)
  2. DEMO FALLBACK: reads the text layer embedded in synthetic demo certificates
     (PNG tEXt chunk 'ocr_text'). This keeps the pipeline end-to-end runnable
     on machines without torch. Output shape is identical in both modes.
"""
from pathlib import Path

from PIL import Image

from app.core.config import settings

_reader = None
_easyocr_available = None


def easyocr_available() -> bool:
    global _easyocr_available
    if _easyocr_available is None:
        try:
            import easyocr  # noqa: F401
            _easyocr_available = True
        except Exception:
            _easyocr_available = False
    return _easyocr_available


def _get_reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["en", "hi"], gpu=False, verbose=False)
    return _reader


def _easyocr_extract(path: Path) -> dict:
    results = _get_reader().readtext(str(path), detail=1, paragraph=False)
    # sort top-to-bottom, left-to-right so lines keep reading order
    results.sort(key=lambda r: (round(r[0][0][1] / 15), r[0][0][0]))
    lines, confs = [], []
    for _box, text, conf in results:
        lines.append(text)
        confs.append(float(conf))
    return {
        "raw_text": "\n".join(lines),
        "confidence": round(sum(confs) / len(confs), 3) if confs else 0.0,
        "engine": "easyocr",
    }


def _fallback_extract(path: Path) -> dict:
    if path.suffix.lower() == ".pdf":
        return {"raw_text": "", "confidence": 0.0, "engine": "demo_fallback",
                "note": "PDF OCR requires EasyOCR + pdf rasterisation; upload PNG/JPG for demo"}
    try:
        with Image.open(path) as img:
            text = img.info.get("ocr_text", "")
    except Exception as exc:
        return {"raw_text": "", "confidence": 0.0, "engine": "demo_fallback", "note": f"unreadable image: {exc}"}
    if text:
        return {"raw_text": text, "confidence": 0.9, "engine": "demo_fallback_embedded_text"}
    sidecar = path.with_suffix(".txt")
    if sidecar.exists():
        return {"raw_text": sidecar.read_text(encoding="utf-8"), "confidence": 0.85, "engine": "demo_fallback_sidecar"}
    return {"raw_text": "", "confidence": 0.0, "engine": "demo_fallback",
            "note": "No text layer found. Install EasyOCR for real OCR on arbitrary scans."}


def extract_text(file_path: str) -> dict:
    path = Path(file_path)
    mode = settings.OCR_ENGINE.lower()
    if mode in ("auto", "easyocr") and easyocr_available() and path.suffix.lower() != ".pdf":
        try:
            out = _easyocr_extract(path)
            if out["raw_text"].strip():
                return out
        except Exception as exc:  # never block the pipeline on OCR failure
            fb = _fallback_extract(path)
            fb["note"] = f"EasyOCR failed ({exc}); used fallback"
            return fb
    return _fallback_extract(path)
