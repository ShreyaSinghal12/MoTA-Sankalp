"""Generic YAML-driven eligibility evaluator. Policy lives in configs/schemes/*.yaml."""
from functools import lru_cache
from pathlib import Path

import yaml

from app.core.config import settings

OPS = {
    "eq": (lambda a, v: a == v, "== {v}"),
    "ne": (lambda a, v: a != v, "!= {v}"),
    "lt": (lambda a, v: a < v, "< {v}"),
    "lte": (lambda a, v: a <= v, "<= {v}"),
    "gt": (lambda a, v: a > v, "> {v}"),
    "gte": (lambda a, v: a >= v, ">= {v}"),
    "in": (lambda a, v: a in v, "in {v}"),
    "between": (lambda a, v: v[0] <= a <= v[1], "between {v[0]} and {v[1]}"),
}


@lru_cache(maxsize=None)
def load_schemes() -> dict:
    schemes = {}
    for path in sorted(Path(settings.SCHEME_DIR).glob("*.yaml")):
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        schemes[cfg["scheme_id"].upper()] = cfg
    return schemes


def get_scheme(scheme_id: str) -> dict:
    scheme = load_schemes().get(scheme_id.upper())
    if not scheme:
        raise KeyError(f"Unknown scheme: {scheme_id}")
    return scheme


def evaluate(scheme_id: str, data: dict) -> dict:
    scheme = get_scheme(scheme_id)
    results = []
    for rule in scheme.get("eligibility_rules", []):
        field, op, value = rule["field"], rule["operator"], rule["value"]
        fn, tmpl = OPS[op]
        expected = tmpl.format(v=value)
        actual = data.get(field)
        if actual is None:
            passed, reason = False, f"'{field}' not provided"
        else:
            try:
                passed = bool(fn(actual, value))
            except TypeError:
                passed = False
            reason = (f"{field}={actual} satisfies {expected}" if passed
                      else f"{field}={actual} violates {expected}")
        results.append({
            "rule": rule["id"], "description": rule.get("description", ""), "field": field,
            "actual_value": actual, "expected": expected,
            "result": "PASS" if passed else "FAIL", "reason": reason,
        })

    missing_docs = []
    if data.get("documents") is not None:
        have = {d.upper() for d in data["documents"]}
        missing_docs = [d for d in scheme.get("mandatory_documents", []) if d not in have]

    eligible = all(r["result"] == "PASS" for r in results)
    return {
        "scheme_id": scheme["scheme_id"],
        "scheme_name": scheme["name"],
        "demo_values": scheme.get("demo_values", True),
        "eligible": eligible,
        "rules": results,
        "missing_documents": missing_docs,
        "rank_score": rank_score(scheme, data),
    }


def rank_score(scheme: dict, data: dict) -> float:
    """Merit score 0-100 using YAML weights (marks high, income low, PVTG / female boost)."""
    w = scheme.get("ranking_weights", {})
    limit = next((r["value"] for r in scheme["eligibility_rules"] if r["id"] == "INCOME_LIMIT"), 600000)
    marks = float(data.get("marks_percentage") or 0)
    income = float(data.get("annual_income") or 0)
    income_component = max(0.0, 1 - income / limit) * 100 if limit else 0
    pvtg = 100.0 if (data.get("is_pvtg") and scheme.get("pvtg_priority")) else 0.0
    score = w.get("marks", 0) * marks + w.get("income", 0) * income_component + w.get("pvtg", 0) * pvtg
    return round(score, 2)


def sanction_amount(scheme_id: str, claimed_fee: float) -> float:
    s = get_scheme(scheme_id).get("sanction", {})
    if s.get("mode") == "claimed_fee_capped":
        return float(min(claimed_fee or 0, s.get("cap", 0)))
    return float(s.get("amount", 0))
