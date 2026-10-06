import joblib
import numpy as np
import pytest

from trustgraph import pipeline
from trustgraph.classifier import detector
from trustgraph.classifier import model as clf
from trustgraph.textnorm import normalize

SCAMS = ["Buy gift cards now and send me the codes", "Send the gift card codes to me quickly",
         "Please buy steam gift cards and text me the codes", "I need gift cards for a client, send codes",
         "Pay the release fee at the link to get your prize", "Your prize is waiting, pay the fee today"]
HONEST = ["See you at dinner tonight", "Your parcel arrives tomorrow morning", "Thanks for the lovely evening",
          "Meeting moved to 3pm, see you there", "Happy birthday, have a great day", "Running late, start without me"]


@pytest.fixture
def tiny_model(tmp_path, monkeypatch):
    y = np.array([1] * len(SCAMS) + [0] * len(HONEST))
    idx = np.arange(len(y))
    folds = [(idx[idx % 2 == 0], idx[idx % 2 == 1]), (idx[idx % 2 == 1], idx[idx % 2 == 0])]
    bundle = clf.fit(SCAMS + HONEST, y, c=1.0, folds=folds)
    path = tmp_path / "classifier.joblib"
    joblib.dump(bundle, path)
    monkeypatch.setenv("TRUSTGRAPH_CLASSIFIER_MODEL", str(path))
    monkeypatch.setattr(detector, "_bundle", None)
    return bundle


def test_normalization_undoes_tricks_and_marks_details_the_same_for_both_labels():
    assert normalize("upd4te your acc0unt at https://secure-pay.example.com/x1") == "update your account at zzlink"
    assert normalize("u r g e n t, call [PHONE]") == "urgent, call zzphone"
    assert normalize("Pay Rs. 1,500 now") == normalize("pay £20 now") == "pay zzamount now"
    # A scam-style and an honest-style link become the same marker.
    assert normalize("x verify1.test/pay") == normalize("x https://app.example.com/orders/abc") == "x zzlink"


def test_flag_off_keeps_the_four_signals(monkeypatch):
    monkeypatch.delenv("TRUSTGRAPH_CLASSIFIER", raising=False)
    signals, _ = pipeline.score_interaction({"message_text": "hello"})
    assert [s.signal_name for s in signals] == ["continuity", "similarity", "precedent", "anomaly"]


def test_flag_on_appends_classifier_last(tiny_model, monkeypatch):
    monkeypatch.setenv("TRUSTGRAPH_CLASSIFIER", "1")
    signals, fused = pipeline.score_interaction({"message_text": "buy gift cards and send the codes"})
    assert [s.signal_name for s in signals][-1] == "classifier"
    assert len(signals) == 5 and 0.0 <= fused.score <= 1.0


def test_classifier_scores_and_explains(tiny_model):
    scam = detector.classifier_score({"message_text": "Buy gift cards and send me the codes today"})
    honest = detector.classifier_score({"message_text": "See you at dinner, running late"})
    assert 0.0 <= honest.score < scam.score <= 1.0
    if scam.score >= 0.5:
        assert "wording like labeled scams" in scam.explanation and "'" in scam.explanation


def test_missing_text_or_model_is_no_evidence(monkeypatch, tmp_path):
    assert detector.classifier_score({}).score == 0.0
    monkeypatch.setenv("TRUSTGRAPH_CLASSIFIER_MODEL", str(tmp_path / "missing.joblib"))
    monkeypatch.setattr(detector, "_bundle", None)
    s = detector.classifier_score({"message_text": "hi"})
    assert s.score == 0.0 and "not installed" in s.explanation


def test_removed_words_are_dropped_before_features():
    assert clf.prepare("Dear user, pay now. Regards", removed=("dear", "user", "regards")) == ", pay now."
