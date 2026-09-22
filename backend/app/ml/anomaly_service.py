"""Isolation Forest anomaly detection trained on synthetic 'normal' scholarship records."""
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from app.core.config import settings

FEATURES = ["annual_income", "marks_percentage", "age", "claimed_fee"]
MODEL_PATH = settings.GENERATED_DIR / "isolation_forest.joblib"
_bundle = None


def _synthetic_normal(n: int = 1500, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    income = np.clip(rng.normal(280000, 110000, n), 40000, 600000)
    marks = np.clip(rng.normal(68, 8, n), 50, 92)
    age = np.clip(rng.normal(26, 3.5, n), 20, 35)
    # half fellowship-style (~4.4L), half overseas-style (15-35L) claims
    fellowship = rng.normal(440000, 30000, n)
    overseas = rng.normal(2500000, 500000, n)
    claimed = np.where(rng.random(n) < 0.5, fellowship, overseas)
    return np.column_stack([income, marks, age, claimed])


def train(save: bool = True) -> dict:
    X = _synthetic_normal()
    mu, sd = X.mean(axis=0), X.std(axis=0)
    model = IsolationForest(n_estimators=200, contamination=0.03, random_state=42)
    model.fit((X - mu) / sd)
    bundle = {"model": model, "mean": mu, "std": sd, "features": FEATURES}
    if save:
        joblib.dump(bundle, MODEL_PATH)
    return bundle


def _get():
    global _bundle
    if _bundle is None:
        _bundle = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else train()
    return _bundle


def score(record: dict) -> dict:
    b = _get()
    x = np.array([[float(record.get(f) or 0) for f in FEATURES]])
    z = (x - b["mean"]) / b["std"]
    pred = int(b["model"].predict(z)[0])
    s = float(b["model"].decision_function(z)[0])
    contributions = sorted(
        [{"feature": f, "value": float(x[0][i]), "z_score": round(float(z[0][i]), 2)} for i, f in enumerate(FEATURES)],
        key=lambda c: -abs(c["z_score"]),
    )
    return {
        "label": "NEEDS_REVIEW" if pred == -1 else "NORMAL",
        "anomaly_score": round(s, 4),
        "note": "negative score = more anomalous",
        "top_deviations": contributions[:3],
        "model": "IsolationForest(n_estimators=200, synthetic normal data)",
    }
