from fastapi import APIRouter
from app.api.v1.endpoints import auth, applications, documents, schemes

router = APIRouter()
router.include_router(auth.router)
router.include_router(applications.router)
router.include_router(documents.router)
router.include_router(schemes.router)
