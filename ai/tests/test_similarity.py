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
    ("Hello from the returns desk. Install our help app, then read me the code so I can finish your refund.",
     "asks for a one-time code, PIN or password"),
])

def test_scam_asks_in_new_wording_score_high(text, reason):
    signal = _score(text)
    assert signal.signal_name == "similarity"
    assert signal.score >= 0.7
    assert reason in signal.explanation

@pytest.mark.parametrize("text, reason", [
    ("Final notice: your parcel will be returned unless the storage fee is paid.", "asks for an upfront fee"),
    ("Support here. Open the app and share the code with us to continue.", "asks for a one-time code, PIN or password"),
])
def test_closed_gaps_raise_their_red_flag(text, reason):
    assert reason in _score(text).explanation


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
    # Warnings with "asks", or "never" right before the ask
    "Stay safe online: Kestrel Bank never asks for your PIN by email. Never share your password with anybody.",
    # Hinglish and Manglish put the "don't" after the verb
    "319204 aapka login OTP hai. Ise kisi se share na karein.",
    "Apna OTP kisi ko bhi mat share karo, bank wale kabhi nahi poochte.",
    "602118 aanu ningalude OTP. Ithu aarumaayi share cheyyaruthu.",
    # Code-sharing that isn't an ask for a login code
    "Share your referral code with friends and you both get 10% off.",
    "I'll send the code for the side gate later, share the code with your family too.",
    "ok see you at 7",
])
def test_legit_messages_with_scam_vocabulary_score_low(text):
    assert _score(text).score < 0.5


@pytest.mark.parametrize("text", [
    # A secrecy demand isn't a warning: "don't tell your family" must not cancel the ask after it.
    "Do not tell your family about this, send me the OTP now.",
    # "share na?" asks ("share it, ok?"), it doesn't forbid.
    "Share na? Send me the verification code you just got.",
    "Bhai jaldi share karo the OTP code sent to your phone.",
])
def test_negation_guard_doesnt_hide_real_asks(text):
    assert "asks for a one-time code, PIN or password" in _score(text).explanation


@pytest.mark.parametrize("text, reason", [
    ("Mum I'm fine but I hit a cyclist. Please send £700 to the man's account so he doesn't call the police.",
     "asks you to pay someone else's account in an emergency"),
    ("Uncle I'm in hospital after a bike crash, they need 15,000 before the scan, please send it now.",
     "asks for money inside an emergency story"),
    ("Hi Dad, lost my phone, this is my new number. Can you transfer $450 for my rent today?",
     "asks for money from a new or borrowed phone"),
    ("If you ever cared about me you'll send 8,000 tonight.",
     "pressures you with guilt, self-harm or a threat to pay"),
    ("Pay 20,000 by Friday or I'll send the screenshots to your wife.",
     "threatens to contact your contacts, family or employer"),
    ("Stay on this video call and do not inform anyone, you are under investigation.",
     "tells you to stay on a video call (\"digital arrest\")"),
])
def test_emotional_pressure_rules(text, reason):
    assert reason in _score(text).explanation


@pytest.mark.parametrize("text", [
    # Real emergencies and honest money talk between family must not trip the new rules.
    "Mum, small crash on the way home, nobody hurt. Insurance is sorting it, call you later.",
    "Dad's in hospital for a routine check, all fine. Visiting hours are 4 to 6.",
    "Hi Dad, new number! Old phone died. Save this one, see you Sunday.",
    "Can you lend me 2,000 till Friday? No worries if not.",
    "Sent the 500 to your account for the cab, thanks!",
    "Share the photos with your family too, they'll love them.",
])
def test_honest_emotional_messages_dont_trip_new_rules(text):
    new_rules = {"asks you to pay someone else's account in an emergency", "asks for money inside an emergency story",
                 "asks for money from a new or borrowed phone", "pressures you with guilt, self-harm or a threat to pay",
                 "threatens to contact your contacts, family or employer"}
    explanation = _score(text).explanation
    assert not any(rule in explanation for rule in new_rules)


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
