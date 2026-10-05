"""Combine every signal's RiskSignal into one TrustGraph score."""
import json
import math

from trustgraph.paths import model_path
from trustgraph.signal import RiskSignal

# Noisy-OR weight = how much we trust a signal (1.0 = take its score at face
# value). Every signal must be listed: an unknown signal_name is a bug.
DEFAULT_WEIGHTS = {
    "continuity": 1.0,
    "similarity": 1.0,
    "precedent": 1.0,
    "anomaly": 1.0,
    # Fifth signal, only present when TRUSTGRAPH_CLASSIFIER=1. The pipeline
    # replaces this with the weight chosen on dev and saved in the model file.
    "classifier": 0.5,
}

BANDS_PATH = "models/risk_bands.json"

# Secondary signals at or above this score are listed after the driver, so the
# UI shows every reason that contributed (a nickname at 0.1 isn't worth it).
SUPPORTING_MIN = 0.3

_bands = None


def fuse(signals: list[RiskSignal], weights: dict[str, float] = None) -> RiskSignal:
    """Noisy-OR: treat each signal as an independent chance the interaction is
    risky, so one strong signal raises the score and agreement compounds."""
    weights = weights or DEFAULT_WEIGHTS

    contributions = {s.signal_name: weights[s.signal_name] * s.score for s in signals}
    combined_score = 1.0 - math.prod(1.0 - c for c in contributions.values())

    driver = max(signals, key=lambda s: contributions[s.signal_name])
    if contributions[driver.signal_name] == 0:
        explanation = "No signal raised concern"
    else:
        explanation = (
            f"Combined score {combined_score:.2f}; driven by '{driver.signal_name}' "
            f"(score {driver.score:.2f}): {driver.explanation}"
        )
        also = sorted(
            (s for s in signals if s is not driver and contributions[s.signal_name] >= SUPPORTING_MIN),
            key=lambda s: contributions[s.signal_name], reverse=True,
        )
        for s in also:
            explanation += f". Also '{s.signal_name}' (score {s.score:.2f}): {s.explanation}"

    return RiskSignal(signal_name="fused", score=combined_score, explanation=explanation)


def risk_band(score: float, bands: dict = None) -> str:
    """Low / Caution / High, with cut points calibrated on held-out normal
    traffic by evaluate.py (Caution 10% of calibration traffic, High 1%)."""
    global _bands
    if bands is None:
        if _bands is None:
            with open(model_path("risk_bands.json")) as f:  # TRUSTGRAPH_MODEL_DIR or models/
                _bands = json.load(f)
        bands = _bands
    if score >= bands["high"]:
        return "High"
    if score >= bands["caution"]:
        return "Caution"
    return "Low"
