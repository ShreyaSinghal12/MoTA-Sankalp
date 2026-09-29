import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # backend/


class Settings:
    APP_NAME = "MoTA-SANKALP"
    APP_FULL_NAME = "Scheme Administration, Network & Knowledge Automated Lifecycle Platform"
    VERSION = "1.0.0-mvp"
    API_PREFIX = "/api/v1"

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + (BASE_DIR / "mota_sankalp.db").as_posix()
    )

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me-mota-sankalp-secret")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480")
    )

    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
    GENERATED_DIR = Path(os.getenv("GENERATED_DIR", str(BASE_DIR / "generated")))
    SCHEME_DIR = BASE_DIR / "configs" / "schemes"
    MODEL_DIR = Path(os.getenv("MODEL_DIR", str(BASE_DIR / "models")))

    YOLO_CONFIDENCE = 0.25
    YOLO_IOU = 0.45
    YOLO_IMGSZ = 640
    YOLO_DEVICE = "cpu"

    OCR_ENGINE = os.getenv("OCR_ENGINE", "auto")

    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}
    MAX_UPLOAD_BYTES = 5 * 1024 * 1024

    NAME_MATCH_THRESHOLD = 90.0
    NAME_PROBABLE_THRESHOLD = 75.0
    PHASH_DUPLICATE_DISTANCE = 4
    INCOME_TOLERANCE = 0.10

    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]

    @property
    def DETECTOR_MODEL_PATH(self) -> Path:
        return self.MODEL_DIR / "document_detector.pt"

settings = Settings()
for _p in (settings.UPLOAD_DIR, settings.GENERATED_DIR, settings.GENERATED_DIR / "sanctions",
           settings.GENERATED_DIR / "sample_docs", settings.MODEL_DIR):
    _p.mkdir(parents=True, exist_ok=True)
