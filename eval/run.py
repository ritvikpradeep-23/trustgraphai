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


def loco_section(run):
    """Leave-one-category-out for every category the engine has reference examples for."""
    from trustgraph.similarity.corpus import SCAM_SCRIPTS
    rng = np.random.default_rng(run.seed)
    setting = "text_only"
    dev_scores, test_scores = run.scores("dev", setting), run.scores("test", setting)
    full_bands = run.bands(setting)
    dev_legit = [(sc, r) for sc, r in zip(dev_scores, run.dev) if r["label"] == "legit"]
    table = []
    for cat in sorted({r["category"] for r in run.test if r["label"] == "scam"}):
        idx = [i for i, r in enumerate(run.test) if r["category"] == cat]
        rows_c, scores_c = [run.test[i] for i in idx], [test_scores[i] for i in idx]
        base = metrics.rate(metrics.hits([s["fused"] for s in scores_c], full_bands["caution"]), rng)
        row = {"category": cat, "n": len(idx), "in_reference_corpus": cat in SCAM_SCRIPTS,
               "recall_full_corpus": base["value"]}
        if cat in SCAM_SCRIPTS:
            reduced = {k: v for k, v in SCAM_SCRIPTS.items() if k != cat}
            with engine.corpus(reduced):
                dev_re = engine.refuse([sc for sc, _ in dev_legit], [r for _, r in dev_legit])
                test_re = engine.refuse(scores_c, rows_c)
            for key in ("fused", "wording"):
                bands = metrics.calibrate([s[key] for s in dev_re])
                r = metrics.rate(metrics.hits([s[key] for s in test_re], bands["caution"]), rng)
                row[f"loco_{key}"], row[f"loco_{key}_lo"], row[f"loco_{key}_hi"] = r["value"], r["lo"], r["hi"]
        else:
            row["loco_fused"] = base["value"]  # never in the corpus: already a held-out category
            row["loco_fused_lo"], row["loco_fused_hi"] = base["lo"], base["hi"]
            row["loco_wording"] = row["loco_wording_lo"] = row["loco_wording_hi"] = float("nan")
        table.append(row)
    run.write_csv("loco.csv", table)
    seen = [t for t in table if t["in_reference_corpus"]]
    summary = {
        "seen_full_corpus_mean": float(np.mean([t["recall_full_corpus"] for t in seen])),
        "seen_left_out_mean": float(np.mean([t["loco_fused"] for t in seen])),
        "seen_left_out_wording_only_mean": float(np.mean([t["loco_wording"] for t in seen])),
        "unseen_mean": float(np.mean([t["loco_fused"] for t in table if not t["in_reference_corpus"]])),
    }
    run.results["loco"] = {"table": table, "summary": summary}
    run.note(f"[loco] known types: {summary['seen_full_corpus_mean']:.1%} with their examples, "
             f"{summary['seen_left_out_mean']:.1%} with them removed "
             f"(wording match alone {summary['seen_left_out_wording_only_mean']:.1%}); "
             f"never-seen types {summary['unseen_mean']:.1%}")


Run.section_loco = loco_section


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
