"""MOCK National Scholarship Portal adapter. Same method signatures a real NSP client would expose."""
import random
from datetime import datetime, timezone

FIRST = ["Sita", "Ramesh", "Lakshmi", "Budhan", "Phulmani", "Somra", "Jyoti", "Mangal", "Rupa", "Etwa"]
LAST = ["Toppo", "Kujur", "Soren", "Murmu", "Ekka", "Minz", "Tirkey", "Marandi", "Bhil", "Meena"]
STATES = ["Jharkhand", "Odisha", "Chhattisgarh", "Madhya Pradesh", "Rajasthan", "Gujarat"]


def fetch_new_applications(count: int = 2, scheme_id: str | None = None) -> list[dict]:
    rng = random.Random()
    out = []
    for _ in range(count):
        scheme = scheme_id or rng.choice(["NFST", "NOS"])
        out.append({
            "nsp_application_id": f"NSP-{datetime.now().year}-{rng.randint(100000, 999999)}",
            "full_name": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
            "gender": rng.choice(["F", "M"]),
            "category": "ST",
            "state": rng.choice(STATES),
            "age": rng.randint(22, 32),
            "scheme_id": scheme,
            "annual_income": float(rng.randrange(120000, 580000, 5000)),
            "marks_percentage": round(rng.uniform(58, 86), 1),
            "claimed_fee": float(rng.randrange(420000, 460000, 1000) if scheme == "NFST" else rng.randrange(1500000, 3200000, 10000)),
            "course": "Ph.D" if scheme == "NFST" else "MSc (Overseas)",
            "institution": "Central University (demo)" if scheme == "NFST" else "University Abroad (demo)",
        })
    return out


def push_status(records: list[dict]) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "gateway": "NSP_MOCK",
        "synced_at": now,
        "accepted": len(records),
        "results": [{**r, "nsp_ack": f"ACK-{abs(hash(r['application_number'])) % 10**8:08d}", "sync_status": "SYNCED"} for r in records],
    }
