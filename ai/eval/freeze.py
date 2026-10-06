"""Build and freeze the evaluation set: generate, filter leaks, write the manifest.

    python -m eval.freeze            # refuses if a frozen test set already exists
    python -m eval.freeze --force    # deliberately replace it (makes a NEW test set)
"""
import argparse
import collections
import json

from eval.generate import generate, write_splits
from eval.leakage import DATA, MANIFEST, engine_reference_texts, filter_leaks, write_manifest

SEED = 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if MANIFEST.exists() and not args.force:
        raise SystemExit(f"{MANIFEST} exists: the test set is frozen. Use --force only to create a new test set.")

    rows = generate(SEED)
    reference = [r["text"] for r in rows if r["split"] in ("corpus", "dev")] + engine_reference_texts()
    test = [r for r in rows if r["split"] == "test"]
    kept, removed = filter_leaks(test, reference)
    rows = [r for r in rows if r["split"] != "test"] + kept
    paths = write_splits(rows, DATA)
    with open(DATA / "removed_by_leakage.jsonl", "w", encoding="utf-8") as f:
        for r in removed:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    counts = {split: dict(collections.Counter(r["label"] for r in rows if r["split"] == split))
              for split in ("corpus", "dev", "test")}
    manifest = write_manifest(paths["test"], SEED, counts, len(removed))
    print(f"Leakage filter removed {len(removed)} of {len(test)} test messages (similarity > 0.9).")
    for split, c in counts.items():
        print(f"  {split:6s} {c}")
    print(f"Frozen test set: {paths['test']}  sha256 {manifest['test_sha256'][:16]}...")


if __name__ == "__main__":
    main()
