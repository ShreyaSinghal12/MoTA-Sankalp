from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import applications, auth, dashboard, integrations, officers, schemes, scrutiny
from app.core.config import settings
from app.db.database import SessionLocal, init_db
from app.db.seed import seed
from app.ml import anomaly_service, detector_service, ocr_service


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    seed()
    if not anomaly_service.MODEL_PATH.exists():
        anomaly_service.train()
    yield


app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description=settings.APP_FULL_NAME + " - Ministry of Tribal Affairs scholarship administration (SIH MVP)",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
def root():
    return {"name": settings.APP_NAME, "full_name": settings.APP_FULL_NAME, "version": settings.VERSION,
            "docs": "/docs", "redoc": "/redoc", "health": f"{settings.API_PREFIX}/health"}


@app.get(f"{settings.API_PREFIX}/health", tags=["health"])
def health():
    db_status = "connected"
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {exc}"
    return {
        "status": "ok",
        "database": db_status,
        "database_engine": settings.DATABASE_URL.split(":")[0],
        "ocr_engine": "easyocr" if (settings.OCR_ENGINE != "fallback" and ocr_service.easyocr_available()) else "demo_fallback",
        "detector_model_present": settings.DETECTOR_MODEL_PATH.exists(),
        "anomaly_model_present": anomaly_service.MODEL_PATH.exists(),
        "detector_classes": detector_service.CLASSES,
    }


for r in (auth.router, dashboard.router, schemes.router, applications.router, scrutiny.router,
          officers.router, integrations.router):
    app.include_router(r, prefix=settings.API_PREFIX)
