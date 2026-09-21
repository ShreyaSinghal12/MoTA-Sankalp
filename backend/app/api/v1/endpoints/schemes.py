from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.rule_engine import rule_engine
from app.schemas.scheme import SchemeConfigSchema, SchemeEvaluationSchema
from typing import List

router = APIRouter(tags=["schemes"])

@router.get("/schemes", response_model=List[SchemeConfigSchema])
async def list_schemes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    schemes = []
    for scheme_id, config in rule_engine.configs.items():
        schemes.append({
            "scheme_id": config.get("scheme_id"),
            "scheme_name": config.get("scheme_name"),
            "description": config.get("description"),
            "version": config.get("version"),
            "eligibility_rules": config.get("eligibility_rules", []),
            "required_documents": config.get("required_documents", []),
            "fraud_checks": config.get("fraud_checks", []),
            "allocation": config.get("allocation", {})
        })
    return schemes

@router.get("/schemes/{scheme_id}", response_model=SchemeConfigSchema)
async def get_scheme(
    scheme_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    config = rule_engine.get_scheme_config(scheme_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Scheme {scheme_id} not found")
    
    return {
        "scheme_id": config.get("scheme_id"),
        "scheme_name": config.get("scheme_name"),
        "description": config.get("description"),
        "version": config.get("version"),
        "eligibility_rules": config.get("eligibility_rules", []),
        "required_documents": config.get("required_documents", []),
        "fraud_checks": config.get("fraud_checks", []),
        "allocation": config.get("allocation", {})
    }

@router.post("/schemes/{scheme_id}/evaluate", response_model=SchemeEvaluationSchema)
async def evaluate_applicant(
    scheme_id: str,
    applicant_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        evaluation = rule_engine.evaluate_eligibility(scheme_id, applicant_data)
        return {
            "scheme_id": evaluation.scheme_id,
            "scheme_name": evaluation.scheme_name,
            "applicant_id": evaluation.applicant_id,
            "overall_status": evaluation.overall_status,
            "overall_score": evaluation.overall_score,
            "rules_passed": evaluation.rules_passed,
            "rules_total": evaluation.rules_total,
            "rule_results": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "passed": r.passed,
                    "weight": r.weight,
                    "description": r.description,
                    "reason": r.reason
                }
                for r in evaluation.rule_results
            ],
            "missing_documents": evaluation.missing_documents,
            "fraud_flags": evaluation.fraud_flags,
            "timestamp": evaluation.timestamp
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))