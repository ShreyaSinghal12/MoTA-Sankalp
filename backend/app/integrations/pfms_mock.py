"""MOCK Public Financial Management System (PFMS) DBT payment adapter."""
from datetime import datetime, timezone

_counter = {"n": 10000}


def initiate_payment(sanction_number: str, amount: float, beneficiary: str, existing_count: int = 0) -> dict:
    _counter["n"] = max(_counter["n"], 10000 + existing_count) + 1
    return {
        "gateway": "PFMS_MOCK",
        "payment_reference": f"PFMS-DEMO-{_counter['n']}",
        "sanction_number": sanction_number,
        "beneficiary": beneficiary,
        "amount": amount,
        "mode": "DBT",
        "status": "PAID",
        "utr": f"UTR{int(datetime.now().timestamp())}",
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
