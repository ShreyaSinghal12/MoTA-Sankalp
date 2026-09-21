from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.core.config import settings

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify API is running.
    
    Returns:
        HealthResponse with status and configuration info
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "database": "not_configured",
        "environment": {
            "debug": settings.DEBUG,
            "log_level": settings.LOG_LEVEL,
            "backend_host": settings.BACKEND_HOST,
            "backend_port": settings.BACKEND_PORT
        }
    }
