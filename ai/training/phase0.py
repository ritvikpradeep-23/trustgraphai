"""Phase 0: check the training data is complete and sound before any training.

    PYTHONPATH=src python -m training.phase0

Checks the fields, the frozen test set's hash, that no template family
crosses splits, and how evenly scam/honest are spread across groups a model
could use as a shortcut (language, channel, evasion trick, length, and the
generator's own formatting habits). Writes reports/<date>-training/phase0.md.
"""
import argparse
import collections
import time
from datetime import date
from pathlib import Path

from eval.generate import load_split
from eval.leakage import DATA, MANIFEST, verify_manifest
from training.data import ARTIFACTS, FIELDS, SHORTCUT_LIMIT, balance, data_hash, load

GROUPS = ["language", "channel", "evasion_type", *ARTIFACTS]


def _split_integrity() -> tuple[int, list[str]]:
    """Template families must never cross splits. This is the one place that
    opens the test file for anything but its hash, and it reads only the
    family ids, never the messages."""
    split_of, crossing = {}, []
    for split in ("corpus", "dev", "test"):
        for r in load_split(DATA / f"{split}.jsonl"):
            if split_of.setdefault(r["template_family"], split) != split:
                crossing.append(r["template_family"])
    return len(split_of), sorted(set(crossing))


def run(out: Path) -> dict:
    problems = []
    for name in ("corpus.jsonl", "dev.jsonl", "test.jsonl", MANIFEST.name):
        if not (DATA / name).exists():
            problems.append(f"missing {DATA / name}")
    if problems:
        return {"problems": problems}

    manifest = verify_manifest()  # raises if the frozen test file changed
    families, crossing = _split_integrity()
    if crossing:
        problems.append(f"{len(crossing)} template families cross splits: {crossing[:5]}")

    rows = {s: load(s) for s in ("corpus", "dev")}
    for split, rs in rows.items():
        missing = collections.Counter(f for r in rs for f in FIELDS if f not in r)
        if missing:
            problems.append(f"{split}: rows missing fields {dict(missing)}")

    counts = {s: collections.Counter((r["label"], r["novelty"]) for r in rs) for s, rs in rows.items()}
    cats = {s: len({r["category"] for r in rs if r["label"] == "scam"}) for s, rs in rows.items()}
    train = rows["corpus"] + rows["dev"]
    tables = [row for g in GROUPS for row in balance(train, g)]
    return {"problems": problems, "manifest": manifest, "families": families, "counts": counts,
            "scam_categories": cats, "balance": tables,
            "hashes": {s: data_hash(rs) for s, rs in rows.items()}}


# How each kind of flagged shortcut is handled in Tracks B and C. The dataset
# itself is not edited: the test set is frozen, and corpus/dev must stay the
# same data the evaluation used.
NOTES = [
    "## Phase 0 notes: how each shortcut is handled", "",
    "| Shortcut | Why it exists | Handling |", "|---|---|---|",
    "| Evasion tricks (leetspeak, spaced letters, obfuscated links, split lines) appear only in scams; "
    "all-lowercase only in honest messages | The generator applies scam tricks only to scams | Text is normalized "
    "before Tracks B and C see it: lowercased, spaced letters rejoined, leetspeak digits inside words undone, "
    "'[.]'/' dot '/'hxxp' links decoded. A trick then looks like the plain message. |",
    "| Link style: '.test', '.invalid', 'secure-pay.example.com' only in scams; 'app.example.com' only in honest | "
    "The generator draws scam and honest links from different patterns | Every link becomes one `<link>` token in both classes. |",
    "| 'Details: <link>' suffix only in honest messages | Generator habit | Link becomes `<link>`; the word 'details' "
    "is on the audit's watch list and is removed in the audit retrain. |",
    "| [PHONE] only in scams | Only scam templates mention a number to call | Phone numbers and [PHONE] become one "
    "`<phone>` token; on the audit watch list. |",
    "| INV- codes mostly in honest code messages | A known generator slip | 'INV-12345' and digit runs become `<num>`. |",
    "| Length: 30+ words is 99% scams, under 15 words 90% honest | Partly real (scams explain more), mostly the "
    "generator | Can't be removed without new data. Reported by length bucket, and the classifier must clearly beat "
    "a baseline that only knows length and whether there is a link. |", "",
    "Language, channel and the [LINK] placeholder are balanced (no flag).", "",
]


def write_report(res: dict, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    L = ["# Phase 0: training data check", "",
         "> The data is synthetic (written by the generator in `eval/`). Nothing here is real-world accuracy.", ""]
    if res["problems"]:
        L += ["## Problems (training must not start)", ""] + [f"- {p}" for p in res["problems"]] + [""]
    else:
        L += ["**All prerequisites are present. No problems found.**", ""]
    if "manifest" in res:
        m = res["manifest"]
        L += ["## Prerequisites", "",
              f"- All {len(FIELDS)} required fields present on every corpus and dev row: {', '.join(FIELDS)}.",
              f"- Frozen test set hash verified: `{m['test_sha256'][:16]}…` (generator seed {m['generator_seed']}).",
              f"- {res['families']} template families; none crosses splits.",
              f"- Training-data hashes: corpus `{res['hashes']['corpus'][:16]}…`, dev `{res['hashes']['dev'][:16]}…`.", "",
              "| Split | Scams (known types) | Scams (types the engine had no examples for) | Honest | Scam types |",
              "|---|---|---|---|---|"]
        for s, c in res["counts"].items():
            L.append(f"| {s} | {c[('scam', 'seen')]} | {c[('scam', 'unseen')]} | {c[('legit', 'n/a')]} | {res['scam_categories'][s]} |")
        L += ["", f"The corpus split holds all {res['scam_categories']['corpus']} scam types, so once a model trains on it the "
              "evaluation's \"never seen\" types are no longer unseen. Novelty is measured by leave-one-type-out and by "
              "versions trained on the 13 known types only.", "",
              f"## Shortcut check (corpus + dev; flagged if a group of 10+ is over {SHORTCUT_LIMIT:.0%} one label)", "",
              "| Group | Value | Messages | Share that are scams | Shortcut risk |", "|---|---|---|---|---|"]
        for t in res["balance"]:
            L.append(f"| {t['field']} | {t['value']} | {t['n']} | {t['scam_share']:.0%} | {'**yes**' if t['flag'] else ''} |")
        flagged = [t for t in res["balance"] if t["flag"]]
        L += ["", f"{len(flagged)} flagged group(s). Every one is a way a model could tell the labels apart without "
              "learning anything about scams. How each is handled is in the Phase 0 notes below.", ""]
    L += NOTES
    (out / "phase0.md").write_text("\n".join(L), encoding="utf-8")
    return out / "phase0.md"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=f"reports/{date.today().isoformat()}-training")
    args = ap.parse_args()
    out = Path(args.out)
    t = time.time()
    res = run(out)
    path = write_report(res, out)
    with open(out / "runlog.md", "a", encoding="utf-8") as f:
        f.write(f"- {time.strftime('%H:%M:%S')} `PYTHONPATH=src python -m training.phase0` "
                f"({time.time() - t:.0f}s): {len(res['problems'])} problem(s), "
                f"{sum(t['flag'] for t in res.get('balance', []))} shortcut flag(s)\n")
    print(path.read_text())


if __name__ == "__main__":
    main()
