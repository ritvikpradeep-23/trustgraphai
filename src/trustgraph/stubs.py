"""Stub for the signal this project hasn't built yet. It returns 0.0,
which under noisy-OR fusion means "no evidence", so it doesn't move the
fused score until the real signal lands. Replace it with its real
implementation; matching anomaly_score()'s signature is all fuse() needs."""
from trustgraph.signal import RiskSignal

_STUB_EXPLANATION = "stub: not implemented yet (no evidence)"


def precedent_score(interaction: dict) -> RiskSignal:
    return RiskSignal(signal_name="precedent", score=0.0, explanation=_STUB_EXPLANATION)
