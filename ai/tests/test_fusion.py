import pytest

from trustgraph.fusion import fuse, risk_band
from trustgraph.signal import RiskSignal

BANDS = {"caution": 0.5, "high": 0.7}


def _signals(continuity=0.0, similarity=0.0, precedent=0.0, anomaly=0.0):
    return [
        RiskSignal("continuity", continuity, "c"),
        RiskSignal("similarity", similarity, "s"),
        RiskSignal("precedent", precedent, "p"),
        RiskSignal("anomaly", anomaly, "anomaly reason"),
    ]


def test_zero_scores_leave_anomaly_score_unchanged():
    fused = fuse(_signals(anomaly=0.9))
    assert fused.score == pytest.approx(0.9)
    assert "driven by 'anomaly'" in fused.explanation
    assert "anomaly reason" in fused.explanation


def test_one_strong_signal_is_not_diluted_by_quiet_ones():
    fused = fuse(_signals(continuity=0.1, similarity=0.1, precedent=0.1, anomaly=0.9))
    assert fused.score >= 0.9


def test_agreement_compounds():
    fused = fuse(_signals(continuity=0.5, anomaly=0.5))
    assert fused.score == pytest.approx(0.75)


def test_no_evidence_means_zero():
    fused = fuse(_signals())
    assert fused.score == 0.0
    assert fused.explanation == "No signal raised concern"


def test_unknown_signal_name_is_rejected():
    with pytest.raises(KeyError):
        fuse([RiskSignal("anomly", 0.5, "typo")])


def test_risk_bands():
    assert risk_band(0.2, BANDS) == "Low"
    assert risk_band(0.5, BANDS) == "Caution"
    assert risk_band(0.95, BANDS) == "High"


def test_supporting_signals_are_listed_after_the_driver():
    fused = fuse(_signals(continuity=0.5, precedent=0.1, anomaly=0.9))
    assert fused.explanation.index("'anomaly'") < fused.explanation.index("Also 'continuity'")
    assert "precedent" not in fused.explanation
