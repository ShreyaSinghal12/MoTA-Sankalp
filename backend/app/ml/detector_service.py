"""Document visual detector.

REAL_MODEL    : backend/models/document_detector.pt (YOLOv8n fine-tuned on real data via training/yolo/)
                is loaded when present and ultralytics is installed.
DEMO_FALLBACK : lightweight colour/structure heuristics (red seal ink, blue signature ink,
                dense black/white QR block) + OCR keywords for text fields.

Text-field classes (income_field / st_certificate_field) have no public training data, so if the
model does not find them (e.g. base-stage model, before you fine-tune on your own annotated
certificates) those two classes alone fall back to OCR keywords.
Every detection carries "source" so the UI and judges can see where each result came from.
"""
from pathlib import Path

import numpy as np
from PIL import Image

from app.core.config import settings

CLASSES = ["official_seal", "signature", "qr_code", "income_field", "st_certificate_field"]

# class names used by other training runs -> canonical names
ALIASES = {
    "official_seal": "official_seal", "seal": "official_seal", "stamp": "official_seal",
    "signature": "signature", "tehsildar_sign": "signature", "sign": "signature",
    "qr_code": "qr_code", "qr": "qr_code",
    "income_field": "income_field", "income_box": "income_field",
    "st_certificate_field": "st_certificate_field", "st_box": "st_certificate_field", "st_field": "st_certificate_field",
}

_model = None
_model_error = None
_model_classes: set = set()


def _load_model():
    global _model, _model_error, _model_classes
    if _model is not None or _model_error is not None:
        return _model
    path = settings.DETECTOR_MODEL_PATH
    if not path.exists():
        _model_error = "model file not found"
        return None
    try:
        from ultralytics import YOLO
        _model = YOLO(str(path))
        _model_classes = {ALIASES[n.lower()] for n in _model.names.values() if n.lower() in ALIASES}
    except Exception as exc:
        _model_error = f"could not load model: {exc}"
    return _model


def _empty(source: str):
    return {c: {"detected": False, "confidence": 0.0, "box": None, "source": source} for c in CLASSES}


def _real_detect(model, path: Path) -> dict:
    out = _empty("yolo")
    res = model.predict(str(path), conf=0.25, imgsz=960, verbose=False)[0]
    names = res.names
    for box in res.boxes:
        cls_name = ALIASES.get(str(names[int(box.cls)]).lower())
        if not cls_name:
            continue
        conf = float(box.conf)
        if conf > out[cls_name]["confidence"]:
            out[cls_name] = {"detected": True, "confidence": round(conf, 3),
                             "box": [round(float(x), 1) for x in box.xyxy[0].tolist()], "source": "yolo"}
    return out


def _bbox(mask: np.ndarray):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def _text_fields(ocr_text: str) -> dict:
    t = (ocr_text or "").lower()
    out = {}
    out["income_field"] = {"detected": "income" in t, "confidence": 0.88 if "income" in t else 0.0,
                           "box": None, "source": "ocr_keywords"}
    st = "scheduled tribe" in t or "st certificate" in t or "category: st" in t
    out["st_certificate_field"] = {"detected": st, "confidence": 0.9 if st else 0.0, "box": None, "source": "ocr_keywords"}
    return out


def _heuristic_detect(path: Path, ocr_text: str) -> dict:
    out = _empty("heuristic")
    with Image.open(path) as img:
        arr = np.asarray(img.convert("RGB")).astype(np.int16)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    total = arr.shape[0] * arr.shape[1]

    red = (r > 150) & (g < 90) & (b < 90)
    red_ratio = float(red.sum() / total)
    if red_ratio > 0.002:
        out["official_seal"].update(detected=True, confidence=round(min(0.97, 0.7 + red_ratio * 40), 3), box=_bbox(red))
    else:
        out["official_seal"]["confidence"] = round(red_ratio * 100, 3)

    blue = (b > 120) & (r < 80) & (g < 110)
    blue_ratio = float(blue.sum() / total)
    if blue_ratio > 0.0008:
        out["signature"].update(detected=True, confidence=round(min(0.95, 0.68 + blue_ratio * 60), 3), box=_bbox(blue))
    else:
        out["signature"]["confidence"] = round(blue_ratio * 100, 3)

    gray = arr.mean(axis=2)
    black = gray < 60
    h, w = black.shape
    best, best_box = 0.0, None
    win = max(40, min(h, w) // 10)
    step = max(10, win // 4)
    for y in range(0, h - win, step):
        for x in range(0, w - win, step):
            patch = black[y:y + win, x:x + win]
            frac = float(patch.mean())
            if 0.3 < frac < 0.7:
                transitions = float(np.abs(np.diff(patch.astype(np.int8), axis=1)).mean())
                score = transitions * (1 - abs(frac - 0.5))
                if score > best:
                    best, best_box = score, [int(x), int(y), int(x + win), int(y + win)]
    if best > 0.03:
        out["qr_code"].update(detected=True, confidence=round(min(0.95, 0.6 + best), 3), box=best_box)
    else:
        out["qr_code"]["confidence"] = round(best, 3)

    out.update(_text_fields(ocr_text))
    return out


def detect(file_path: str, ocr_text: str = "") -> dict:
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        return {"mode": "SKIPPED", "reason": "visual detection runs on images only", "detections": _empty("none")}
    model = _load_model()
    if model is not None:
        try:
            dets = _real_detect(model, path)
            fields = _text_fields(ocr_text)
            missing = [c for c in ("income_field", "st_certificate_field") if not dets[c]["detected"]]
            for c in missing:
                dets[c] = fields[c]
            return {"mode": "REAL_MODEL", "model_path": str(settings.DETECTOR_MODEL_PATH),
                    "model_classes": sorted(_model_classes), "ocr_fallback_classes": missing, "detections": dets}
        except Exception as exc:
            return {"mode": "DEMO_FALLBACK", "reason": f"model inference failed: {exc}",
                    "detections": _heuristic_detect(path, ocr_text)}
    return {"mode": "DEMO_FALLBACK", "reason": _model_error or "no model", "detections": _heuristic_detect(path, ocr_text)}
