"""Generate the labeled evaluation messages (synthetic, AI-written).

Each hand-written seed and each slot template is one "template family".
A family produces several variants (different fake names, amounts, links,
channel framing and, for some, evasion tricks). Families never cross splits,
so near-identical wording can't sit in both dev and test.

Usage:
    python -m eval.generate                       # frozen set (seed 0) -> eval/data/
    python -m eval.generate --seed 7 --out eval/batches/seed_7   # a fresh batch

Shortcut guards: scam and legit messages share the same channel mix, the same
neutral openers/sign-offs, and both carry links and emoji, so none of those
alone separates the labels.
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np

from eval.seeds_legit import LEGIT
from eval.seeds_scam import SCAM

SPLIT_SHARES = {"corpus": 0.30, "dev": 0.25, "test": 0.45}
CHANNELS = ["whatsapp", "sms", "email", "instagram", "messenger"]
CHANNEL_P = [0.35, 0.30, 0.15, 0.10, 0.10]

# Variants per family. Legit gets more so the set is ~2:1 legit to scam.
SCAM_SEED_VARIANTS, SCAM_TEMPLATE_VARIANTS = 5, 10
LEGIT_SEED_VARIANTS, LEGIT_TEMPLATE_VARIANTS = 14, 80

LOW_URGENCY = {"romance scam money request", "investment or crypto scam", "task or like-and-earn scam"}
HARD_NEGATIVES = {"OTP message with do-not-share", "real urgent family message",
                  "college circular or exam-fee deadline", "recruiter outreach", "refund confirmation"}

NAMES = ["Anita", "Rahul", "Meera", "Arjun", "Sam", "Priya", "Tom", "Fatima", "Joseph", "Lisa", "Kiran", "Nisha"]
BANKS = ["Nimbus Bank", "Harbor Bank", "Kestrel Bank", "Orbit Bank", "your bank"]
COURIERS = ["Kestrel Courier", "SwiftPost", "ParcelGo", "the courier"]
STORES = ["ShopMax", "PlayZone", "MegaMart", "app store", "online store"]
COMPANIES = ["Brightline Ltd", "Corvid Supplies", "Tandem Works", "Lumen Traders"]
LINK_WORDS = ["secure", "verify", "pay", "claim", "update", "account", "help", "parcel", "track",
              "portal", "service", "info", "reward", "refund", "login", "my", "app", "orders"]
EMOJI = ["⚠️", "✅", "🙏", "😊", "👍", "📦", "💰", "🔔", "❤️", "🎉"]
OPENERS = ["", "", "", "Hi, ", "Hello, ", "Hey, ", "Dear user, "]
CLOSERS = ["", "", "", " Thanks.", " Regards.", " Sent from my phone", " Cheers."]
SCAM_EVASIONS = ["spacing", "leetspeak", "emoji_padding", "obfuscated_link", "split_phrasing"]
LEGIT_STYLES = ["emoji_padding", "casual_lowercase"]
LEGIT_LINK_CATEGORIES = {"delivery update", "bank transaction alert", "college circular or exam-fee deadline",
                         "government notice", "real promotion", "refund confirmation"}


def _link(rng, legit=False):
    a, b = rng.choice(LINK_WORDS, 2, replace=False)
    code = "".join(rng.choice(list("abcdefghjkmnpqrstuvwxyz23456789"), 6))
    if legit:
        return str(rng.choice([f"https://{a}.example.org/{code}", f"https://app.example.com/{b}/{code}", "[LINK]"]))
    return str(rng.choice([f"https://{a}-{b}.example.com/{code}", f"http://{a}{rng.integers(1, 99)}.test/{b}",
                           f"{a}-{b}.invalid/{code}", f"https://sh.example/{code}", "[LINK]"]))


def _amount(rng):
    n = int(rng.choice([99, 149, 250, 499, 750, 999, 1500, 2500, 4999, 12000]))
    return str(rng.choice([f"Rs {n:,}", f"₹{n:,}", f"£{n:,}", f"${n:,}", f"Rs. {n:,}", f"€{n:,}"]))


def _common(rng, legit):
    return {
        "link": _link(rng, legit), "amount": _amount(rng), "name": str(rng.choice(NAMES)),
        "phone": "[PHONE]", "bank": str(rng.choice(BANKS)), "courier": str(rng.choice(COURIERS)),
        "store": str(rng.choice(STORES)), "company": str(rng.choice(COMPANIES)),
        "code": str(rng.choice([f"{rng.integers(100000, 999999)}", f"INV-{rng.integers(10000, 99999)}"])),
    }


def fill(text: str, slots: dict, rng, legit: bool) -> str:
    """Replace {slot} with a random option (category slots first, then common fakes)."""
    common = _common(rng, legit)
    for _ in range(4):  # slot values can contain further placeholders
        def repl(m):
            key = m.group(1)
            if key in slots:
                return str(rng.choice(slots[key]))
            return common.get(key, m.group(0))
        new = re.sub(r"\{(\w+)\}", repl, text)
        if new == text:
            break
        text = new
    return " ".join(text.split())


# ---------------------------------------------------------------- evasion
def _spacing(text, rng):
    words = [w for w in re.findall(r"[A-Za-z]{5,}", text)]
    for w in rng.choice(words, min(2, len(words)), replace=False) if words else []:
        text = text.replace(w, " ".join(w), 1)
    return text


def _leet(text, rng):
    table = str.maketrans({"a": "4", "e": "3", "o": "0", "i": "1"})
    words = re.findall(r"[a-z]{4,}", text)
    for w in rng.choice(words, min(3, len(words)), replace=False) if words else []:
        text = text.replace(w, w.translate(table), 1)
    return text


def _emoji(text, rng):
    parts = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(f"{p} {rng.choice(EMOJI)}" if rng.random() < 0.6 else p for p in parts)


def _obfuscate_links(text, rng):
    def repl(m):
        url = m.group(0)
        return str(rng.choice([url.replace(".", "[.]"), url.replace("http", "hxxp"), url.replace(".", " dot ")]))
    return re.sub(r"(https?://)?[\w-]+(\.[\w-]+)+(/\S*)?", repl, text)


def _split(text, rng):
    parts = re.split(r"(?<=[.!?,])\s+", text)
    return "\n".join(p.lower() if rng.random() < 0.5 else p for p in parts)


EVADE = {"spacing": _spacing, "leetspeak": _leet, "emoji_padding": _emoji,
         "obfuscated_link": _obfuscate_links, "split_phrasing": _split,
         "casual_lowercase": lambda t, rng: t.lower()}


def frame(text: str, channel: str, rng) -> str:
    """Channel-style framing shared by both labels."""
    text = f"{rng.choice(OPENERS)}{text}{rng.choice(CLOSERS)}".strip()
    if channel == "email" and rng.random() < 0.6:
        subject = " ".join(text.split()[:5]).rstrip(",.!?:")
        text = f"Subject: {subject}\n\n{text}"
    return text


# ---------------------------------------------------------------- families
def _families():
    """Yield (label, category, novelty, family_kind, language, base_text, slots)."""
    for cat, spec in SCAM.items():
        for lang, key in (("en", "seeds"), ("hinglish", "hinglish"), ("manglish", "manglish")):
            for s in spec.get(key, []):
                yield "scam", cat, spec["novelty"], "handwritten", lang, s, spec.get("slots", {})
        for t in spec.get("templates", []):
            yield "scam", cat, spec["novelty"], "template", "en", t, spec.get("slots", {})
    for cat, spec in LEGIT.items():
        for lang, key in (("en", "seeds"), ("hinglish", "hinglish"), ("manglish", "manglish")):
            for s in spec.get(key, []):
                yield "legit", cat, "n/a", "handwritten", lang, s, spec.get("slots", {})
        for t in spec.get("templates", []):
            yield "legit", cat, "n/a", "template", "en", t, spec.get("slots", {})


def _assign_splits(families, rng):
    """Group-aware: shuffle each category's units and deal them into splits.

    A unit is one hand-written seed, or ALL templates of a category together:
    a category's templates share slot phrases, so splitting them apart would
    leak near-identical wording between dev and test.
    """
    units = {}
    for i, (label, cat, _, kind, *_rest) in enumerate(families):
        key = (label, cat, "templates") if kind == "template" else (label, cat, i)
        units.setdefault(key, []).append(i)
    by_cat = {}
    for key, ids in units.items():
        by_cat.setdefault(key[:2], []).append(ids)
    split_of = {}
    for unit_list in by_cat.values():
        order = rng.permutation(len(unit_list))
        n = len(unit_list)
        n_test = max(1, round(n * SPLIT_SHARES["test"]))
        n_dev = max(1, round(n * SPLIT_SHARES["dev"]))
        for j, u in enumerate(order):
            split = "test" if j < n_test else "dev" if j < n_test + n_dev else "corpus"
            for fid in unit_list[u]:
                split_of[fid] = split
    return split_of


def _difficulty(label, cat, novelty, lang, evasion):
    if label == "legit":
        return "hard" if cat in HARD_NEGATIVES or lang != "en" else "easy"
    if lang != "en" or evasion not in ("none", "emoji_padding") or cat in LOW_URGENCY:
        return "hard"
    return "easy" if novelty == "seen" else "medium"


def generate(seed: int = 0) -> list[dict]:
    rng = np.random.default_rng(seed)
    families = list(_families())
    split_of = _assign_splits(families, rng)
    rows, seen_texts = [], set()
    for fid, (label, cat, novelty, kind, lang, base, slots) in enumerate(families):
        legit = label == "legit"
        if kind == "handwritten":
            n = LEGIT_SEED_VARIANTS if legit else SCAM_SEED_VARIANTS
        else:
            n = LEGIT_TEMPLATE_VARIANTS if legit else SCAM_TEMPLATE_VARIANTS
        for v in range(n):
            text = fill(base, slots, rng, legit)
            if legit and cat in LEGIT_LINK_CATEGORIES and rng.random() < 0.3:
                text += f" Details: {_link(rng, legit=True)}"
            evasion = "none"
            if not legit and rng.random() < 0.30:
                evasion = str(rng.choice(SCAM_EVASIONS))
            elif legit and rng.random() < 0.15:
                evasion = str(rng.choice(LEGIT_STYLES))
            if evasion != "none":
                text = EVADE[evasion](text, rng)
            channel = str(rng.choice(CHANNELS, p=CHANNEL_P))
            text = frame(text, channel, rng)
            if text in seen_texts:
                continue
            seen_texts.add(text)
            rows.append({
                "id": f"m{len(rows) + 1:05d}", "text": text, "label": label, "category": cat,
                "split": split_of[fid], "template_family": f"{label[0]}{fid:04d}", "channel": channel,
                "language": lang, "evasion_type": evasion,
                "difficulty": _difficulty(label, cat, novelty, lang, evasion),
                "novelty": novelty, "source": kind,
            })
    return rows


def write_splits(rows: list[dict], out: Path) -> dict[str, Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths = {}
    for split in SPLIT_SHARES:
        paths[split] = out / f"{split}.jsonl"
        with open(paths[split], "w", encoding="utf-8") as f:
            for r in rows:
                if r["split"] == split:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return paths


def load_split(path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="eval/data")
    args = ap.parse_args()
    rows = generate(args.seed)
    paths = write_splits(rows, Path(args.out))
    for split, p in paths.items():
        part = [r for r in rows if r["split"] == split]
        print(f"{split:6s} {len(part):5d} messages ({sum(r['label'] == 'scam' for r in part)} scam) -> {p}")


if __name__ == "__main__":
    main()
