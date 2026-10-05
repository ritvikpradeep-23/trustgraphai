"""Precedent signal: has this number, account, link or wallet been reported
as a scam before?

Checks the interaction's own identifiers (phone number, payout account,
email domain/address) and any identifiers written in the message text
against a database of scam reports. Matching is exact after normalization,
so "+44 (0)7700 900123" finds a report filed as "07700900123", but a number
one digit off does not match: precedent is about the same actor coming back.

Report evidence grows with the number of independent reports and fades with
age, because numbers and accounts get recycled to innocent owners.

Reports file: list of {"type", "value", "reports", "last_reported_days",
"category"}, type one of phone, account, domain, email, wallet.
"""
import json
import math
import re

from trustgraph.identifiers import normalize_account, normalize_domain, normalize_phone
from trustgraph.signal import RiskSignal

REPORTS_PATH = "data/precedent/reports.json"
MAX_CHARS = 5000

# One report gives 0.6, two 0.84, three 0.94: each independent report is
# another person confirming the same identifier was used to scam them.
PER_REPORT = 0.6
# Full weight for reports from the last 6 months, fading to half by 2 years.
FRESH_DAYS = 180
STALE_DAYS = 730
STALE_WEIGHT = 0.5

_PHONE_IN_TEXT = re.compile(r"(?<![\w.])\+?\(?\d[\d\s().-]{8,16}\d(?![\w.])")
_ACCOUNT_IN_TEXT = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){2,7}(?:\s?[A-Z0-9]{1,4})?\b", re.IGNORECASE)
_EMAIL_IN_TEXT = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_DOMAIN_IN_TEXT = re.compile(r"\b(?:https?://)?(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/\S*)?", re.IGNORECASE)
_WALLET_IN_TEXT = re.compile(r"\b(?:bc1[a-z0-9]{25,59}|[13][a-km-zA-HJ-NP-Z1-9]{25,34}|0x[a-fA-F0-9]{40})\b")

_LABEL = {"phone": "phone number", "account": "account", "domain": "website/domain",
          "email": "email address", "wallet": "crypto wallet"}

_index = None


def _normalize(kind: str, value: str) -> str:
    value = str(value).strip()
    if kind == "phone":
        return normalize_phone(value)
    if kind == "account":
        return normalize_account(value)
    if kind == "domain":
        return normalize_domain(value)
    if kind == "email":
        return value.lower()
    return value  # wallets are case-sensitive


def load_reports(reports: list[dict]) -> dict:
    """Index reports by (type, normalized value), merging duplicates."""
    index = {}
    for r in reports:
        key = (r["type"], _normalize(r["type"], r["value"]))
        if not key[1]:
            continue
        if key in index:
            prev = index[key]
            index[key] = {**prev, "reports": prev["reports"] + r["reports"],
                          "last_reported_days": min(prev["last_reported_days"], r["last_reported_days"])}
        else:
            index[key] = dict(r)
    return index


def _get_index() -> dict:
    global _index
    if _index is None:
        with open(REPORTS_PATH) as f:
            _index = load_reports(json.load(f))
    return _index


def _candidates(interaction: dict) -> list[tuple[str, str, str]]:
    """(type, normalized value, where it was found)."""
    found = []
    identity = interaction.get("identity")
    if isinstance(identity, dict):
        for field, kind in (("phone_number", "phone"), ("payout_account", "account")):
            if identity.get(field):
                found.append((kind, _normalize(kind, identity[field]), "caller"))
        email = identity.get("email_domain")
        if email:
            found.append(("domain", _normalize("domain", email), "caller"))
            if "@" in str(email):
                found.append(("email", _normalize("email", email), "caller"))

    text = interaction.get("message_text")
    if isinstance(text, str) and text.strip():
        text = text[:MAX_CHARS]
        for m in _EMAIL_IN_TEXT.finditer(text):
            found.append(("email", _normalize("email", m.group()), "message"))
        for m in _DOMAIN_IN_TEXT.finditer(_EMAIL_IN_TEXT.sub(" ", text)):
            found.append(("domain", _normalize("domain", m.group()), "message"))
        for m in _ACCOUNT_IN_TEXT.finditer(text):
            found.append(("account", _normalize("account", m.group()), "message"))
        for m in _PHONE_IN_TEXT.finditer(text):
            if len(re.sub(r"\D", "", m.group())) >= 10:
                found.append(("phone", _normalize("phone", m.group()), "message"))
        for m in _WALLET_IN_TEXT.finditer(text):
            found.append(("wallet", m.group(), "message"))
    return [c for c in found if c[1]]


def _evidence(report: dict) -> float:
    count = max(int(report["reports"]), 1)
    age = max(float(report["last_reported_days"]), 0.0)
    if age <= FRESH_DAYS:
        recency = 1.0
    elif age >= STALE_DAYS:
        recency = STALE_WEIGHT
    else:
        recency = 1.0 - (1.0 - STALE_WEIGHT) * (age - FRESH_DAYS) / (STALE_DAYS - FRESH_DAYS)
    return (1.0 - (1.0 - PER_REPORT) ** count) * recency


def _show(kind: str, value: str) -> str:
    if kind in ("phone", "account"):
        return f"…{value[-4:]}"
    if kind == "wallet":
        return f"{value[:6]}…"
    return f"'{value}'"


def _when(days: float) -> str:
    days = int(days)
    if days == 0:
        return "today"
    if days < 60:
        return f"{days} days ago"
    if days < 730:
        return f"{days // 30} months ago"
    return f"{days // 365} years ago"


def precedent_score(interaction: dict) -> RiskSignal:
    index = _get_index()
    hits = {}
    for kind, value, where in _candidates(interaction):
        report = index.get((kind, value))
        if report and (kind, value) not in hits:
            hits[(kind, value)] = (report, where)

    if not hits:
        return RiskSignal(signal_name="precedent", score=0.0, explanation="No matching scam reports")

    findings = []
    for (kind, value), (report, where) in hits.items():
        times = "once" if report["reports"] == 1 else f"{report['reports']} times"
        source = "" if where == "caller" else " (in the message)"
        findings.append((_evidence(report),
                         f"{_LABEL[kind]} {_show(kind, value)}{source} was reported {times} for "
                         f"{report['category']}, last {_when(report['last_reported_days'])}"))
    score = 1.0 - math.prod(1.0 - e for e, _ in findings)
    findings.sort(reverse=True)
    return RiskSignal(signal_name="precedent", score=float(score),
                      explanation="Reported before: " + "; ".join(reason for _, reason in findings))
