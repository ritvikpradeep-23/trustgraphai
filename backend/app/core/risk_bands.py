"""Risk levels from a 0-1 score, one rule everywhere: High from 0.65,
Caution from 0.25, Low below. Same cut points as the browser extension
(trustgraph_extension/shared/constants.js TG.HIGH_THRESHOLD / TG.FLAG_THRESHOLD)."""
HIGH = 0.65
CAUTION = 0.25


def band(score: float) -> str:
    if score >= HIGH:
        return "High"
    if score >= CAUTION:
        return "Caution"
    return "Low"
