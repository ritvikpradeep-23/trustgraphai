"""Stubs for the signals this project hasn't built yet. They return 0.0,
which under noisy-OR fusion means "no evidence", so they don't move the
fused score until real signals land. Replace each with its real
implementation; matching anomaly_score()'s signature is all fuse() needs."""
from trustgraph.signal import RiskSignal

_STUB_EXPLANATION = "stub: not implemented yet (no evidence)"


def similarity_score(interaction: dict) -> RiskSignal:
    return RiskSignal(signal_name="similarity", score=0.0, explanation=_STUB_EXPLANATION)


def precedent_score(interaction: dict) -> RiskSignal:
    return RiskSignal(signal_name="precedent", score=0.0, explanation=_STUB_EXPLANATION)
