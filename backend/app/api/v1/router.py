from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, schemes

router = APIRouter()

router.include_router(health.router)
router.include_router(auth.router, prefix="/auth")
router.include_router(schemes.router)