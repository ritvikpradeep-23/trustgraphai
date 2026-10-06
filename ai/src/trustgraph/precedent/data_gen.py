"""Synthetic scam-report database standing in for a shared report feed
(e.g. a bank consortium or national fraud reporting service).

400 random reported identifiers plus a few named ones the example scenarios
use. Report counts are skewed (most identifiers are reported once or twice,
a few dozens of times) and ages spread over four years.
"""
import json
import string

import numpy as np

CATEGORIES = ["bank impersonation", "invoice fraud", "parcel phishing", "crypto investment scam",
              "romance scam", "tech support scam", "tax impersonation", "money mule account",
              "gift-card scam", "CEO fraud"]
WORDS = ["secure", "verify", "parcel", "refund", "account", "help", "support", "billing",
         "update", "track", "claim", "wallet", "login", "service", "alert"]
TLDS = [".com", ".co.uk", ".net", ".info", ".top", ".xyz", ".online"]
BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

# Used by trustgraph.scenarios; keep the two in sync.
NAMED = [
    {"type": "phone", "value": "+44 7700 900999", "reports": 9, "last_reported_days": 12, "category": "bank impersonation"},
    {"type": "account", "value": "GB82 WEST 1234 5698 7654 32", "reports": 4, "last_reported_days": 30, "category": "money mule account"},
    {"type": "domain", "value": "royalmail-redeliver.com", "reports": 23, "last_reported_days": 3, "category": "parcel phishing"},
    {"type": "wallet", "value": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh", "reports": 6, "last_reported_days": 20, "category": "crypto investment scam"},
    {"type": "email", "value": "ceo.office.acme@gmail.com", "reports": 2, "last_reported_days": 45, "category": "CEO fraud"},
    {"type": "account", "value": "GB94BARC10201530093459", "reports": 3, "last_reported_days": 60, "category": "invoice fraud"},
    # A recycled number: one report, three years ago. Should not alarm on its own.
    {"type": "phone", "value": "+44 7700 900111", "reports": 1, "last_reported_days": 1100, "category": "tech support scam"},
]


def _random_value(rng, kind: str) -> str:
    if kind == "phone":
        return f"+447{rng.integers(10**8, 10**9)}"
    if kind == "account":
        letters = "".join(rng.choice(list(string.ascii_uppercase), 4))
        return f"GB{rng.integers(10, 99)}{letters}{rng.integers(10**13, 10**14)}"
    if kind == "domain":
        return f"{rng.choice(WORDS)}-{rng.choice(WORDS)}{rng.integers(1, 99)}{rng.choice(TLDS)}"
    if kind == "email":
        return f"{rng.choice(WORDS)}.{rng.choice(WORDS)}{rng.integers(1, 999)}@{rng.choice(['gmail.com', 'outlook.com', 'proton.me'])}"
    return "1" + "".join(rng.choice(list(BASE58), 33))


def generate_reports(n: int = 400, seed: int = 42) -> list[dict]:
    rng = np.random.default_rng(seed)
    kinds = rng.choice(["phone", "account", "domain", "email", "wallet"], size=n, p=[0.35, 0.25, 0.2, 0.1, 0.1])
    reports = [{
        "type": str(kind),
        "value": _random_value(rng, kind),
        "reports": int(min(rng.geometric(0.45), 40)),
        "last_reported_days": int(rng.integers(0, 1500)),
        "category": str(rng.choice(CATEGORIES)),
    } for kind in kinds]
    return NAMED + reports


def main():
    reports = generate_reports()
    with open("data/precedent/reports.json", "w") as f:
        json.dump(reports, f, indent=1)
    print(f"Wrote {len(reports)} reports -> data/precedent/reports.json")


if __name__ == "__main__":
    main()
