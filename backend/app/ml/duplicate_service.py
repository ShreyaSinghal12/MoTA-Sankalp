"""Perceptual-hash (pHash) near-duplicate detection. Flags for review; never auto-accuses fraud."""
import imagehash
from PIL import Image

from app.core.config import settings


def compute_phash(file_path: str) -> str | None:
    try:
        with Image.open(file_path) as img:
            return str(imagehash.phash(img.convert("L")))
    except Exception:
        return None


def hamming(h1: str, h2: str) -> int:
    return int(imagehash.hex_to_hash(h1) - imagehash.hex_to_hash(h2))


def find_matches(phash: str, candidates: list[dict], top_k: int = 3) -> dict:
    """candidates: [{document_id, application_id, doc_type, phash}]"""
    if not phash:
        return {"checked": 0, "nearest": [], "possible_duplicate": False}
    scored = []
    for c in candidates:
        if not c.get("phash"):
            continue
        d = hamming(phash, c["phash"])
        scored.append({**c, "hamming_distance": d, "similarity": round(1 - d / 64, 3)})
    scored.sort(key=lambda x: x["hamming_distance"])
    nearest = scored[:top_k]
    dup = [m for m in nearest if m["hamming_distance"] <= settings.PHASH_DUPLICATE_DISTANCE]
    return {
        "checked": len(scored),
        "threshold": settings.PHASH_DUPLICATE_DISTANCE,
        "nearest": nearest,
        "possible_duplicate": bool(dup),
        "note": "Near-identical image found - requires officer verification, not proof of fraud" if dup else "No near-duplicate",
    }
