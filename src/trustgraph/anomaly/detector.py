"""The anomaly signal as a component of TrustGraph's fusion layer."""
import math

import joblib
import numpy as np
import pandas as pd

from trustgraph.anomaly.features import RAW_FEATURES, circular_hour_distance, to_model_frame
from trustgraph.anomaly.train import MODEL_PATH
from trustgraph.signal import RiskSignal

Z_THRESHOLD = 2.0

# IsolationForest misses single-feature extremes (9x the usual amount isolates
# as fast as 2x) and several mildly-off features at once. So the per-feature
# z-scores are combined as a root-sum-square and set a minimum score:
# 0.5 at evidence 2.5, ~0.73 at 3.5, ~0.88 at 4.5, still rising past that.
EVIDENCE_START = 2.5
EVIDENCE_SCALE = 1.0
# A new channel alone is common (~5% of legit traffic) and its binary z is
# ~4.2, so it may add to other evidence but not dominate it.
_NEW_CHANNEL_CAP = 2.0

# 0.5 is where decision_function crosses zero, i.e. the model's own
# contamination=0.05 boundary.
_MODEL_BOUNDARY = 0.5

# Features where only a high value is suspicious (a low amount or zero
# urgency keywords is not a red flag).
_ONE_SIDED = {"amount_ratio", "contact_freq_24h", "urgency_score", "new_channel_flag"}

_LABEL = {
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


def _parse(feat: str, value) -> tuple[float | None, str | None]:
    """(usable value, None) or (None, "unknown" | "invalid")."""
    if value is None:
        return None, "unknown"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None, "invalid"
    if math.isnan(v):
        return None, "unknown"
    if feat == "hour_of_day":
        ok = 0 <= v < 24
    elif feat == "new_channel_flag":
        ok = v in (0.0, 1.0)
    else:
        ok = math.isfinite(v) and v >= 0
    return (v, None) if ok else (None, "invalid")


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


def _format_ratio(ratio: float) -> str:
    return f"{ratio:.1f}×" if ratio < 100 else f"{ratio:,.0f}×"


def _describe(feat: str, value: float, z: float) -> str:
    if feat == "duration_sec":
        return f"unusually {'long' if z > 0 else 'short'} call ({_format_duration(value)})"
    if feat == "hour_of_day":
        return f"contact at {int(value):02d}:00, outside usual hours"
    if feat == "amount_ratio":
        return f"requested amount is {_format_ratio(value)} this contact's usual"
    if feat == "contact_freq_24h":
        return f"contacted {int(value)} times in the last 24h"
    if feat == "urgency_score":
        return f"{int(value)} urgency keywords in the message"
    return "first contact from this device/channel"


def _strengths(values: dict, bundle: dict) -> dict[str, tuple[float, float]]:
    """feature -> (how unusual, signed z), for features the caller supplied."""
    out = {}
    for feat, value in values.items():
        z = _z(feat, value, bundle)
        out[feat] = (z if feat in _ONE_SIDED else abs(z), z)
    return out


def _evidence_floor(strengths: dict[str, tuple[float, float]]) -> float:
    total = 0.0
    for feat, (strength, _) in strengths.items():
        s = max(strength, 0.0)
        if feat == "new_channel_flag":
            s = min(s, _NEW_CHANNEL_CAP)
        total += s * s
    evidence = math.sqrt(total)
    if evidence <= EVIDENCE_START:
        return 0.0
    return 1.0 / (1.0 + math.exp(-(evidence - EVIDENCE_START) / EVIDENCE_SCALE))


def _explain(values: dict, unresolved: dict[str, str], strengths: dict, score: float) -> str:
    unusual = [
        (strength, _describe(feat, values[feat], z))
        for feat, (strength, z) in strengths.items()
        if strength > Z_THRESHOLD
    ]

    if unusual:
        unusual.sort(reverse=True)
        text = "Unusual: " + "; ".join(desc for _, desc in unusual)
    elif score >= _MODEL_BOUNDARY:
        text = "Unusual combination of individually normal values"
    elif len(unresolved) * 2 >= len(RAW_FEATURES):
        text = "Insufficient data to assess"
    else:
        text = "No unusual behavior"

    if unresolved:
        text += " (" + ", ".join(f"{_LABEL[f]} {why}" for f, why in unresolved.items()) + ")"
    return text


def anomaly_score(interaction: dict) -> RiskSignal:
    bundle = _load_bundle()

    values, unresolved = {}, {}
    for feat in RAW_FEATURES:
        value, problem = _parse(feat, interaction.get(feat))
        if problem:
            unresolved[feat] = problem
        else:
            values[feat] = value

    # Unknown or invalid features get the training median: no evidence either way.
    model_input = {f: values.get(f, bundle["feature_median"][f]) for f in RAW_FEATURES}
    decision_value = bundle["model"].decision_function(to_model_frame(pd.DataFrame([model_input])))[0]

    strengths = _strengths(values, bundle)
    score = max(_normalize(decision_value, bundle["sigma"]), _evidence_floor(strengths))
    score = float(np.clip(score, 0.0, 1.0))

    return RiskSignal(
        signal_name="anomaly",
        score=score,
        explanation=_explain(values, unresolved, strengths, score),
    )
