import pytest

from trustgraph.continuity.detector import continuity_score

ACCT = "GB29 NWBK 6016 1331 9268 19"
KNOWN = {
    "payout_account": {ACCT: 540},
    "phone_number": {"+44 20 7946 0958": 800},
    "email_domain": {"acme-corp.co.uk": 900},
    "display_name": {"Jane Doe": 900},
}
SAME = {"payout_account": ACCT, "phone_number": "+44 20 7946 0958",
        "email_domain": "billing@acme-corp.co.uk", "display_name": "Jane Doe"}


def _score(known=None, **changes):
    return continuity_score({"identity": {**SAME, **changes}, "known_identity": KNOWN if known is None else known})


def test_unchanged_identity_scores_zero():
    signal = _score()
    assert signal.signal_name == "continuity"
    assert signal.score == 0.0
    assert signal.explanation == "Identity details match this contact's history"


@pytest.mark.parametrize("changes", [
    {"payout_account": "gb29nwbk60161331926819"},
    {"phone_number": "+44 (0)20 7946 0958"},
    {"phone_number": "020 7946 0958"},
    {"email_domain": "ACCOUNTS@Mail.Acme-Corp.co.uk"},
    {"display_name": "  jane   DOE "},
])
def test_formatting_differences_are_not_changes(changes):
    assert _score(**changes).score == 0.0


def test_new_payout_account_is_flagged_and_masked():
    signal = _score(payout_account="GB94BARC10201530093459")
    assert signal.score == pytest.approx(0.8)
    assert "payout account changed to …3459" in signal.explanation
    assert "BARC" not in signal.explanation


@pytest.mark.parametrize("domain", ["acme-c0rp.co.uk", "acmecorp.co.uk", "acme-corp.com", "acme-corp.co"])
def test_lookalike_domains_score_higher_than_new_ones(domain):
    lookalike = _score(email_domain=domain)
    unrelated = _score(email_domain="gmail.com")
    assert lookalike.score > unrelated.score
    assert "imitates known 'acme-corp.co.uk'" in lookalike.explanation


def test_nickname_is_weaker_than_a_different_name():
    assert _score(display_name="Janie Doe").score < _score(display_name="Robert Smith").score


def test_several_changes_compound():
    both = _score(payout_account="GB94BARC10201530093459", phone_number="+447700900123").score
    assert both == pytest.approx(1 - (1 - 0.8) * (1 - 0.5))


def test_recently_added_account_stays_suspicious_then_fades():
    recent = "GB12MIDL40051512345678"
    def age(days):
        return _score(known={**KNOWN, "payout_account": {ACCT: 540, recent: days}}, payout_account=recent).score
    assert age(6) == pytest.approx(0.8)
    assert 0 < age(40) < age(6)
    assert age(90) == 0.0


def test_no_history_means_no_evidence():
    assert continuity_score({"identity": SAME}).explanation == "No identity history to compare"
    assert continuity_score({}).score == 0.0


def test_malformed_input_does_not_crash():
    assert continuity_score({"identity": "oops", "known_identity": ["x"]}).score == 0.0
    assert continuity_score({"identity": SAME, "known_identity": {"payout_account": ACCT}}).score == 0.0
    bad_age = {**KNOWN, "payout_account": {ACCT: "long ago"}}
    assert _score(known=bad_age).score == 0.0
