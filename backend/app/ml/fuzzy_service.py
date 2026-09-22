"""RapidFuzz name comparison with Indian-name normalisation."""
import re

from rapidfuzz import fuzz

from app.core.config import settings

HONORIFICS = {"mr", "mrs", "ms", "miss", "shri", "smt", "dr", "sri", "km"}


def normalize(name: str) -> str:
    n = (name or "").lower()
    n = re.sub(r"[^a-z\s]", " ", n)
    tokens = [t for t in n.split() if t not in HONORIFICS]
    return " ".join(tokens)


def _initials_consistent(a: str, b: str) -> bool:
    """True if every single-letter token in one name is the initial of a token in the other,
    and all full tokens match (e.g. 'anjali k munda' vs 'anjali kumari munda')."""
    ta, tb = a.split(), b.split()
    if not ta or not tb or len(ta) != len(tb):
        return False
    for x, y in zip(ta, tb):
        if x == y:
            continue
        if len(x) == 1 and y.startswith(x):
            continue
        if len(y) == 1 and x.startswith(y):
            continue
        return False
    return True


def compare_names(name_a: str, name_b: str) -> dict:
    a, b = normalize(name_a), normalize(name_b)
    scores = {
        "ratio": round(fuzz.ratio(a, b), 2),
        "token_sort_ratio": round(fuzz.token_sort_ratio(a, b), 2),
        "token_set_ratio": round(fuzz.token_set_ratio(a, b), 2),
        "partial_ratio": round(fuzz.partial_ratio(a, b), 2),
    }
    similarity = round(max(scores["token_sort_ratio"], (scores["token_set_ratio"] + scores["ratio"]) / 2), 2)
    initials = _initials_consistent(a, b)
    if similarity >= settings.NAME_MATCH_THRESHOLD:
        interpretation = "MATCH"
    elif similarity >= settings.NAME_PROBABLE_THRESHOLD or initials:
        interpretation = "PROBABLE_MATCH_REVIEW"
    else:
        interpretation = "MISMATCH"
    return {
        "name_a": name_a, "name_b": name_b,
        "normalized_a": a, "normalized_b": b,
        "similarity": similarity, "scores": scores,
        "initials_consistent": initials,
        "interpretation": interpretation,
    }
