"""Add new examples for the learning routine (learn_cycle.py) to pick up.

    python add_examples.py scam "Your electricity will be cut tonight, call 98xxxxxx" --type "electricity disconnection"
    python add_examples.py honest "Your OTP for the bank login is 482910. Do not share it."
    python add_examples.py --csv new_examples.csv      # columns: text,label[,scam_type]; label = scam or honest
    python add_examples.py --retry-rejected            # give examples from a rejected learning run another go

"honest" is for real messages that were wrongly flagged: learning from those
matters as much as learning new scams. Examples are stored in
data/learning/inbox.jsonl on this computer and used once by the next run.
"""
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

INBOX = Path(__file__).resolve().parent / "data" / "learning" / "inbox.jsonl"
REJECTED = INBOX.with_name("rejected.jsonl")
USED = INBOX.with_name("used.json")
LABELS = {"scam": "scam", "honest": "legit", "legit": "legit", "not_scam": "legit"}


def add(text: str, label: str, scam_type: str | None = None, source: str = "add_examples.py",
        retry: bool = False) -> dict:
    """Append one example to the inbox. label: scam, honest (= legit / not_scam)."""
    text = " ".join(str(text).split())
    if not text:
        raise ValueError("empty text")
    if label not in LABELS:
        raise ValueError(f"label must be one of {sorted(LABELS)}, got {label!r}")
    item = {"text": text, "label": LABELS[label], "scam_type": (scam_type or "").strip() or None,
            "source": source, "added": datetime.now().isoformat(timespec="seconds")}
    if retry:
        item["retry"] = True  # tested once already: learned again, but not counted as "new" in the catch rate
    INBOX.parent.mkdir(parents=True, exist_ok=True)
    with open(INBOX, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
    return item


def retry_rejected() -> int:
    """Put the examples from rejected learning runs back in the inbox (each example is
    otherwise used once). Read data/learning/rejected.jsonl first and delete lines you don't trust."""
    if not REJECTED.exists():
        return 0
    items = [json.loads(line) for line in REJECTED.read_text(encoding="utf-8").splitlines() if line.strip()]
    import learn_cycle  # same key as the learning routine, so these are no longer "used"
    keys = {learn_cycle.key(it["text"], it["label"]) for it in items}
    if USED.exists():
        USED.write_text(json.dumps([k for k in json.loads(USED.read_text(encoding="utf-8")) if k not in keys]),
                        encoding="utf-8")
    for it in items:
        add(it["text"], "honest" if it["label"] == "legit" else "scam", it.get("scam_type"), source="retry",
            retry=True)
    REJECTED.unlink()
    return len(items)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("label", nargs="?", choices=["scam", "honest"])
    ap.add_argument("text", nargs="?")
    ap.add_argument("--type", help="scam type, e.g. 'fake e-challan' (optional)")
    ap.add_argument("--csv", help="CSV file with columns text,label[,scam_type]")
    ap.add_argument("--retry-rejected", action="store_true", help="re-queue examples from rejected learning runs")
    args = ap.parse_args(argv)
    if args.retry_rejected:
        print(f"Put {retry_rejected()} rejected example(s) back in {INBOX}.")
    elif args.csv:
        with open(args.csv, newline="", encoding="utf-8") as f:
            n = 0
            for row in csv.DictReader(f):
                add(row["text"], row["label"].strip().lower(), row.get("scam_type"), source=f"csv {Path(args.csv).name}")
                n += 1
        print(f"Added {n} examples to {INBOX}")
    elif args.label and args.text:
        add(args.text, args.label, args.type)
        print(f"Added 1 {args.label} example to {INBOX}. The next learning run will use it.")
    else:
        ap.error("give a label and a text, or --csv")


if __name__ == "__main__":
    main()
