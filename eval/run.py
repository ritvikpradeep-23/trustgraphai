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

ABLATION = [("similarity", "similarity signal (wording match + red flags)"), ("flags", "red-flag rules only"),
            ("wording", "wording match only"), ("anomaly", "anomaly only"), ("fused", "all four signals fused")]


def _score_table(run, setting: str, keys) -> list[dict]:
    """Each score calibrated on its own dev legit scores (matched false-alarm rate), measured on test."""
    rows = []
    dev_s, test_s = run.scores("dev", setting), run.scores("test", setting)
    for key, label in keys:
        bands = metrics.calibrate([sc[key] for sc, r in zip(dev_s, run.dev) if r["label"] == "legit"])
        m = metrics.evaluate(run.test, test_s, key, bands, run.seed)
        rows.append({"setting": setting, "score": key, "what": label,
                     "recall_caution": m["recall_caution"]["value"], "recall_caution_lo": m["recall_caution"]["lo"],
                     "recall_caution_hi": m["recall_caution"]["hi"], "recall_high": m["recall_high"]["value"],
                     "recall_caution_unseen": m["recall_caution_unseen"]["value"],
                     "test_false_alarms_caution": m["fpr_caution"]["value"], "test_false_alarms_high": m["fpr_high"]["value"],
                     "roc_auc": m["roc_auc"], "pr_auc": m["pr_auc"]})
    return rows


def ablation_section(run):
    table = _score_table(run, "text_only", ABLATION)
    run.write_csv("ablation.csv", table)
    meta = []
    for setting in engine.SETTINGS:
        meta += _score_table(run, setting, [("fused", "all four signals fused"), ("anomaly", "anomaly only")])
    run.write_csv("metadata_settings.csv", meta)
    run.results["ablation"] = table
    run.results["metadata_settings"] = meta
    for t in table:
        run.note(f"[ablation] {t['what']:<45s} recall@Caution {t['recall_caution']:.1%}  ROC-AUC {t['roc_auc']:.3f}")
    for t in meta:
        if t["score"] == "fused":
            run.note(f"[metadata] {t['setting']:<16s} recall@Caution {t['recall_caution']:.1%}  "
                     f"false alarms {t['test_false_alarms_caution']:.1%}  ROC-AUC {t['roc_auc']:.3f}")


Run.section_ablation = ablation_section

GROUP_FIELDS = ("category", "language", "evasion_type", "channel")


def errors_section(run, worst: int = 25):
    setting = "text_only"
    bands = run.bands(setting)
    scores = run.scores("test", setting)
    pairs = list(zip(run.test, scores))
    flagged = lambda sc: bool(metrics.hits([sc["fused"]], bands["caution"])[0])
    fn = sorted([(r, sc) for r, sc in pairs if r["label"] == "scam" and not flagged(sc)], key=lambda p: p[1]["fused"])
    fp = sorted([(r, sc) for r, sc in pairs if r["label"] == "legit" and flagged(sc)], key=lambda p: -p[1]["fused"])

    def describe(r, sc):
        return {"id": r["id"], "category": r["category"], "novelty": r["novelty"], "language": r["language"],
                "evasion_type": r["evasion_type"], "channel": r["channel"], "fused": round(sc["fused"], 3),
                "wording": round(sc["wording"], 3), "flags": round(sc["flags"], 3), "anomaly": round(sc["anomaly"], 3),
                "text": r["text"], "engine_explanation": engine.explain(r, setting)}

    worst_fn = [describe(*p) for p in fn[:worst]]
    worst_fp = [describe(*p) for p in fp[:worst]]
    run.write_csv("false_negatives_worst.csv", worst_fn)
    run.write_csv("false_positives_worst.csv", worst_fp)

    groups = []
    for kind, errs, label in (("missed scam", fn, "scam"), ("false alarm", fp, "legit")):
        totals = {}
        for r in run.test:
            if r["label"] == label:
                for f in GROUP_FIELDS:
                    totals[(f, r[f])] = totals.get((f, r[f]), 0) + 1
        counts = {}
        for r, _ in errs:
            for f in GROUP_FIELDS:
                counts[(f, r[f])] = counts.get((f, r[f]), 0) + 1
        for (f, v), c in sorted(counts.items(), key=lambda kv: -kv[1]):
            groups.append({"error": kind, "field": f, "value": v, "errors": c, "of": totals[(f, v)],
                           "rate": round(c / totals[(f, v)], 3)})
    run.write_csv("error_groups.csv", groups)
    run.results["errors"] = {"n_false_negatives": len(fn), "n_false_positives": len(fp),
                             "worst_false_negatives": worst_fn, "worst_false_positives": worst_fp, "groups": groups}
    run.note(f"[errors] {len(fn)} missed scams, {len(fp)} false alarms on the frozen test set (text only)")
    for g in [g for g in groups if g["field"] in ("language", "evasion_type")]:
        run.note(f"[errors]   {g['error']:<11s} {g['field']}={g['value']:<16s} {g['errors']}/{g['of']} ({g['rate']:.0%})")


Run.section_errors = errors_section


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
