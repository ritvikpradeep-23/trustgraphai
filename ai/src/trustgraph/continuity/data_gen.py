"""Synthetic identity histories for legit traffic.

Legit contacts do change their details for honest reasons; these rates are
judgment calls standing in for real data, and they set how noisy continuity
is on legit calls (and so where the fused Caution/High lines land):

    first contact, no history ........ 10% of interactions
    payout account on the interaction  30% (money requests only)
      - new account (switched banks) .  1% of those
      - account added 1-29 days ago ..  1% of those
    phone number on the interaction .. 70%, new number 3%
    email domain on the interaction .. 50%, new domain 0.5%
    display name on the interaction .. 90%, nickname/typo 2%, new name 0.5%
"""
import json
import string

import numpy as np

DOMAINS = ["acme-corp.com", "northwind.co.uk", "brightpath.io", "fabrikam.net", "contoso.com",
           "gmail.com", "outlook.com", "harbourline.org", "tailspin.travel", "woodgrove.bank"]
FIRST = ["Jane", "Priya", "Tom", "Aisha", "Marco", "Chen", "Olu", "Sara", "Dev", "Lena"]
LAST = ["Doe", "Patel", "Nguyen", "Okafor", "Rossi", "Kim", "Silva", "Novak", "Haddad", "Berg"]


def random_account(rng) -> str:
    letters = "".join(rng.choice(list(string.ascii_uppercase), 4))
    return f"GB{rng.integers(10, 99)}{letters}{rng.integers(10**13, 10**14)}"


def random_phone(rng) -> str:
    return f"+447{rng.integers(10**8, 10**9)}"


def random_name(rng) -> str:
    return f"{rng.choice(FIRST)} {rng.choice(LAST)}"


def name_variant(rng, name: str) -> str:
    """Nickname or typo: drop, double or swap one letter."""
    i = int(rng.integers(1, len(name) - 1))
    return rng.choice([name[:i] + name[i + 1:], name[:i] + name[i] + name[i:], name[:i] + name[i + 1] + name[i] + name[i + 2:]])


def random_contact(rng) -> dict:
    """A contact's established details: value -> days since first seen."""
    return {
        "payout_account": {random_account(rng): int(rng.integers(60, 2000))},
        "phone_number": {random_phone(rng): int(rng.integers(60, 2000))},
        "email_domain": {str(rng.choice(DOMAINS)): int(rng.integers(60, 2000))},
        "display_name": {random_name(rng): int(rng.integers(60, 2000))},
    }


def legit_identity(rng) -> dict:
    known = random_contact(rng)
    current = {field: next(iter(values)) for field, values in known.items()}

    if rng.random() < 0.30:
        roll = rng.random()
        if roll < 0.01:
            current["payout_account"] = random_account(rng)
        elif roll < 0.02:
            current["payout_account"] = random_account(rng)
            known["payout_account"][current["payout_account"]] = int(rng.integers(1, 30))
    else:
        del current["payout_account"]

    if rng.random() < 0.70:
        if rng.random() < 0.03:
            current["phone_number"] = random_phone(rng)
    else:
        del current["phone_number"]

    if rng.random() < 0.50:
        if rng.random() < 0.005:
            current["email_domain"] = str(rng.choice([d for d in DOMAINS if d != current["email_domain"]]))
    else:
        del current["email_domain"]

    if rng.random() < 0.90:
        roll = rng.random()
        if roll < 0.02:
            current["display_name"] = name_variant(rng, current["display_name"])
        elif roll < 0.025:
            current["display_name"] = random_name(rng)
    else:
        del current["display_name"]

    if rng.random() < 0.10:
        return {"identity": current, "known_identity": {}}
    return {"identity": current, "known_identity": known}


def generate_legit(n: int, seed: int) -> list[dict]:
    rng = np.random.default_rng(seed)
    return [legit_identity(rng) for _ in range(n)]


def main():
    # Seeds pair with the anomaly calibration/test CSVs row for row; identity
    # changes are drawn independently of the call's behavioural features.
    for name, seed in (("legit_calibration", 12), ("legit_test", 13)):
        path = f"data/continuity/{name}.json"
        with open(path, "w") as f:
            json.dump(generate_legit(1000, seed), f)
        print(f"Wrote 1000 rows -> {path}")


if __name__ == "__main__":
    main()
