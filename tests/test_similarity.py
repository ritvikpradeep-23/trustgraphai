import pytest

from trustgraph.similarity.detector import MATCH_CAP, similarity_score


def _score(text):
    return similarity_score({"message_text": text})


@pytest.mark.parametrize("text, reason", [
    ("I'm with the anti-fraud unit of your bank, we need to shift your savings to a protected account now.",
     "asks to move money to a 'safe' account"),
    ("hey r u free? grab some steam cards for a client and send me pics of the codes",
     "asks for gift-card codes"),
    ("Don't worry, it's just a security check, read me the code we just sent to your phone",
     "asks for a one-time code, PIN or password"),
    ("Your PC is infected, please download AnyDesk so our engineer can fix it",
     "asks for remote access to a device"),
    ("Our banking details have been updated, please pay the invoice to our new account.",
     "says the bank details have changed"),
    ("You owe unpaid tax and a warrant is out for your arrest, pay now.",
     "threatens arrest or legal action"),
    ("I hacked your phone camera. Pay 900 in BTC or I'll leak the video to your colleagues.",
     "threatens to share private videos or photos"),
    ("You've got the remote role! Please transfer the 120 onboarding fee so we can set up your laptop.",
     "asks you to pay to get or start a job"),
])
def test_scam_asks_in_new_wording_score_high(text, reason):
    signal = _score(text)
    assert signal.signal_name == "similarity"
    assert signal.score >= 0.7
    assert reason in signal.explanation


@pytest.mark.parametrize("text", [
    "Your verification code is 482913. Never share this code with anyone.",
    "Your bank will never ask you to move money to a safe account.",
    "Hi Jane, invoice for last month attached, same account as usual, due end of month.",
    "Don't tell Tom but I got him concert tickets for his birthday!",
    "At A&E with Dad, he's fine, just a check-up. Will call later.",
    "Your parcel will arrive today between 1 and 3pm.",
    "I'll send you the photos from the party tonight!",
    "Can you send the wedding photos to the family group?",
    "The football training fee for next term is 40, pay at the club.",
    "Welcome to the team! We will never charge you a fee to start. Your first day is Monday.",
])
def test_legit_messages_with_scam_vocabulary_score_low(text):
    assert _score(text).score < 0.5


def test_wording_alone_is_capped():
    # Indistinguishable from a real "new number" text: needs another signal to agree.
    signal = _score("hi mum its me, phone broke this is my new number. need to pay something today can u help")
    assert signal.score <= MATCH_CAP
    assert "family emergency or new-number scam" in signal.explanation


def test_red_flags_compound():
    one = _score("Please buy Amazon gift cards and send me the codes.").score
    two = _score("Please buy Amazon gift cards and send me the codes. Keep this between us.").score
    assert two > one


def test_missing_or_bad_text_is_no_evidence():
    for interaction in ({}, {"message_text": None}, {"message_text": "   "}, {"message_text": 12345}):
        signal = similarity_score(interaction)
        assert signal.score == 0.0
        assert signal.explanation == "No message text to compare"


def test_very_long_text_is_handled():
    signal = _score("Please move your money to a safe account. " + "blah " * 10000)
    assert 0.0 <= signal.score <= 1.0
