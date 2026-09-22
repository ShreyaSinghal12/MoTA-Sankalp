from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/schemes", tags=["schemes"])

class SchemeResponse(BaseModel):
    id: str
    name: str
    description: str

@router.get("/", response_model=list)
async def list_schemes():
    return [
        {"id": "NFST", "name": "National Fellowship for ST", "description": "Domestic research fellowship"},
        {"id": "NOS", "name": "National Overseas Scholarship", "description": "International study support"}
    ]

@router.get("/{scheme_id}", response_model=SchemeResponse)
async def get_scheme(scheme_id: str):
    return {"id": scheme_id, "name": f"Scheme {scheme_id}", "description": "Scheme details"}

@router.post("/{scheme_id}/evaluate")
async def evaluate_scheme(scheme_id: str, application_data: dict):
    return {"overall_status": "ELIGIBLE", "score": 85.0}
