from fastapi import APIRouter
from app.api.v1.endpoints import health

router = APIRouter()

# Health check routes
router.include_router(health.router)

# Other endpoints will be added in later phases:
# router.include_router(auth.router, prefix="/auth")
# router.include_router(applications.router, prefix="/applications")
# router.include_router(documents.router, prefix="/documents")
# router.include_router(schemes.router, prefix="/schemes")
