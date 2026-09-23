"""Stage 5: fixed-neutral stubs for the signals this project hasn't built
yet, so the fusion checkpoint can be exercised with all 4 slots filled.
Replace each with its real implementation as it lands - matching
anomaly_score()'s signature is what plugs it into fuse() with no other
changes."""
from trustgraph.signal import RiskSignal


def continuity_score(interaction: dict) -> RiskSignal:
    return RiskSignal(signal_name="continuity", score=0.5, explanation="stub: not implemented yet")


def similarity_score(interaction: dict) -> RiskSignal:
    return RiskSignal(signal_name="similarity", score=0.5, explanation="stub: not implemented yet")


def precedent_score(interaction: dict) -> RiskSignal:
    return RiskSignal(signal_name="precedent", score=0.5, explanation="stub: not implemented yet")
