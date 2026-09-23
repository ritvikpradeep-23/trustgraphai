"""Stage 5: combine every signal's RiskSignal into one TrustGraph score."""
from trustgraph.signal import RiskSignal

# Equal weighting until real signals justify tuning this.
DEFAULT_WEIGHTS = {
    "continuity": 0.25,
    "similarity": 0.25,
    "precedent": 0.25,
    "anomaly": 0.25,
}


def fuse(signals: list[RiskSignal], weights: dict[str, float] = None) -> RiskSignal:
    weights = weights or DEFAULT_WEIGHTS

    contributions = {s.signal_name: s.score * weights.get(s.signal_name, 0.0) for s in signals}
    combined_score = sum(contributions.values())

    driver = max(signals, key=lambda s: contributions[s.signal_name])
    explanation = (
        f"Combined score {combined_score:.2f}; driven by '{driver.signal_name}' "
        f"(score {driver.score:.2f}): {driver.explanation}"
    )

    return RiskSignal(
        signal_name="fused",
        score=combined_score,
        explanation=explanation,
    )
