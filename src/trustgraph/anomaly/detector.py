"""The anomaly signal as a component of TrustGraph's fusion layer."""
import math

import joblib
import numpy as np
import pandas as pd

from trustgraph.anomaly.features import RAW_FEATURES, circular_hour_distance, to_model_frame
from trustgraph.anomaly.train import MODEL_PATH
from trustgraph.signal import RiskSignal

Z_THRESHOLD = 2.0

# 0.5 is where decision_function crosses zero, i.e. the model's own
# contamination=0.05 boundary.
_MODEL_BOUNDARY = 0.5

# Features where only a high value is suspicious (a low amount or zero
# urgency keywords is not a red flag).
_ONE_SIDED = {"amount_ratio", "contact_freq_24h", "urgency_score", "new_channel_flag"}

_UNKNOWN_LABEL = {
    "duration_sec": "call duration",
    "hour_of_day": "time of day",
    "amount_ratio": "amount",
    "contact_freq_24h": "contact frequency",
    "urgency_score": "urgency",
    "new_channel_flag": "channel history",
}

_bundle = None


def _load_bundle():
    global _bundle
    if _bundle is None:
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def _is_missing(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def _normalize(decision_value: float, sigma: float) -> float:
    """Logistic squash of decision_function (0 == contamination boundary,
    negative == more anomalous), scaled by the training set's own spread."""
    return 1.0 / (1.0 + math.exp(decision_value / sigma))


def _z(feat: str, value: float, bundle: dict) -> float:
    if feat == "hour_of_day":
        return float(circular_hour_distance(value, bundle["hour_center"])) / bundle["hour_rms"]
    return (value - bundle["feature_mean"][feat]) / bundle["feature_std"][feat]


def _format_duration(seconds: float) -> str:
    return f"{seconds:.0f}s" if seconds < 120 else f"{seconds / 60:.0f} min"


def _describe(feat: str, value: float, z: float) -> str:
    if feat == "duration_sec":
        return f"unusually {'long' if z > 0 else 'short'} call ({_format_duration(value)})"
    if feat == "hour_of_day":
        return f"contact at {int(value):02d}:00, outside usual hours"
    if feat == "amount_ratio":
        return f"requested amount is {value:.1f}× this contact's usual"
    if feat == "contact_freq_24h":
        return f"contacted {int(value)} times in the last 24h"
    if feat == "urgency_score":
        return f"{int(value)} urgency keywords in the message"
    return "first contact from this device/channel"


def _explain(values: dict, missing: list[str], score: float, bundle: dict) -> str:
    unusual = []
    for feat in RAW_FEATURES:
        if feat in missing:
            continue
        z = _z(feat, values[feat], bundle)
        strength = z if feat in _ONE_SIDED else abs(z)
        if strength > Z_THRESHOLD:
            unusual.append((strength, _describe(feat, values[feat], z)))

    if unusual:
        unusual.sort(reverse=True)
        text = "Unusual: " + "; ".join(desc for _, desc in unusual)
    elif score >= _MODEL_BOUNDARY:
        text = "Unusual combination of individually normal values"
    else:
        text = "No unusual behavior"

    if missing:
        text += " (" + ", ".join(f"{_UNKNOWN_LABEL[f]} unknown" for f in missing) + ")"
    return text


def anomaly_score(interaction: dict) -> RiskSignal:
    bundle = _load_bundle()

    values, missing = {}, []
    for feat in RAW_FEATURES:
        value = interaction.get(feat)
        if _is_missing(value):
            missing.append(feat)
            value = bundle["feature_median"][feat]
        values[feat] = float(value)

    row = to_model_frame(pd.DataFrame([values]))
    decision_value = bundle["model"].decision_function(row)[0]
    score = float(np.clip(_normalize(decision_value, bundle["sigma"]), 0.0, 1.0))

    return RiskSignal(
        signal_name="anomaly",
        score=score,
        explanation=_explain(values, missing, score, bundle),
    )
