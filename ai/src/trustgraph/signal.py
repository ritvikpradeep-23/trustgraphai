from dataclasses import dataclass


@dataclass
class RiskSignal:
    signal_name: str  # e.g. "anomaly"
    score: float  # 0.0 (normal) to 1.0 (very anomalous)
    explanation: str  # human-readable reason, for the judge-facing UI
