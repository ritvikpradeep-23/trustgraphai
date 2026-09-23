"""Hand-written named scenarios spanning every signal, so detection on them
isn't guaranteed by any one generator. Each is a full interaction dict.

"scam" scenarios should reach Caution or above. "legit" ones are controls:
honest changes the system should NOT alarm on. subtle_invoice_bump is
deliberately mild and shows where a single signal needs help from others.
"""
import math

_ACCT = "GB29NWBK60161331926819"
_PHONE = "+442079460958"
_KNOWN = {
    "payout_account": {_ACCT: 540},
    "phone_number": {_PHONE: 800},
    "email_domain": {"acme-corp.com": 900},
    "display_name": {"Jane Doe": 900},
}
_SAME = {"payout_account": _ACCT, "phone_number": _PHONE, "email_domain": "acme-corp.com", "display_name": "Jane Doe"}
_CALM = {"duration_sec": 95, "hour_of_day": 11, "amount_ratio": 1.0,
         "contact_freq_24h": 1, "urgency_score": 0, "new_channel_flag": 0}


def _call(**features):
    return {**_CALM, **features}


def _id(**changes):
    return {"identity": {**_SAME, **changes}, "known_identity": _KNOWN}


SCENARIOS = [
    # Behavioural scams (anomaly signal)
    ("grandparent_emergency", "scam", {
        **_call(duration_sec=150, hour_of_day=2, amount_ratio=6.0, contact_freq_24h=3, urgency_score=5, new_channel_flag=1),
        **_id(phone_number="+447700900123"),
        "message_text": "Grandma it's me, I've been arrested and need bail money tonight. Please don't tell Mum, send it to my lawyer."}),
    ("ceo_wire_fraud", "scam", {
        **_call(duration_sec=60, amount_ratio=9.0, contact_freq_24h=2, urgency_score=4),
        **_id(email_domain="acme-corp.co", payout_account="DE89370400440532013000"),
        "message_text": "I need you to process an urgent wire today for the acquisition. Keep this between us until it's announced."}),
    ("sim_swap_takeover", "scam", {
        # The number is hijacked, so it matches history; only the payout moves.
        **_call(duration_sec=45, hour_of_day=14, amount_ratio=3.5, urgency_score=1, new_channel_flag=1),
        **_id(payout_account="GB94BARC10201530093459")}),
    ("harassment_burst", "scam", _call(duration_sec=15, hour_of_day=22, contact_freq_24h=20, urgency_score=2)),
    ("romance_scam_escalation", "scam", {
        **_call(duration_sec=900, hour_of_day=23, amount_ratio=4.0, contact_freq_24h=4, urgency_score=1),
        "message_text": "My love, I'm stuck abroad and my account is frozen. You're the only one I trust, please send money for my flight home."}),
    ("tech_support_popup", "scam", {
        **_call(duration_sec=1200, hour_of_day=16, amount_ratio=2.5, urgency_score=3, new_channel_flag=1),
        "message_text": "This is Microsoft support, your computer is infected. Install AnyDesk so our engineer can remove the virus."}),
    ("one_ring_callback_bait", "scam", _call(duration_sec=1, hour_of_day=3, amount_ratio=math.nan, contact_freq_24h=5, new_channel_flag=1)),
    ("subtle_invoice_bump", "scam", _call(hour_of_day=10, amount_ratio=1.6, urgency_score=1)),
    # Identity scams where the call itself looks routine (continuity signal)
    ("invoice_redirect_compromised_mailbox", "scam", {
        **_call(amount_ratio=1.02), **_id(payout_account="GB94BARC10201530093459"),
        "message_text": "Please note our bank details have changed. Kindly pay this month's invoice to the new account below."}),
    ("lookalike_domain_invoice", "scam", {
        **_call(amount_ratio=1.05), **_id(email_domain="acme-c0rp.com", payout_account="GB33BUKB20201555555555")}),
    ("account_swapped_last_week", "scam", {
        **_call(amount_ratio=0.98),
        "identity": {**_SAME, "payout_account": "GB12MIDL40051512345678"},
        "known_identity": {**_KNOWN, "payout_account": {_ACCT: 540, "GB12MIDL40051512345678": 6}}}),
    ("new_number_family_impersonation", "scam", {
        **_call(amount_ratio=1.8, urgency_score=2), **_id(phone_number="+447700900456"),
        "message_text": "Hi Mum it's me, new number, my old phone broke. Can you help me pay a bill today?"}),
    # Scams only the wording gives away: identity and call behaviour look normal
    ("hijacked_mailbox_gift_cards", "scam", {
        **_call(), **_id(),
        "message_text": "Are you at your desk? I need 5 Amazon gift cards for a client today, send me the codes. Keep it confidential."}),
    ("bank_safe_account_call", "scam", {
        **_call(duration_sec=140),
        "message_text": "This is your bank's fraud team. Your account is compromised, move your savings to the safe account I give you."}),
    ("one_time_code_theft", "scam", {
        **_call(duration_sec=70),
        "message_text": "To cancel the suspicious payment I just need you to read me the six digit code we texted you."}),
    # Honest changes that should stay Low
    ("legit_new_phone", "legit", {**_call(), **_id(phone_number="+447700900789")}),
    ("legit_nickname", "legit", {**_call(), **_id(display_name="Janie Doe")}),
    ("legit_routine_payment", "legit", {
        **_call(), **_id(), "message_text": "Hi, invoice 4471 attached for March, payable to the usual account by Friday. Thanks!"}),
    ("legit_2fa_text", "legit", {
        **_call(), "message_text": "Your verification code is 482913. Never share this code with anyone, we will never ask for it."}),
    ("legit_surprise_party", "legit", {
        **_call(), **_id(), "message_text": "Don't tell Tom but we're throwing him a surprise party Saturday, can you bring snacks?"}),
]
