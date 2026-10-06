"""Independent check of the continuity signal, end to end through fusion.

Generates its own contacts with messier, real-world formatting than
trustgraph.continuity.data_gen (spaced/lowercase account numbers, phone
numbers written several ways, mail subdomains, titles and middle initials in
names) and different legit change rates, so the rules are tested on input
they weren't written around. Call features are kept calm so the result shows
what continuity catches on its own.

Run: PYTHONPATH=src python3 scratch/continuity_check.py [seed]
"""
import json
import string
import sys

import numpy as np

from trustgraph.fusion import BANDS_PATH, risk_band
from trustgraph.pipeline import score_interaction

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


def account():
    return "GB" + str(rng.integers(10, 99)) + "".join(rng.choice(list(string.ascii_uppercase), 4)) + str(rng.integers(10**13, 10**14))


def spaced(acct):
    styled = " ".join(acct[i:i + 4] for i in range(0, len(acct), 4))
    return styled.lower() if rng.random() < 0.3 else styled


def phone_digits():
    return f"20{rng.integers(10**7, 10**8)}"  # UK London national number without leading 0


def phone_style(national):
    return str(rng.choice([f"+44{national}", f"+44 {national[:2]} {national[2:6]} {national[6:]}",
                           f"0{national}", f"+44 (0){national[:2]} {national[2:]}"]))


COMPANIES = ["meridian-supplies", "bluefin", "oakridge", "hollis-group", "quartzline", "vantagepoint"]
TLDS = [".com", ".co.uk", ".io", ".net"]
FIRST = ["Maria", "James", "Fatima", "Wei", "Kofi", "Anna", "Ravi", "Elena"]
LAST = ["Garcia", "Walker", "Hussain", "Zhang", "Mensah", "Kowalski", "Iyer", "Petrova"]


def typosquat(domain):
    name, tld = domain.split(".", 1)
    options = [
        name.replace("o", "0", 1) if "o" in name else name + "s",
        name.replace("m", "rn", 1) if "m" in name else name[:-1],
        name.replace("-", "", 1) if "-" in name else name + "-uk",
        name[:2] + name[3] + name[2] + name[4:] if len(name) > 4 else name + "x",
    ]
    squatted = str(rng.choice([o for o in options if o != name]))
    new_tld = tld if rng.random() < 0.6 else str(rng.choice([t for t in [".com", ".co", ".net"] if t != "." + tld]))[1:]
    return f"{squatted}.{new_tld}"


def contact():
    first, last = str(rng.choice(FIRST)), str(rng.choice(LAST))
    domain = str(rng.choice(COMPANIES)) + str(rng.choice(TLDS))
    return {"account": account(), "phone": phone_digits(), "domain": domain, "first": first, "last": last}


def history(c):
    age = lambda: int(rng.integers(90, 1500))
    return {"payout_account": {spaced(c["account"]): age()}, "phone_number": {phone_style(c["phone"]): age()},
            "email_domain": {c["domain"]: age()}, "display_name": {f"{c['first']} {c['last']}": age()}}


def presented(c):
    """Same contact, written however this interaction happens to write it."""
    name = str(rng.choice([f"{c['first']} {c['last']}", f"{c['first'].upper()} {c['last'].upper()}",
                           f"{c['first']} {c['last']}  "]))
    domain = c["domain"] if rng.random() > 0.05 else f"mail.{c['domain']}"
    return {"payout_account": spaced(c["account"]), "phone_number": phone_style(c["phone"]),
            "email_domain": f"accounts@{domain}", "display_name": name}


def interaction(identity, known):
    return {**CALM, "identity": identity, "known_identity": known}


def band(inter):
    return risk_band(score_interaction(inter)[1].score, BANDS)


print("1. Legit contacts, formatting noise plus honest changes (2000)")
legit, noise_only = [], []
for _ in range(2000):
    c = contact()
    known, ident = history(c), presented(c)
    noise_only.append(interaction(dict(ident), known))
    roll = rng.random()
    if roll < 0.05:
        ident["phone_number"] = phone_style(phone_digits())
    elif roll < 0.065:
        ident["payout_account"] = spaced(account())
    elif roll < 0.075:
        ident["email_domain"] = "billing@" + str(rng.choice(COMPANIES)) + str(rng.choice(TLDS))
    elif roll < 0.105:
        ident["display_name"] = str(rng.choice([f"{c['first']} {c['last'][0]}. {c['last']}", f"Dr {c['first']} {c['last']}",
                                                 f"{c['first'][:-1]} {c['last']}"]))
    legit.append(interaction(ident, known))
noise_flagged = np.mean([band(i) != "Low" for i in noise_only])
legit_flagged = np.mean([band(i) != "Low" for i in legit])
check("formatting alone never raises an alert", noise_flagged == 0, f"{noise_flagged:.1%} flagged")
check("legit traffic with honest changes stays within the 5% budget", legit_flagged <= 0.05, f"{legit_flagged:.1%} flagged")

print()
print("2. Identity-takeover fraud with routine-looking calls (300 each)")
fraud = {
    "new payout account": lambda c, k, i: i.update(payout_account=spaced(account())),
    "lookalike domain + new account": lambda c, k, i: i.update(email_domain="ap@" + typosquat(c["domain"]), payout_account=spaced(account())),
    "lookalike domain alone": lambda c, k, i: i.update(email_domain="ap@" + typosquat(c["domain"])),
    "account swapped 1-20 days ago": lambda c, k, i: (
        i.update(payout_account=(a := spaced(account()))), k["payout_account"].update({a: int(rng.integers(1, 21))})),
    "new number + new account": lambda c, k, i: i.update(phone_number=phone_style(phone_digits()), payout_account=spaced(account())),
}
for name, mutate in fraud.items():
    caught = []
    for _ in range(300):
        c = contact()
        known, ident = history(c), presented(c)
        mutate(c, known, ident)
        caught.append(band(interaction(ident, known)) != "Low")
    rate = float(np.mean(caught))
    check(f"{name} caught", rate >= 0.95, f"{rate:.1%}")

print()
print("3. Known blind spot (reported, not a target)")
c = contact()
spoof = band(interaction(presented(c), history(c)))
print(f"     exact impersonation with every detail copied -> {spoof} (continuity can't see it; other signals must)")

print()
print(f"{sum(results)}/{len(results)} checks passed")
