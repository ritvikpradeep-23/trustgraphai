import math

from trustgraph.anomaly.detector import anomaly_score
from trustgraph.anomaly.features import circular_hour_distance
from trustgraph.signal import RiskSignal

NORMAL_INTERACTION = {
    "duration_sec": 90, "hour_of_day": 14, "amount_ratio": 1.0,
    "contact_freq_24h": 1, "urgency_score": 0, "new_channel_flag": 0,
}
ANOMALOUS_INTERACTION = {
    "duration_sec": 30, "hour_of_day": 3, "amount_ratio": 8.5,
    "contact_freq_24h": 25, "urgency_score": 7, "new_channel_flag": 1,
}
# Single mild push: amount_ratio just past the normal range, below the floor.
BORDERLINE_AMOUNT = {**NORMAL_INTERACTION, "duration_sec": 100, "hour_of_day": 13, "amount_ratio": 1.4}
# Single mild push: an unseen channel, everything else normal.
BORDERLINE_NEW_CHANNEL = {**NORMAL_INTERACTION, "duration_sec": 80, "hour_of_day": 15, "new_channel_flag": 1}


def _check_shape(signal: RiskSignal):
    assert signal.signal_name == "anomaly"
    assert 0.0 <= signal.score <= 1.0
    assert isinstance(signal.explanation, str) and signal.explanation


def test_clearly_normal_interaction_scores_low_and_says_so():
    signal = anomaly_score(NORMAL_INTERACTION)
    _check_shape(signal)
    assert signal.score < 0.3
    assert signal.explanation == "No unusual behavior"


def test_clearly_anomalous_interaction_scores_high():
    signal = anomaly_score(ANOMALOUS_INTERACTION)
    _check_shape(signal)
    assert signal.score > 0.7
    assert "8.5× this contact's usual" in signal.explanation
    assert "03:00" in signal.explanation


def test_borderline_amount_ratio_scores_between_normal_and_anomalous():
    signal = anomaly_score(BORDERLINE_AMOUNT)
    _check_shape(signal)
    assert 0.1 <= signal.score <= 0.6
    assert "1.4× this contact's usual" in signal.explanation


def test_borderline_new_channel_scores_between_normal_and_anomalous():
    signal = anomaly_score(BORDERLINE_NEW_CHANNEL)
    _check_shape(signal)
    assert 0.1 <= signal.score <= 0.6
    assert "first contact from this device/channel" in signal.explanation


def test_score_keeps_rising_past_the_training_range():
    scores = [anomaly_score({**BORDERLINE_AMOUNT, "amount_ratio": a}).score for a in (1.4, 1.6, 2.2, 9.0)]
    assert scores == sorted(scores)
    assert scores[1] >= 0.5
    assert scores[-1] >= 0.9


def test_new_channel_alone_is_not_floored():
    assert anomaly_score(BORDERLINE_NEW_CHANNEL).score < 0.5


def test_missing_feature_is_imputed_and_reported():
    interaction = {k: v for k, v in NORMAL_INTERACTION.items() if k != "amount_ratio"}
    signal = anomaly_score(interaction)
    _check_shape(signal)
    assert signal.score < 0.3
    assert "amount unknown" in signal.explanation

    nan_signal = anomaly_score({**NORMAL_INTERACTION, "amount_ratio": math.nan})
    assert nan_signal.score == signal.score


def test_hour_wraps_around_midnight():
    assert circular_hour_distance(23, 1) == 2
    late = anomaly_score({**NORMAL_INTERACTION, "hour_of_day": 23})
    midnight = anomaly_score({**NORMAL_INTERACTION, "hour_of_day": 0})
    assert abs(late.score - midnight.score) < 0.1
