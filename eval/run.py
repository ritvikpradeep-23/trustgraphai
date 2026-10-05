"""Run the TrustGraph evaluation and write reports/<date>/.

    PYTHONPATH=src python -m eval.run                 # everything
    PYTHONPATH=src python -m eval.run --only metrics  # one section
    PYTHONPATH=src python -m eval.run --batch-seed 7  # also score a fresh generated batch

The frozen test set (eval/data/test.jsonl) is checked against its manifest
hash first. Thresholds are calibrated on dev legit messages and written to
reports/ only; models/ and data/ are never touched. All data is synthetic.
"""
import argparse
import csv
import json
import time
from datetime import date
from pathlib import Path

import numpy as np

from eval import engine, metrics
from eval.generate import load_split
from eval.leakage import DATA, verify_manifest

SECTIONS = ["metrics", "loco", "ablation", "errors", "report_once", "sms"]


class Run:
    def __init__(self, out: Path, seed: int):
        self.out, self.seed = out, seed
        self.out.mkdir(parents=True, exist_ok=True)
        self.log = []
        self.results = {}
        self.manifest = verify_manifest()
        self.dev = load_split(DATA / "dev.jsonl")
        self.test = load_split(DATA / "test.jsonl")
        self.corpus_split = load_split(DATA / "corpus.jsonl")
        self._scores = {}

    def note(self, line: str):
        stamp = time.strftime("%H:%M:%S")
        self.log.append(f"- {stamp} {line}")
        print(line)

    def scores(self, split: str, setting: str) -> list[dict]:
        """Cached engine scores for a split under a metadata setting."""
        key = (split, setting)
        if key not in self._scores:
            t = time.time()
            self._scores[key] = engine.score_rows(getattr(self, split), setting)
            self.note(f"scored {split} ({len(self._scores[key])} messages, {setting}) in {time.time() - t:.0f}s")
        return self._scores[key]

    def bands(self, setting: str, key: str = "fused") -> dict:
        legit = [sc[key] for sc, r in zip(self.scores("dev", setting), self.dev) if r["label"] == "legit"]
        return metrics.calibrate(legit)

    def write_csv(self, name: str, rows: list[dict]):
        if not rows:
            return
        with open(self.out / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    # ------------------------------------------------------------ sections
    def section_metrics(self):
        setting = "text_only"
        bands = self.bands(setting)
        (self.out / "thresholds.json").write_text(json.dumps({setting: bands}, indent=2))
        test_scores = self.scores("test", setting)
        head = metrics.evaluate(self.test, test_scores, "fused", bands, self.seed)
        per_cat = metrics.by_group(self.test, test_scores, "fused", bands, "category", seed=self.seed)
        legit_cat = metrics.by_group(self.test, test_scores, "fused", bands, "category", label="legit", seed=self.seed)
        groups = {f: metrics.by_group(self.test, test_scores, "fused", bands, f, seed=self.seed)
                  for f in ("language", "evasion_type", "channel", "difficulty")}
        self.write_csv("per_category.csv", per_cat)
        self.write_csv("legit_false_alarms_by_category.csv", legit_cat)
        for f, t in groups.items():
            self.write_csv(f"recall_by_{f}.csv", t)
        self.results["metrics"] = {"setting": setting, "headline": head, "per_category": per_cat,
                                   "legit_by_category": legit_cat, "groups": groups}
        r, f = head["recall_caution"], head["fpr_caution"]
        self.note(f"[metrics] text only: recall@Caution {r['value']:.1%} [{r['lo']:.1%}, {r['hi']:.1%}], "
                  f"false alarms {f['value']:.1%}, ROC-AUC {head['roc_auc']:.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=SECTIONS, action="append")
    ap.add_argument("--seed", type=int, default=0, help="bootstrap seed")
    ap.add_argument("--out", default=f"reports/{date.today().isoformat()}")
    args = ap.parse_args()
    run = Run(Path(args.out), args.seed)
    run.note(f"frozen test set verified: sha256 {run.manifest['test_sha256'][:16]}...")
    for name in args.only or SECTIONS:
        fn = getattr(run, f"section_{name}", None)
        if fn is None:
            run.note(f"[{name}] not built yet, skipped")
            continue
        fn()
    (run.out / "results.json").write_text(json.dumps(run.results, indent=1, default=float))
    (run.out / "runlog.md").write_text("# Run log\n\n" + "\n".join(run.log) + "\n")


if __name__ == "__main__":
    main()
