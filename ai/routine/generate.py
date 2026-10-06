"""Generate the 14 round batches for the fast routine.

    PYTHONPATH=src python -m routine.generate            # writes data/rounds/ (refuses if it exists)

  round_01-02  development: set Caution/High cut-offs, gate candidates. Never used for fixes.
  round_03-12  the ten improvement rounds.
  round_13-14  frozen final test: never used for fixes or tuning, scored once.

Every hand-written seed and every slot template is one template_family, and
each family lives in exactly one round. Scam types rotate: each improvement
round leans on a different window of types and two favoured evasion tricks.
Any message with word TF-IDF cosine above 0.9 to the engine's examples, the
earlier eval/ data, or an earlier round is dropped (leakage control).

Synthetic data only: fake placeholders, reserved-domain links or [LINK],
[PHONE], fictional names and brands.
"""
import argparse
import hashlib
import json
import math
import re
from datetime import date
from pathlib import Path

import numpy as np

from eval.generate import EVADE
from eval.leakage import filter_leaks
from routine.seeds_legit import LEGIT
from routine.seeds_scam_a import SCAM_A
from routine.seeds_scam_b import SCAM_B
from routine.seeds_scam_c import SCAM_C

OUT = Path("data/rounds")
MANIFEST = OUT / "MANIFEST.json"
N_ROUNDS = 14
DEV, IMPROVE, FINAL = (1, 2), tuple(range(3, 13)), (13, 14)
TARGET = {"scam": 60, "legit": 120}
SCAM = {**SCAM_A, **SCAM_B, **SCAM_C}

CHANNELS = ["whatsapp", "sms", "email", "instagram", "messenger"]
CHANNEL_P = [0.32, 0.30, 0.16, 0.12, 0.10]
SCAM_TRICKS = ["spacing", "leetspeak", "emoji_padding", "obfuscated_link", "split_phrasing"]
NAMES = ["Asha", "Vikram", "Neha", "Ravi", "Leena", "Omar", "Grace", "Daniel", "Divya", "Hari", "Mina", "Joel"]
BANKS = ["Lotus Bank", "Meridian Bank", "Pinecrest Bank", "Harbourline Bank", "your bank"]
BRANDS = ["Zippa", "Kartly", "Bluefin", "Novamart", "Streamly", "Cafe Orbit"]
COMPANIES = ["Tidewell Ltd", "Oakridge Partners", "Quillon Systems", "Marlow & Co"]
COURIERS = ["SwiftShip", "ParcelHub", "Expressly", "the courier"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "the 14th", "the 21st"]
TIMES = ["9am", "10:30am", "2pm", "4pm", "6:15pm"]
OPENERS = ["", "", "", "Hi, ", "Hello, ", "Hey, ", "Dear customer, "]
CLOSERS = ["", "", "", " Thanks.", " Regards.", " Sent from my phone", " Cheers."]
LINK_WORDS = ["secure", "pay", "help", "account", "update", "track", "orders", "portal", "info", "my", "app", "claim"]
URGENT = re.compile(r"\b(urgent|immediately|now|today|tonight|asap|within \d+ hours|final|last day|deadline)\b", re.I)


def _link(rng) -> str:
    """One link pool for BOTH labels, so link style can't give the label away."""
    a, b = rng.choice(LINK_WORDS, 2, replace=False)
    code = "".join(rng.choice(list("abcdefghjkmnpqrstuvwxyz23456789"), 6))
    return str(rng.choice([f"https://{a}.example.com/{code}", f"https://{a}-{b}.example.org/{code}",
                           f"http://{a}{rng.integers(1, 99)}.test/{b}", f"{a}-{b}.invalid/{code}", "[LINK]"]))


def _amount(rng) -> str:
    n = int(rng.choice([99, 249, 500, 750, 1200, 2500, 4999, 15000]))
    return str(rng.choice([f"Rs {n:,}", f"₹{n:,}", f"£{n:,}", f"${n:,}", f"Rs. {n:,}"]))


def fill(text: str, slots: dict, rng) -> str:
    common = {"name": str(rng.choice(NAMES)), "amount": _amount(rng), "link": _link(rng), "phone": "[PHONE]",
              "bank": str(rng.choice(BANKS)), "brand": str(rng.choice(BRANDS)), "company": str(rng.choice(COMPANIES)),
              "courier": str(rng.choice(COURIERS)), "day": str(rng.choice(DAYS)), "time": str(rng.choice(TIMES)),
              "code": str(rng.integers(100000, 999999))}
    for _ in range(3):  # slot values may contain further {slots}
        new = re.sub(r"\{(\w+)\}", lambda m: str(rng.choice(slots[m.group(1)])) if m.group(1) in slots
                     else common.get(m.group(1), m.group(0)), text)
        if new == text:
            break
        text = new
    return " ".join(text.split())


def frame(text: str, channel: str, rng) -> str:
    text = f"{rng.choice(OPENERS)}{text}{rng.choice(CLOSERS)}".strip()
    if channel == "email" and rng.random() < 0.5:
        text = "Subject: " + " ".join(text.split()[:5]).rstrip(",.!?:") + "\n\n" + text
    return text


