"""Score a FINAL candidate on the frozen test set, once.

    PYTHONPATH=src python -m training.final_test similarity_v3
    PYTHONPATH=src python -m training.final_test classifier_v1

This is the only training script that reads eval/data/test.jsonl. It checks
the file against its SHA-256 manifest first, uses cut-offs set on dev (never
on test), and refuses to run twice for the same candidate: after a test
result has been seen, the candidate may not change. The current engine is
scored alongside, at its own dev cut-offs, for comparison.

Note: this test set was already looked at in two evaluation reports (never
trained or tuned on); see reports/2026-10-05-training/PLAN.md.
"""
import argparse
import json
import os
import time
from datetime import date
from pathlib import Path

import joblib
import numpy as np

from eval import metrics
from eval.generate import load_split
from eval.leakage import DATA, verify_manifest
from training import scoring
from training.data import load
from trustgraph.classifier import model as clf
from trustgraph.similarity import detector as sim
from trustgraph.similarity.corpus import LEGIT_MESSAGES, SCAM_SCRIPTS

CANDIDATES = Path("models/candidate")


def engine_scores(rows, base, index, classifier=None, weight=0.0):
    _, similarity = scoring.similarity_scores(index, rows, base["flag_keep"])
    extra = clf.scores(classifier, [r["text"] for r in rows]) if classifier else None
    return scoring.fuse(base, similarity, extra, weight)


def build(name: str):
    """(similarity index, classifier bundle or None, weight) for a candidate."""
    bundle = CANDIDATES / name
    if (bundle / "classifier.joblib").exists():
        model = joblib.load(bundle / "classifier.joblib")
        manifest = json.loads((bundle / "manifest.json").read_text())
        # The classifier's cut-offs assume the similarity bundle named in "requires", if any.
        b = next((p.name for p in CANDIDATES.iterdir() if p.name in manifest["requires"]), None)
        index = sim.build_index(*sim.load_corpus(str(CANDIDATES / b / "similarity_corpus.json"))) if b \
            else sim.build_index(SCAM_SCRIPTS, LEGIT_MESSAGES)
        return index, model, model["fusion_weight"]
    return sim.build_index(*sim.load_corpus(str(bundle / "similarity_corpus.json"))), None, 0.0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", help="folder name under models/candidate/")
    ap.add_argument("--out", default=f"reports/{date.today().isoformat()}-training")
    args = ap.parse_args(argv)
    out = Path(args.out)
    result_path = out / f"final_test_{args.candidate}.json"
    if result_path.exists():
        raise SystemExit(f"Refusing: {args.candidate} was already scored on the test set ({result_path}). "
                         "A changed candidate needs a new test set.")
    t0 = time.time()
    manifest = verify_manifest()
    test = load_split(DATA / "test.jsonl")
    dev = load("dev")
    base_test, base_dev = scoring.base_signals("test", test), scoring.base_signals("dev", dev)
    dev_legit = np.array([r["label"] == "legit" for r in dev])

    res = {"candidate": args.candidate, "test_sha256": manifest["test_sha256"], "date": date.today().isoformat()}
    rng_seed = 0
    for name, (index, model, weight) in (("current engine", (sim.build_index(SCAM_SCRIPTS, LEGIT_MESSAGES), None, 0.0)),
                                         (args.candidate, build(args.candidate))):
        bands = metrics.calibrate(engine_scores(dev, base_dev, index, model, weight)[dev_legit])
        s = engine_scores(test, base_test, index, model, weight)
        m = metrics.evaluate(test, [{"s": float(x)} for x in s], "s", bands, rng_seed)
        m["by_language"] = {g["language"]: g["caution"] for g in
                            metrics.by_group(test, [{"s": float(x)} for x in s], "s", bands, "language", seed=rng_seed)}
        res[name] = m
        print(f"[{name}] test recall@Caution {m['recall_caution']['value']:.1%} "
              f"[{m['recall_caution']['lo']:.1%}, {m['recall_caution']['hi']:.1%}], false alarms "
              f"{m['fpr_caution']['value']:.1%}, High false alarms {m['fpr_high']['value']:.1%}")
    out.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(res, indent=1, default=float))
    with open(out / "runlog.md", "a", encoding="utf-8") as f:
        f.write(f"- {time.strftime('%H:%M:%S')} `PYTHONPATH=src python -m training.final_test {args.candidate}` "
                f"(test sha256 {manifest['test_sha256'][:16]}..., {time.time() - t0:.0f}s): ONE-TIME test result written\n")


if __name__ == "__main__":
    main()
