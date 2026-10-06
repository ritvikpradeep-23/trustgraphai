"""Regression checks for the original-model bridge and safe fallback."""
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from app.ai import scam_engine
from app.api import detect as detection_api
from app.schemas.detection import DetectionRequest


def test_bridge_does_not_invent_history(monkeypatch):
    captured = {}
    def score(interaction):
        captured.update(interaction)
        return [SimpleNamespace(signal_name="anomaly", score=.12)], SimpleNamespace(score=.76, explanation="Observed signals")
    monkeypatch.setattr(scam_engine, "engine", lambda: (score, lambda _: "Caution"))
    answer = scam_engine.analyze("Please act immediately", sender="example")
    assert answer["score"] == .76 and answer["level"] == "CAUTION"
    assert captured == {"message_text": "Please act immediately", "urgency_score": 1, "sender": "example"}
    assert "not a calibrated fraud probability" in answer["reasons"][1]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -.1, 1.1])
def test_bad_model_scores_are_unavailable(monkeypatch, value):
    monkeypatch.setattr(scam_engine, "engine", lambda: (lambda _: ([], SimpleNamespace(score=value)), lambda _: "High"))
    assert scam_engine.analyze("Test") is None


def test_detection_preserves_real_model_score_and_signals(monkeypatch):
    monkeypatch.setattr(detection_api, "find_previous_report_matches", lambda *a, **kw: [])
    monkeypatch.setattr(detection_api, "scam_analyze", lambda *a: {
        "score": .764, "level": "CAUTION", "signals": {"anomaly": .11, "continuity": .2, "similarity": .7, "precedent": 0}, "reasons": ["Test model"]})
    answer = detection_api.detect(DetectionRequest(channel="other", text="Test"), Mock())
    assert answer.risk_score == .764 and answer.risk_level == "CAUTION"
    assert answer.model_available and answer.score_kind == "review-score"
    assert answer.signals.anomaly == .11


def test_unavailable_model_is_not_a_safe_zero(monkeypatch):
    monkeypatch.setattr(detection_api, "find_previous_report_matches", lambda *a, **kw: [])
    monkeypatch.setattr(detection_api, "scam_analyze", lambda *a: None)
    answer = detection_api.detect(DetectionRequest(channel="other", text="Test"), Mock())
    assert answer.risk_score is None and answer.risk_level == "UNKNOWN"
    assert not answer.model_available


def test_compatibility_extension_scorer_does_not_hardcode_high(monkeypatch):
    from app.api import extension_score
    from app.schemas.detection import DetectionSignals
    monkeypatch.setattr(extension_score, "detect", lambda *a: SimpleNamespace(
        risk_score=.76, risk_level="CAUTION", reasons=["Signals"], method="original-scam-engine+database-pattern-matching",
        signals=DetectionSignals(anomaly=.1, continuity=0, similarity=.7, precedent=0)))
    answer = extension_score.score(extension_score.ScoreRequest(message_text="Test"), Mock())
    assert answer["band"] == "Caution" and answer["score"] == .76
    assert {s["name"] for s in answer["signals"]} == {"anomaly", "continuity", "similarity", "precedent"}
