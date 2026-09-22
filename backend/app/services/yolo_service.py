"""
yolo_service.py

Runs the fine-tuned YOLOv8 certificate detector locally.
No image ever leaves the server (no Roboflow or any other external API).

Class names are read from the model file itself, so the backend always
uses exactly the classes the model was trained with.
"""

import logging
import time
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

# Elements each document type is expected to carry.
# Missing elements are flagged for officer review; they never auto-reject.
EXPECTED_ELEMENTS = {
    "CASTE_CERTIFICATE": ["official_seal", "tehsildar_sign", "st_box"],
    "INCOME_CERTIFICATE": ["official_seal", "tehsildar_sign", "income_box"],
}


class YOLOService:
    def __init__(self, model_path=None):
        self.model_path = Path(model_path or settings.YOLO_MODEL_PATH)
        self.model = None
        self.load_error = None

    def _load(self):
        """Load the model on first use so the API starts even without it."""
        if self.model is not None or self.load_error is not None:
            return
        if not self.model_path.is_file():
            self.load_error = f"Model file not found: {self.model_path}"
            logger.warning(self.load_error)
            return
        try:
            from ultralytics import YOLO
            self.model = YOLO(str(self.model_path))
            logger.info("YOLO model loaded from %s, classes: %s",
                        self.model_path, list(self.model.names.values()))
        except Exception as exc:
            self.load_error = f"Failed to load model: {exc}"
            logger.error(self.load_error)

    @property
    def available(self):
        self._load()
        return self.model is not None

    def detect(self, image_path, confidence=None):
        """Detect certificate elements. Returns a plain dict for the API."""
        self._load()
        if self.model is None:
            return {"available": False, "error": self.load_error, "detections": []}

        start = time.perf_counter()
        results = self.model.predict(
            source=str(image_path),
            conf=confidence if confidence is not None else settings.YOLO_CONFIDENCE,
            iou=settings.YOLO_IOU,
            imgsz=settings.YOLO_IMGSZ,
            device=settings.YOLO_DEVICE,
            verbose=False,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        result = results[0]
        height, width = result.orig_shape
        detections = []
        for box in result.boxes:
            cls_id = int(box.cls[0])
            x1, y1, x2, y2 = (round(float(v), 1) for v in box.xyxy[0])
            detections.append({
                "class": self.model.names[cls_id],
                "confidence": round(float(box.conf[0]), 4),
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            })
        detections.sort(key=lambda d: d["confidence"], reverse=True)

        return {
            "available": True,
            "model_path": str(self.model_path),
            "image_size": {"width": width, "height": height},
            "num_detections": len(detections),
            "detections": detections,
            "processing_time_ms": round(elapsed_ms, 1),
        }

    @staticmethod
    def found_classes(detections, min_confidence=0.5):
        return sorted({d["class"] for d in detections if d["confidence"] >= min_confidence})

    def check_expected_elements(self, document_type, detections, min_confidence=0.5):
        """Compare detections with what this document type should contain."""
        expected = EXPECTED_ELEMENTS.get(document_type, [])
        found = self.found_classes(detections, min_confidence)
        missing = [c for c in expected if c not in found]
        return {"expected": expected, "found": found, "missing": missing}


yolo_service = YOLOService()
