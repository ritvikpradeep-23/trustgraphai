"""Turn the public email corpora into learning datasets plus held-out email check sets (real data).

    python scripts/import_email_datasets.py

Source: "Phishing Email Curated Datasets" (Zenodo 8339691, CC BY 4.0), via the byte-identical
Hugging Face mirror kudzaiprichard/aura-phishing-email-corpus. Download into eval/external/email/
(gitignored), MD5s as published:
  Nazario_5.csv     45db8330ea4aabbf72f5199949ae03e5   1,565 phishing (Nazario) + 1,500 honest
  Nigerian_5.csv    edfbbb89c40e7447f47867bcc82e72f9   3,332 advance-fee fraud + 2,999 honest

Each email becomes "Subject: ...\n\n<body>", cut to MAX_CHARS. Links become
link.invalid, email addresses [email], and long digit runs (phones, accounts) [number].
Near-duplicates (same first 200 normalized characters) are kept once. Every email is put
in exactly one place, chosen by a hash of its text:
  eval/external/email/design.jsonl    for designing rules; its misses may be read
  eval/external/email/holdout.jsonl   scored before and after only; never read
  data/learning/datasets/<date>_email_public.csv   the learning routine, 300 rows per run
"""
import csv
import hashlib
import json
import random
import re
import sys
from pathlib import Path

AI = Path(__file__).resolve().parents[1]
RAW = AI / "eval" / "external" / "email"
LEARN_FILE = AI / "data" / "learning" / "datasets" / "2026-10-07_email_public.csv"
MAX_CHARS = 1000
# per (source, label): how many go to design / holdout / learning
SIZES = {"phishing": (100, 100, 225), "advance-fee fraud": (100, 100, 135), "honest": (200, 200, 540)}

URL = re.compile(r"(https?://|www\.)\S+|\b[\w.-]+\.(com|net|org|info|biz|ru|cn|co\.uk|in)(/\S*)?\b", re.I)
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(\.[\w-]+)+\b")
DIGITS = re.compile(r"(?<![\w$£€])\+?\d[\d\s().-]{7,}\d")
QP = re.compile(r"=([0-9A-F]{2})")


def clean(subject: str, body: str) -> str:
    def tidy(t):
        t = QP.sub(lambda m: chr(int(m.group(1), 16)), t or "")
        t = EMAIL.sub("[email]", t)
        t = URL.sub("link.invalid", t)
        t = DIGITS.sub("[number]", t)
        return " ".join(t.split())
    subject, body = tidy(subject), tidy(body)
    text = f"Subject: {subject}\n\n{body}" if subject else body
    return text[:MAX_CHARS].rsplit(" ", 1)[0] if len(text) > MAX_CHARS else text


def read(name: str, kinds: dict[str, str]) -> list[dict]:
    csv.field_size_limit(10**9)
    with open(RAW / name, encoding="utf-8", errors="replace", newline="") as f:
        return [{"text": clean(r["subject"], r["body"]), "kind": kinds[r["label"]], "source": name}
                for r in csv.DictReader(f)]


def main():
    rows = (read("Nazario_5.csv", {"1": "phishing", "0": "honest"})
            + read("Nigerian_5.csv", {"1": "advance-fee fraud", "0": "honest"}))
    seen, unique = set(), []
    for r in rows:
        key = re.sub(r"\W+", "", r["text"].lower())[:200]
        if len(r["text"]) >= 80 and key not in seen:
            seen.add(key)
            unique.append(r)
    out = {"design": [], "holdout": [], "learn": []}
    for kind, sizes in SIZES.items():
        pool = sorted((r for r in unique if r["kind"] == kind),
                      key=lambda r: hashlib.sha256(r["text"].encode()).hexdigest())
        if len(pool) < sum(sizes):
            sys.exit(f"only {len(pool)} {kind} emails, need {sum(sizes)}")
        for part, (start, n) in zip(out, ((0, sizes[0]), (sizes[0], sizes[1]), (sizes[0] + sizes[1], sizes[2]))):
            out[part] += pool[start:start + n]

    for part in ("design", "holdout"):
        with open(RAW / f"{part}.jsonl", "w", encoding="utf-8") as f:
            for i, r in enumerate(out[part]):
                f.write(json.dumps({"id": f"email_{part}{i:03d}", "text": r["text"],
                                    "label": "legit" if r["kind"] == "honest" else "scam",
                                    "group": r["kind"], "source": r["source"], "synthetic": False}) + "\n")
    learn = out["learn"]
    random.Random(7).shuffle(learn)  # each 300-row run gets a mix of all three kinds
    LEARN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEARN_FILE, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["text", "label", "scam_type"])
        for r in learn:
            w.writerow([r["text"], "honest" if r["kind"] == "honest" else "scam",
                        "" if r["kind"] == "honest" else f"email {r['kind']}"])
    for part, rs in out.items():
        print(part, len(rs), {k: sum(r["kind"] == k for r in rs) for k in SIZES})


if __name__ == "__main__":
    main()
