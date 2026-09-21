import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

@dataclass
class EvaluationResult:
    rule_id: str
    rule_name: str
    passed: bool
    weight: int
    description: str
    reason: str

@dataclass
class SchemeEvaluation:
    scheme_id: str
    scheme_name: str
    applicant_id: int
    overall_status: str
    overall_score: float
    rules_passed: int
    rules_total: int
    rule_results: List[EvaluationResult]
    missing_documents: List[str]
    fraud_flags: List[Dict[str, Any]]
    timestamp: str

class RuleEngine:
    def __init__(self):
        self.configs = {}
        self.load_all_schemes()
    
    def load_all_schemes(self):
        configs_path = Path(__file__).parent.parent.parent / "configs" / "schemes"
        for yaml_file in configs_path.glob("*.yaml"):
            with open(yaml_file, 'r') as f:
                config = yaml.safe_load(f)
                scheme_id = config.get("scheme_id")
                self.configs[scheme_id] = config
    
    def get_scheme_config(self, scheme_id: str) -> Dict[str, Any]:
        return self.configs.get(scheme_id)
    
    def evaluate_eligibility(self, scheme_id: str, applicant_data: Dict[str, Any]) -> SchemeEvaluation:
        config = self.get_scheme_config(scheme_id)
        if not config:
            raise ValueError(f"Scheme {scheme_id} not found")
        
        rule_results = []
        total_weight = 0
        passed_weight = 0
        
        for rule in config.get("eligibility_rules", []):
            rule_id = rule.get("rule_id")
            rule_name = rule.get("name")
            weight = rule.get("weight", 1)
            condition = rule.get("condition")
            description = rule.get("description")
            
            total_weight += weight
            
            try:
                passed = self._evaluate_condition(condition, applicant_data)
                if passed:
                    passed_weight += weight
                    reason = "Condition satisfied"
                else:
                    reason = "Condition not satisfied"
            except Exception as e:
                passed = False
                reason = f"Error evaluating: {str(e)}"
            
            result = EvaluationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                passed=passed,
                weight=weight,
                description=description,
                reason=reason
            )
            rule_results.append(result)
        
        overall_score = (passed_weight / total_weight * 100) if total_weight > 0 else 0
        
        missing_docs = self._check_missing_documents(config, applicant_data)
        
        fraud_flags = self._run_fraud_checks(config, applicant_data)
        
        if overall_score >= 80 and len(missing_docs) == 0 and len(fraud_flags) == 0:
            overall_status = "ELIGIBLE"
        elif overall_score >= 60 and len(missing_docs) == 0:
            overall_status = "NEEDS_REVIEW"
        else:
            overall_status = "INELIGIBLE"
        
        from datetime import datetime
        evaluation = SchemeEvaluation(
            scheme_id=scheme_id,
            scheme_name=config.get("scheme_name"),
            applicant_id=applicant_data.get("id"),
            overall_status=overall_status,
            overall_score=round(overall_score, 2),
            rules_passed=sum(1 for r in rule_results if r.passed),
            rules_total=len(rule_results),
            rule_results=rule_results,
            missing_documents=missing_docs,
            fraud_flags=fraud_flags,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return evaluation
    
    def _evaluate_condition(self, condition: str, applicant_data: Dict[str, Any]) -> bool:
        safe_dict = {
            "applicant": type('obj', (object,), applicant_data)
        }
        result = eval(condition, {"__builtins__": {}}, safe_dict)
        return bool(result)
    
    def _check_missing_documents(self, config: Dict[str, Any], applicant_data: Dict[str, Any]) -> List[str]:
        required_docs = config.get("required_documents", [])
        provided_docs = applicant_data.get("documents", [])
        provided_doc_types = [doc.get("type") if isinstance(doc, dict) else doc for doc in provided_docs]
        
        missing = []
        for doc_req in required_docs:
            if doc_req.get("mandatory"):
                doc_type = doc_req.get("doc_type")
                if doc_type not in provided_doc_types:
                    missing.append(doc_type)
        
        return missing
    
    def _run_fraud_checks(self, config: Dict[str, Any], applicant_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        fraud_checks = config.get("fraud_checks", [])
        flags = []
        
        for check in fraud_checks:
            check_id = check.get("check_id")
            check_name = check.get("name")
            severity = check.get("severity")
            description = check.get("description")
            
            if check_id == "F001":
                if applicant_data.get("duplicate_application_detected"):
                    flags.append({
                        "check_id": check_id,
                        "name": check_name,
                        "severity": severity,
                        "description": description,
                        "flagged": True
                    })
            
            elif check_id == "F101":
                if applicant_data.get("duplicate_application_detected"):
                    flags.append({
                        "check_id": check_id,
                        "name": check_name,
                        "severity": severity,
                        "description": description,
                        "flagged": True
                    })
            
            elif check_id == "F002" or check_id == "F102":
                if applicant_data.get("document_forgery_detected"):
                    flags.append({
                        "check_id": check_id,
                        "name": check_name,
                        "severity": severity,
                        "description": description,
                        "flagged": True
                    })
        
        return flags

rule_engine = RuleEngine()