def families() -> list[dict]:
    """Every seed and template, with the round it belongs to."""
    rng = np.random.default_rng(0)
    out = []
    for label, table in (("scam", SCAM), ("legit", LEGIT)):
        for ci, (cat, spec) in enumerate(sorted(table.items())):
            fams = [{"lang": lang, "text": t, "kind": "seed"} for lang, t in spec["seeds"]]
            fams += [{"lang": "English", "text": t, "kind": "template"} for t in spec["templates"]]
            order = rng.permutation(len(fams))
            for j, k in enumerate(order):
                f = {**fams[k], "label": label, "category": cat, "slots": spec.get("slots", {}),
                     "in_corpus": spec.get("in_corpus", "n/a")}
                if label == "scam":
                    # 1 dev family, 2 final-test families, 7 spread over a window of 5 improvement rounds.
                    if j == 0:
                        f["round"] = DEV[ci % 2]
                    elif j in (1, 2):
                        f["round"] = FINAL[j - 1]
                    else:
                        start = (ci * 2) % 10
                        f["round"] = 3 + (start + (j - 3) * 5 // 7) % 10
                else:
                    # 2 dev, 2 final-test, 9 spread one per improvement round.
                    if j in (0, 1):
                        f["round"] = DEV[j]
                    elif j in (2, 3):
                        f["round"] = FINAL[j - 2]
                    else:
                        f["round"] = 3 + (ci + j - 4) % 10
                f["template_family"] = f"{label[0]}{len(out):04d}"
                out.append(f)
    return out


def _difficulty(label: str, lang: str, evasion: str, text: str) -> str:
    if label == "legit":
        return "hard" if URGENT.search(text) or "code" in text.lower() else "medium"
    if evasion != "none" or lang != "English":
        return "hard"
    soft = not URGENT.search(text) and "[LINK]" not in text and "http" not in text
    return "hard" if soft else "medium"


def make_round(r: int, fams: list[dict], reference: list[str], rng) -> tuple[list[dict], int]:
    favoured = [SCAM_TRICKS[r % 5], SCAM_TRICKS[(r + 2) % 5]]
    rows, rows_removed = [], 0
    for label in ("scam", "legit"):
        mine = [f for f in fams if f["round"] == r and f["label"] == label]
        per = math.ceil(TARGET[label] * 1.6 / len(mine))
        cands, seen = [], set()
        for f in mine:
            for _ in range(per):
                text = fill(f["text"], f["slots"], rng)
                evasion = "none"
                if label == "scam" and rng.random() < 0.40:
                    evasion = str(rng.choice(favoured)) if rng.random() < 0.6 else str(rng.choice(SCAM_TRICKS))
                elif rng.random() < 0.12:
                    evasion = str(rng.choice(["emoji_padding", "casual_lowercase"]))  # both labels
                if evasion != "none":
                    text = EVADE[evasion](text, rng)
                channel = str(rng.choice(CHANNELS, p=CHANNEL_P))
                text = frame(text, channel, rng)
                if text in seen:
                    continue
                seen.add(text)
                cands.append({"text": text, "label": label, "category": f["category"],
                              "template_family": f["template_family"], "channel": channel, "language": f["lang"],
                              "evasion_type": evasion, "difficulty": _difficulty(label, f["lang"], evasion, text),
                              "in_corpus": f["in_corpus"], "round": r})
        kept, removed = filter_leaks(cands, reference)
        # Trim to the target, keeping at least one message from every family.
        by_fam = {}
        for c in kept:
            by_fam.setdefault(c["template_family"], []).append(c)
        chosen = [v[0] for v in by_fam.values()]
        rest = [c for v in by_fam.values() for c in v[1:]]
        idx = rng.permutation(len(rest))[:max(0, TARGET[label] - len(chosen))]
        chosen += [rest[i] for i in sorted(idx)]
        rows += chosen
        rows_removed += len(removed)
    rng.shuffle(rows)
    for i, row in enumerate(rows):
        row["id"] = f"r{r:02d}_{i:04d}"
    return [{k: row[k] for k in ("id", "text", "label", "category", "template_family", "channel", "language",
                                 "evasion_type", "difficulty", "in_corpus", "round")} for row in rows], rows_removed


def sha256(path: Path) -> str:
    from eval.leakage import sha256 as line_ending_safe_sha256
    return line_ending_safe_sha256(path)


def reference_texts() -> list[str]:
    """Everything a new round must not be a near-copy of: the engine's built-in
    examples and every message in the earlier evaluation data."""
    from trustgraph.similarity.corpus import LEGIT_MESSAGES, SCAM_SCRIPTS
    ref = [t for v in SCAM_SCRIPTS.values() for t in v] + list(LEGIT_MESSAGES)
    for p in sorted(Path("eval/data").glob("*.jsonl")):
        ref += [json.loads(line)["text"] for line in p.open(encoding="utf-8")]
    return ref


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if MANIFEST.exists() and not args.force:
        raise SystemExit(f"{MANIFEST} exists: the rounds are frozen. Use --force only before any round has been run.")
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    fams = families()
    reference = reference_texts()
    manifest = {"generator_seed": args.seed, "created": date.today().isoformat(), "synthetic_data": True,
                "dev_rounds": list(DEV), "improvement_rounds": list(IMPROVE), "final_test_rounds": list(FINAL),
                "leakage_threshold": 0.9, "files": {}}
    for r in range(1, N_ROUNDS + 1):
        rows, removed = make_round(r, fams, reference, rng)
        path = OUT / f"round_{r:02d}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        reference += [row["text"] for row in rows]
        counts = {lab: sum(row["label"] == lab for row in rows) for lab in ("scam", "legit")}
        cats = len({row["category"] for row in rows if row["label"] == "scam"})
        manifest["files"][path.name] = {"sha256": sha256(path), "counts": counts, "scam_categories": cats,
                                        "dropped_by_leakage": removed}
        print(f"{path.name}: {counts}, {cats} scam types, {removed} dropped as near-copies")
    MANIFEST.write_text(json.dumps(manifest, indent=1))
    print(f"wrote {MANIFEST}")


if __name__ == "__main__":
    main()
