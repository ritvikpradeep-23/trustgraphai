"""Independent check of the precedent signal, end to end through fusion.

Builds its own report database (not data/precedent/reports.json) and then
presents reported identifiers the messy ways people actually write them: with
spaces, brackets and dashes, mid-sentence, inside links and email addresses.
Legit messages are full of harmless numbers, links and addresses. Call
features are calm, so the result shows what precedent catches on its own.

Run: PYTHONPATH=src python3 scratch/precedent_check.py [seed]
"""
import json
import string
import sys

import numpy as np

from trustgraph.fusion import BANDS_PATH, risk_band
from trustgraph.pipeline import score_interaction
from trustgraph.precedent import detector

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
rng = np.random.default_rng(SEED)
BANDS = json.load(open(BANDS_PATH))
CALM = {"duration_sec": 100, "hour_of_day": 12, "amount_ratio": 1.0,
        "contact_freq_24h": 1, "urgency_score": 0, "new_channel_flag": 0}
results = []
print(f"seed {SEED}")


def check(name, passed, detail):
    results.append(passed)
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")


def pick(options):
    return str(rng.choice(options))


def uk_mobile():
    return f"7{rng.integers(100_000_000, 999_999_999)}"  # national number without leading 0


def phone_styles(national):
    return [f"+44{national}", f"0{national}", f"+44 (0){national[:4]} {national[4:]}",
            f"0{national[:4]} {national[4:7]} {national[7:]}", f"0{national[:4]}-{national[4:]}"]


def iban():
    return f"GB{rng.integers(10, 99)}{''.join(rng.choice(list(string.ascii_uppercase), 4))}{rng.integers(10**13, 10**14)}"


def iban_styles(acct):
    spaced = " ".join(acct[i:i + 4] for i in range(0, len(acct), 4))
    return [acct, spaced, acct.lower(), spaced.lower()]


def scam_domain():
    return f"{pick(['secure', 'my', 'help', 'claim', 'verify'])}-{pick(['parcel', 'refund', 'bank', 'tax', 'wallet'])}{rng.integers(1, 999)}.{pick(['com', 'net', 'info', 'co.uk', 'top'])}"


def domain_styles(domain):
    return [domain, f"www.{domain}", f"https://{domain}/login", f"http://www.{domain}/track?id={rng.integers(1000, 9999)}",
            f"{domain.upper()}"]


def wallet():
    return "bc1q" + "".join(rng.choice(list("023456789acdefghjklmnpqrstuvwxyz"), 38))


# Fresh report database for this run.
reported = {"phone": [uk_mobile() for _ in range(150)], "account": [iban() for _ in range(150)],
            "domain": [scam_domain() for _ in range(150)], "wallet": [wallet() for _ in range(50)]}
reports = []
for kind, values in reported.items():
    for v in values:
        reports.append({"type": kind, "value": f"0{v}" if kind == "phone" else v,
                        "reports": int(rng.integers(2, 15)), "last_reported_days": int(rng.integers(0, 180)),
                        "category": "scam"})
old_numbers = [uk_mobile() for _ in range(50)]
reports += [{"type": "phone", "value": f"+44{n}", "reports": 1, "last_reported_days": int(rng.integers(800, 2000)),
             "category": "scam"} for n in old_numbers]
detector._index = detector.load_reports(reports)


def band(interaction):
    return risk_band(score_interaction({**CALM, **interaction})[1].score, BANDS)


print("1. Reported identifiers coming back, written every which way (300 each)")
cases = {
    "reported number calling": lambda: {"identity": {"phone_number": pick(phone_styles(pick(reported["phone"])))}},
    "reported number in the message": lambda: {"message_text": f"Ring me back on {pick(phone_styles(pick(reported['phone'])))} asap"},
    "reported account to pay": lambda: {"identity": {"payout_account": pick(iban_styles(pick(reported['account'])))}},
    "reported account in the message": lambda: {"message_text": f"Please transfer it to {pick(iban_styles(pick(reported['account'])))}. Thanks"},
    "reported link in the message": lambda: {"message_text": f"Confirm your details here: {pick(domain_styles(pick(reported['domain'])))}"},
    "reported wallet in the message": lambda: {"message_text": f"Send the coins to {pick(reported['wallet'])} and I'll do the rest"},
}
for name, make in cases.items():
    rate = float(np.mean([band(make()) != "Low" for _ in range(300)]))
    check(f"{name} caught", rate >= 0.99, f"{rate:.1%}")

print()
print("2. Legit messages full of harmless numbers, links and accounts (1000)")
LEGIT = [
    "Call me on {phone} when you're free.", "My new number is {phone}, save it!",
    "Invoice attached, pay to {acct} as usual.", "Menu's at {site}, booking for 8?",
    "Tracking: {site}/track?id={n}", "Order {n} confirmed, total 23.50.", "See {site} for the timetable.",
    "Email me at sam.{n}@outlook.com", "Ref {n}, sort code 20-00-00, thanks!",
]
legit_sites = ["bbc.co.uk", "trainline.com", "royalmail.com", "nhs.uk", "gov.uk", "amazon.co.uk", "bookings.example.org"]
legit = [{"message_text": pick(LEGIT).format(phone=pick(phone_styles(uk_mobile())), acct=pick(iban_styles(iban())),
                                              site=pick(legit_sites), n=rng.integers(10000, 9999999))}
         for _ in range(1000)]
flagged = float(np.mean([band(i) != "Low" for i in legit]))
check("legit messages are not flagged", flagged <= 0.01, f"{flagged:.1%} flagged")

print()
print("3. Fading and near misses")
old = float(np.mean([band({"identity": {"phone_number": pick(phone_styles(n))}}) != "Low" for n in old_numbers]))
check("a single report from 2+ years ago doesn't alarm on its own", old == 0.0, f"{old:.0%} flagged")
near = []
for v in reported["phone"][:100]:
    tweaked = v[:-1] + str((int(v[-1]) + 1) % 10)
    near.append(band({"identity": {"phone_number": f"0{tweaked}"}}) != "Low")
check("a number one digit off a reported one doesn't match", not any(near), f"{np.mean(near):.0%} flagged")

print()
print(f"{sum(results)}/{len(results)} checks passed")
