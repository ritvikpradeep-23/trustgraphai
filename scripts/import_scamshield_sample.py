"""Fetch a pinned-source, redacted ScamShield sample; emit JSON for review.

This script never writes files or seeds the database. The corpus declares MIT.
Only corpus-authored synthetic scam rows are used; no private user reports or
upstream mixed-license real-message datasets are copied into the public demo.
"""
import argparse
from collections import Counter, defaultdict, deque
import hashlib
import json
from pathlib import Path
import re
import sys
import httpx

ROOT = Path(__file__).resolve().parents[1]
DATASET = "sidzzz07/scamshield-dataset"
REVISION = "059dee884476a45e380808e68d09e74baff67291"

def normalize(text):
    return " ".join(re.findall(r"\w+", text.casefold()))

def redact(text):
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", "[email redacted]", text)
    text = re.sub(r"(?i)\b(?:https?://|www\.)[^\s<>]+|\b(?:[\w-]+\.)+(?:com|net|org|info|in|co|xyz|live|top|online|bank|click|me|io|site)(?:/[^\s<>]*)?", "https://scamshield-demo.invalid", text)
    text = re.sub(r"\+?\d[\d ()-]{7,}\d", "[phone redacted]", text)
    return " ".join(text.split())

def skeleton(text):
    # Number-only variants must not be counted as unique scam examples.
    return re.sub(r"\d+", "number", normalize(text))

def fetch():
    rows = []
    # Respect the host's network proxy configuration; TLS verification stays on.
    with httpx.Client(timeout=30) as client:
        info = client.get(f"https://huggingface.co/api/datasets/{DATASET}")
        info.raise_for_status()
        if info.json()["sha"] != REVISION or info.json()["cardData"].get("license") != "mit":
            raise RuntimeError("Dataset revision/license changed; review provenance before import")
        response = client.get(f"https://huggingface.co/datasets/{DATASET}/resolve/{REVISION}/train.jsonl", follow_redirects=True)
        response.raise_for_status()
        if hashlib.sha256(response.content).hexdigest() != "418b1d7af29945135284d4293230c75b26c3bccd3dda5382caf730fbc0e49cbf":
            raise RuntimeError("Pinned training file checksum mismatch")
        for line in response.text.split("\n"):
            if line:
                row = json.loads(line)
                row["origin_split"] = "train"
                if row["source_dataset"] == "Synthetic_Tier_C" and row["is_scam"] == 1:
                    rows.append(row)
        check = client.get(f"https://huggingface.co/api/datasets/{DATASET}")
        check.raise_for_status()
        if check.json()["sha"] != REVISION:
            raise RuntimeError("Source changed during import")
    return rows

def select_sample(rows, count=264):
    existing = json.loads((ROOT / "data/demo_scam_patterns.json").read_text(encoding="utf-8"))
    seen = {skeleton(p["text"]) for p in existing}
    groups = defaultdict(deque)
    rejected = Counter()
    for row in sorted(rows, key=lambda row: row["id"]):
        text = redact(row["text"])
        category = row["head2_scam_intent"]
        key = skeleton(text)
        if row["is_scam"] != 1 or row["source_dataset"] != "Synthetic_Tier_C":
            rejected["not_synthetic_scam"] += 1
        elif category in ("Legitimate / Benign", "General Spam / Telemarketing"):
            rejected["benign_or_general_spam"] += 1
        elif len(normalize(text)) < 24:
            rejected["too_short"] += 1
        elif key in seen:
            rejected["duplicate_or_number_only_variant"] += 1
        else:
            seen.add(key)
            groups[(category, row["language"])].append({
                "id": "scamshield_v1_" + row["id"], "title": category,
                "text": text, "language": row["language"],
                "source_dataset": DATASET, "source_revision": REVISION,
                "source_row_id": row["id"], "source_split": row["origin_split"],
                "source_kind": "Synthetic_Tier_C", "license": "MIT",
                "redacted": True,
            })
    selected = []
    keys = sorted(groups)
    while len(selected) < count and any(groups.values()):
        for key in keys:
            if groups[key] and len(selected) < count:
                selected.append(groups[key].popleft())
    if len(selected) < count:
        raise RuntimeError(f"Only {len(selected)} unique non-number-only scam examples available; do not pad the count")
    digest = hashlib.sha256(json.dumps(selected, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {"patterns": selected, "provenance": {
        "dataset": DATASET, "revision": REVISION, "license": "MIT",
        "source_rows_checked": len(rows), "imported": len(selected),
        "rejected": dict(rejected), "selection_sha256": digest,
        "categories": dict(Counter(p["title"] for p in selected)),
        "languages": dict(Counter(p["language"] for p in selected)),
        "selection": "Sorted source IDs, round-robin category/language; exact normalized and number-only variants removed after redaction. Synthetic scam rows only; benign and general-spam classes excluded."
    }}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--compact", action="store_true", help="Emit compact reviewed message rows; no file writes")
    args = parser.parse_args()
    rows = fetch()
    if args.inspect:
        print(json.dumps({"sources": dict(Counter(r["source_dataset"] for r in rows)), "scam_sources": dict(Counter(r["source_dataset"] for r in rows if r["is_scam"] == 1))}))
        sys.exit(0)
    result = select_sample(rows)
    if args.compact:
        print(json.dumps({"rows": [[p["source_row_id"], p["title"], p["language"], p["text"]] for p in result["patterns"]], "provenance": result["provenance"]}, ensure_ascii=False))
    else:
        print(json.dumps(result["provenance"] if args.summary else result, ensure_ascii=False))
