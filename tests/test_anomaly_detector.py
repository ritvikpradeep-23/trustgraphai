from trustgraph.anomaly.detector import anomaly_score
from trustgraph.signal import RiskSignal

NORMAL_INTERACTION = {
    "duration_sec": 90, "hour_of_day": 14, "amount_ratio": 1.0,
    "contact_freq_24h": 1, "urgency_score": 0, "new_channel_flag": 0,
}
ANOMALOUS_INTERACTION = {
    "duration_sec": 30, "hour_of_day": 3, "amount_ratio": 8.5,
    "contact_freq_24h": 25, "urgency_score": 7, "new_channel_flag": 1,
}
# Single mild push: amount_ratio somewhat elevated, everything else normal.
BORDERLINE_AMOUNT = {
    "duration_sec": 100, "hour_of_day": 13, "amount_ratio": 2.2,
    "contact_freq_24h": 1, "urgency_score": 0, "new_channel_flag": 0,
}
# Single mild push: an unseen channel, everything else normal.
BORDERLINE_NEW_CHANNEL = {
    "duration_sec": 80, "hour_of_day": 15, "amount_ratio": 1.0,
    "contact_freq_24h": 1, "urgency_score": 0, "new_channel_flag": 1,
}


def _check_shape(signal: RiskSignal):
    assert signal.signal_name == "anomaly"
    assert 0.0 <= signal.score <= 1.0
    assert isinstance(signal.explanation, str) and signal.explanation


def test_clearly_normal_interaction_scores_low():
    signal = anomaly_score(NORMAL_INTERACTION)
    _check_shape(signal)
    assert signal.score < 0.3


def test_clearly_anomalous_interaction_scores_high():
    signal = anomaly_score(ANOMALOUS_INTERACTION)
    _check_shape(signal)
    assert signal.score > 0.7


def test_borderline_amount_ratio_scores_in_middle_band():
    signal = anomaly_score(BORDERLINE_AMOUNT)
    _check_shape(signal)
    assert 0.15 <= signal.score <= 0.65
    assert "amount_ratio" in signal.explanation


def test_borderline_new_channel_scores_in_middle_band():
    signal = anomaly_score(BORDERLINE_NEW_CHANNEL)
    _check_shape(signal)
    assert 0.15 <= signal.score <= 0.65
    assert "new_channel_flag" in signal.explanation
