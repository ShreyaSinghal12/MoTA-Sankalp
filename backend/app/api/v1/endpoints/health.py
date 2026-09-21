from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.health import HealthResponse
from app.core.config import settings
from app.db.session import get_db

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    database_status = "not_configured"
    
    try:
        db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception as e:
        database_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "version": "0.1.0",
        "database": database_status,
        "environment": {
            "debug": settings.DEBUG,
            "log_level": settings.LOG_LEVEL,
            "backend_host": settings.BACKEND_HOST,
            "backend_port": settings.BACKEND_PORT
        }
    }