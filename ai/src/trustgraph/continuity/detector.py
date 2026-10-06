"""Continuity signal: has this contact's identity changed?

Scammers who hijack or impersonate a known contact have to change something
stable about it: the account the money goes to, the number they call from,
the domain they email from. This signal compares the interaction's current
details against the details previously seen for the same contact.

Interaction fields:
    identity:        {field: value} as seen on this interaction
    known_identity:  {field: {value: days_since_first_seen}} from past
                     interactions with this contact (a plain list of values
                     is also accepted when ages aren't known)
Fields: payout_account, phone_number, email_domain, display_name.
"""
import math
from difflib import SequenceMatcher

from trustgraph.identifiers import normalize_account, normalize_domain, normalize_phone, split_domain
from trustgraph.signal import RiskSignal

FIELDS = ["payout_account", "email_domain", "phone_number", "display_name"]

# Evidence (0-1) that a never-before-seen value is a takeover rather than a
# legit change. A new payout account is the core tell of invoice/CEO fraud;
# people change names and numbers far more often than bank accounts.
NEW_VALUE = {"payout_account": 0.8, "email_domain": 0.6, "phone_number": 0.5, "display_name": 0.3}

# A value that is close to, but not exactly, a known one. For a domain that is
# typosquatting ("acme-c0rp.com", or the same brand on another ending like
# "acme-corp.co"), which is worse than an honestly new domain.
# For a name it's usually a nickname or typo, so it's weaker than a new name.
LOOKALIKE_VALUE = {"email_domain": 0.95, "display_name": 0.1}
LOOKALIKE_RATIO = 0.8

# A known value first seen recently still counts: an account swapped in on
# last week's call is no safer for being reused. Full weight for the first two
# weeks, then decaying linearly to zero by day 60.
RECENT_FULL_DAYS = 14
RECENT_DAYS = 60

_LABEL = {
    "payout_account": "payout account",
    "email_domain": "email domain",
    "phone_number": "phone number",
    "display_name": "name",
}


def _normalize(field: str, value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if field == "payout_account":
        text = normalize_account(text)
    elif field == "phone_number":
        text = normalize_phone(text)
    elif field == "email_domain":
        text = normalize_domain(text)
    else:
        text = " ".join(text.casefold().split())
    return text or None


def _lookalike(field: str, a: str, b: str) -> bool:
    if field == "email_domain":
        (brand_a, suffix_a), (brand_b, suffix_b) = split_domain(a), split_domain(b)
        if brand_a == brand_b:
            return suffix_a != suffix_b
        return SequenceMatcher(None, brand_a, brand_b).ratio() >= LOOKALIKE_RATIO
    return SequenceMatcher(None, a, b).ratio() >= LOOKALIKE_RATIO


def _known_values(field: str, raw) -> dict[str, tuple[float | None, str]]:
    """normalized value -> (days since first seen or None if unknown, original text)."""
    if isinstance(raw, dict):
        items = raw.items()
    elif isinstance(raw, (list, tuple, set)):
        items = ((v, None) for v in raw)
    else:
        items = [(raw, None)]
    out = {}
    for value, days in items:
        norm = _normalize(field, value)
        if norm is None:
            continue
        try:
            age = float(days)
            age = age if math.isfinite(age) and age >= 0 else None
        except (TypeError, ValueError):
            age = None
        out[norm] = (age, str(value).strip())
    return out


def _show(field: str, norm: str, original: str) -> str:
    """Accounts and numbers are masked to their last 4 characters for the UI."""
    if field in ("payout_account", "phone_number"):
        return f"…{norm[-4:]}"
    return f"'{norm if field == 'email_domain' else original}'"


def _field_evidence(field: str, current: str, current_raw: str,
                    known: dict[str, tuple[float | None, str]]) -> tuple[float, str]:
    shown = _show(field, current, current_raw)
    if current in known:
        age = known[current][0]
        if age is None or age >= RECENT_DAYS:
            return 0.0, ""
        fade = max(age - RECENT_FULL_DAYS, 0) / (RECENT_DAYS - RECENT_FULL_DAYS)
        evidence = NEW_VALUE[field] * (1 - fade)
        return evidence, f"{_LABEL[field]} {shown} first seen {age:.0f} days ago"

    closest = max(known, key=lambda k: SequenceMatcher(None, current, k).ratio())
    closest_shown = _show(field, closest, known[closest][1])
    if field in LOOKALIKE_VALUE and _lookalike(field, current, closest):
        verb = "imitates" if field == "email_domain" else "is a variant of"
        return LOOKALIKE_VALUE[field], f"{_LABEL[field]} {shown} {verb} known {closest_shown}"
    if field == "display_name":
        return NEW_VALUE[field], f"name {shown} differs from known {closest_shown}"
    return NEW_VALUE[field], f"{_LABEL[field]} changed to {shown}, never used by this contact"


def continuity_score(interaction: dict) -> RiskSignal:
    identity = interaction.get("identity")
    history = interaction.get("known_identity")
    identity = identity if isinstance(identity, dict) else {}
    history = history if isinstance(history, dict) else {}

    findings = []
    compared = 0
    for field in FIELDS:
        raw = identity.get(field)
        current = _normalize(field, raw)
        known = _known_values(field, history.get(field))
        if current is None or not known:
            continue
        compared += 1
        evidence, reason = _field_evidence(field, current, str(raw).strip(), known)
        if evidence > 0:
            findings.append((evidence, reason))

    # Noisy-OR, like fusion: each changed detail is an independent chance of takeover.
    score = 1.0 - math.prod(1.0 - e for e, _ in findings)

    if findings:
        findings.sort(reverse=True)
        explanation = "Identity changed: " + "; ".join(reason for _, reason in findings)
    elif compared:
        explanation = "Identity details match this contact's history"
    else:
        explanation = "No identity history to compare"

    return RiskSignal(signal_name="continuity", score=score, explanation=explanation)
