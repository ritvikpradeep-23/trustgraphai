import pytest

from trustgraph.precedent import detector
from trustgraph.precedent.detector import load_reports, precedent_score

REPORTS = [
    {"type": "phone", "value": "07700 900999", "reports": 9, "last_reported_days": 12, "category": "bank impersonation"},
    {"type": "account", "value": "GB82 WEST 1234 5698 7654 32", "reports": 1, "last_reported_days": 30, "category": "money mule account"},
    {"type": "domain", "value": "https://royalmail-redeliver.com/", "reports": 23, "last_reported_days": 3, "category": "parcel phishing"},
    {"type": "email", "value": "CEO.Office@gmail.com", "reports": 2, "last_reported_days": 45, "category": "CEO fraud"},
    {"type": "wallet", "value": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh", "reports": 6, "last_reported_days": 20, "category": "crypto investment scam"},
    {"type": "phone", "value": "+44 7700 900111", "reports": 1, "last_reported_days": 1100, "category": "tech support scam"},
]


@pytest.fixture(autouse=True)
def fixed_reports(monkeypatch):
    monkeypatch.setattr(detector, "_index", load_reports(REPORTS))


@pytest.mark.parametrize("interaction", [
    {"identity": {"phone_number": "+44 (0)7700 900 999"}},
    {"identity": {"phone_number": "447700900999"}},
    {"message_text": "Call me back on 07700-900-999 urgently"},
])
def test_reported_number_matches_in_any_format(interaction):
    signal = precedent_score(interaction)
    assert signal.signal_name == "precedent"
    assert signal.score > 0.95
    assert "…0999" in signal.explanation and "9 times" in signal.explanation


def test_identifiers_in_the_message_are_checked():
    text = ("Pay GB82WEST12345698765432, or use royalmail-redeliver.com/track?id=1, "
            "or BTC bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh, questions to ceo.office@gmail.com")
    signal = precedent_score({"message_text": text})
    for expected in ("account …5432", "'royalmail-redeliver.com'", "crypto wallet bc1qxy…", "'ceo.office@gmail.com'"):
        assert expected in signal.explanation
    assert "(in the message)" in signal.explanation


def test_more_reports_and_fresher_reports_score_higher():
    once = precedent_score({"message_text": "GB82 WEST 1234 5698 7654 32"}).score
    nine = precedent_score({"identity": {"phone_number": "07700900999"}}).score
    old = precedent_score({"identity": {"phone_number": "07700900111"}}).score
    assert once == pytest.approx(0.6)
    assert nine > once
    assert old == pytest.approx(0.3)
    assert "3 years ago" in precedent_score({"identity": {"phone_number": "07700900111"}}).explanation


def test_near_misses_and_ordinary_text_do_not_match():
    assert precedent_score({"identity": {"phone_number": "07700 900998"}}).score == 0.0
    assert precedent_score({"identity": {"email_domain": "billing@gmail.com"}}).score == 0.0
    ordinary = "Call me on 07911 123456 or see bbc.co.uk/news, invoice 2024-1187, total 4.50"
    signal = precedent_score({"message_text": ordinary})
    assert signal.score == 0.0
    assert signal.explanation == "No matching scam reports"


def test_duplicate_reports_merge():
    index = load_reports(REPORTS + [{"type": "phone", "value": "+447700900111", "reports": 2,
                                     "last_reported_days": 10, "category": "tech support scam"}])
    merged = index[("phone", "7700900111")]
    assert merged["reports"] == 3 and merged["last_reported_days"] == 10


def test_bad_input_is_no_evidence():
    for interaction in ({}, {"identity": "x", "message_text": 5}, {"identity": {"phone_number": None}}):
        assert precedent_score(interaction).score == 0.0
