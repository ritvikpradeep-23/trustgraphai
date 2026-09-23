"""Stage 4: the anomaly signal as a component of TrustGraph's fusion layer."""
import math

import joblib
import numpy as np
import pandas as pd

from trustgraph.anomaly.train import MODEL_PATH
from trustgraph.signal import RiskSignal

_bundle = None


def _load_bundle():
    global _bundle
    if _bundle is None:
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def _normalize(decision_value: float, sigma: float) -> float:
    """Map decision_function's threshold-centered score (0 == the training
    contamination boundary, negative == more anomalous) to 0-1 via a
    logistic squash scaled by the training set's own spread."""
    return 1.0 / (1.0 + math.exp(decision_value / sigma))


def _top_extreme_features(interaction: dict, bundle: dict, k: int = 2) -> list[str]:
    z_scores = {}
    for feat in bundle["features"]:
        mean = bundle["feature_mean"][feat]
        std = bundle["feature_std"][feat]
        z_scores[feat] = abs((interaction[feat] - mean) / std)
    ranked = sorted(z_scores, key=z_scores.get, reverse=True)
    return ranked[:k]


def anomaly_score(interaction: dict) -> RiskSignal:
    bundle = _load_bundle()
    model = bundle["model"]
    features = bundle["features"]

    row = pd.DataFrame([{feat: interaction[feat] for feat in features}])
    decision_value = model.decision_function(row)[0]
    score = _normalize(decision_value, bundle["sigma"])

    top_features = _top_extreme_features(interaction, bundle)
    explanation = (
        f"Most extreme feature(s): {', '.join(top_features)} "
        f"(anomaly score {score:.2f})"
    )

    return RiskSignal(
        signal_name="anomaly",
        score=float(np.clip(score, 0.0, 1.0)),
        explanation=explanation,
    )
