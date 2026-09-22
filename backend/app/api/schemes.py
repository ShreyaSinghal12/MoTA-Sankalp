from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.schemas.schemas import EvaluateRequest
from app.services import rule_engine

router = APIRouter(prefix="/schemes", tags=["schemes"], dependencies=[Depends(get_current_user)])


@router.get("")
def list_schemes():
    return [{"scheme_id": k, "name": v["name"], "level": v.get("level"), "demo_values": v.get("demo_values", True)}
            for k, v in rule_engine.load_schemes().items()]


@router.get("/{scheme_id}")
def get_scheme(scheme_id: str):
    try:
        return rule_engine.get_scheme(scheme_id)
    except KeyError as e:
        raise HTTPException(404, str(e))


@router.post("/{scheme_id}/evaluate")
def evaluate(scheme_id: str, body: EvaluateRequest):
    try:
        return rule_engine.evaluate(scheme_id, body.model_dump())
    except KeyError as e:
        raise HTTPException(404, str(e))
