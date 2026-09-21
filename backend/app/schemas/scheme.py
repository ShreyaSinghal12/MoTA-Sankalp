from pydantic import BaseModel
from typing import List, Dict, Any

class EvaluationResultSchema(BaseModel):
    rule_id: str
    rule_name: str
    passed: bool
    weight: int
    description: str
    reason: str

class SchemeEvaluationSchema(BaseModel):
    scheme_id: str
    scheme_name: str
    applicant_id: int
    overall_status: str
    overall_score: float
    rules_passed: int
    rules_total: int
    rule_results: List[EvaluationResultSchema]
    missing_documents: List[str]
    fraud_flags: List[Dict[str, Any]]
    timestamp: str

class SchemeConfigSchema(BaseModel):
    scheme_id: str
    scheme_name: str
    description: str
    version: str
    eligibility_rules: List[Dict[str, Any]]
    required_documents: List[Dict[str, Any]]
    fraud_checks: List[Dict[str, Any]]
    allocation: Dict[str, Any]