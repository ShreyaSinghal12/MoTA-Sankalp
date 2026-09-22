from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/applications", tags=["applications"])

class ApplicationResponse(BaseModel):
    id: int
    applicant_id: int
    scheme_id: str
    status: str

@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(app_id: int):
    return {"id": app_id, "applicant_id": 1, "scheme_id": "NFST", "status": "UNDER_SCRUTINY"}

@router.post("/{app_id}/evaluate")
async def evaluate_application(app_id: int):
    return {"status": "ELIGIBLE", "score": 95.5, "missing_documents": []}

@router.post("/{app_id}/documents")
async def upload_document(app_id: int, file: UploadFile = File(...)):
    return {"file_name": file.filename, "size": len(await file.read())}
