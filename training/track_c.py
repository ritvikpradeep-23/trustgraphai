"""Track C: a supervised text classifier as a fifth signal.

    PYTHONPATH=src python -m training.track_c

Trained on the corpus split only. Settings are tuned with group-aware
cross-validation (template families never split across folds) on corpus+dev;
dev then chooses the fusion weight and is where everything is compared, at
each candidate's own matched ~10% / ~1% dev false-alarm cut-offs.

Evaluated three ways:
  (a) random 5-fold CV on the corpus split: near-copies from the same template
      family land on both sides, so this is the "in-distribution" number
  (b) dev: every dev template family is unseen in training
  (c) leave-one-type-out: for each of the 29 scam types, retrain from scratch
      (vectorizer included) without that type and measure dev recall on it

Plus the shortcut audit, a trivial baseline, a "13 known types only" version
scored on the other 16, and the engine with and without the classifier.
Writes reports/<date>-training/track_c* and models/candidate/classifier_v1/.
"""
import argparse
import json
import os
import re
import tempfile
import time
from datetime import date
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from eval import metrics
from eval.generate import BANKS, COMPANIES, COURIERS, NAMES, STORES
from training import scoring
from training.bundle import live_bands, write_bundle
from training.data import data_hash, group_folds, labels, length_bucket, load
from training.track_b import write_csv
from trustgraph.classifier import detector as clf_detector
from trustgraph.classifier import model as clf
from trustgraph.similarity import detector as sim
from trustgraph.textnorm import readable

SEED = 0
C_GRID = [0.1, 0.3, 1.0, 3.0, 10.0]
WEIGHTS = [0.3, 0.5, 1.0]
BUNDLE_B = Path("models/candidate/similarity_v3")  # Track B retry

# Shortcut audit watch list: words that describe the generator, not scams.
WATCH = {
    "marker": {"zzlink", "zzphone", "zzamount", "zznum"},
    "channel": {"subject", "whatsapp", "sms", "email", "instagram", "messenger"},
    "greeting or sign-off": {"hi", "hello", "hey", "dear", "user", "thanks", "regards", "cheers", "sent", "details"},
    "brand or name": {w.lower() for x in BANKS + COURIERS + STORES + COMPANIES + NAMES for w in re.findall(r"\w+", x)}
                     - {"the", "your", "bank", "courier", "store", "online", "app", "ltd"},
    "language marker": {"hai", "hain", "aap", "aapka", "aapke", "karein", "karo", "ke", "ki", "ko", "se", "mein",
                        "ka", "nahi", "aanu", "ningalude", "ningal", "il", "ninnu", "cheyyuka", "undu", "ee", "oru"},
}


def watch_kind(term: str) -> str:
    for kind, words in WATCH.items():
        if any(w in words for w in term.split()):
            return kind
    return ""


def texts_y(rows):
    return [r["text"] for r in rows], labels(rows)


def train(rows, c, removed=(), seed=SEED) -> dict:
    texts, y = texts_y(rows)
    return clf.fit(texts, y, c, group_folds(rows, k=5, seed=seed), removed, seed)


def tune_c(rows) -> tuple[float, list[dict]]:
    """Group-aware 5-fold CV on corpus+dev: mean ROC-AUC per C."""
    texts, y = texts_y(rows)
    prepared = [clf.prepare(t) for t in texts]
    table = []
    for c in C_GRID:
        aucs = []
        for tr, va in group_folds(rows, k=5, seed=SEED):
            vec, lr = clf._fit_once([prepared[i] for i in tr], y[tr], c, SEED)
            aucs.append(roc_auc_score(y[va], lr.decision_function(vec.transform([prepared[i] for i in va]))))
        table.append({"C": c, "group_cv_roc_auc": float(np.mean(aucs)), "sd": float(np.std(aucs))})
    best = max(table, key=lambda t: t["group_cv_roc_auc"])["C"]
    return best, table


def cv_recall(rows, c, folds) -> dict:
    """Recall at matched ~10% false alarms using out-of-fold scores."""
    texts, y = texts_y(rows)
    oof = np.zeros(len(rows))
    for tr, va in folds:
        b = clf.fit([texts[i] for i in tr], y[tr], c, group_folds([rows[i] for i in tr], 5, SEED))
        oof[va] = clf.scores(b, [texts[i] for i in va])
    return scoring.compare(rows, oof, SEED)


def random_folds(n, k=5, seed=SEED):
    idx = np.random.default_rng(seed).permutation(n)
    return [(np.setdiff1d(idx, part), part) for part in np.array_split(idx, k)]


def similarity_index(on_top_of_b: bool):
    if on_top_of_b:
        scams, legit, norm = sim.load_corpus(str(BUNDLE_B / "similarity_corpus.json"))
        return sim.build_index(scams, legit, norm), scams, legit, norm
    from trustgraph.similarity.corpus import LEGIT_MESSAGES, SCAM_SCRIPTS
    return sim.build_index(SCAM_SCRIPTS, LEGIT_MESSAGES, False), SCAM_SCRIPTS, LEGIT_MESSAGES, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=f"reports/{date.today().isoformat()}-training")
    args = ap.parse_args()
    out = Path(args.out)
    t0 = time.time()
    corpus, dev = load("corpus"), load("dev")
    dev_texts = [r["text"] for r in dev]
    is_legit = np.array([r["label"] == "legit" for r in dev])
    base = scoring.base_signals("dev", dev)
    sms = scoring.sms_rows()
    sms_base = scoring.base_signals("sms", sms) if sms else None
    unseen = {r["category"] for r in dev if r["label"] == "scam" and r["novelty"] == "unseen"}

    # The classifier sits on top of Track B's examples if Track B was adopted.
    b_verdict = json.loads((BUNDLE_B / "manifest.json").read_text())["dev_metrics"]["verdict"] if BUNDLE_B.exists() else "none"
    on_b = b_verdict.startswith("adopt")
    index, sim_scams, sim_legit, sim_norm = similarity_index(on_b)
    _, dev_sim = scoring.similarity_scores(index, dev, base["flag_keep"])
    engine_without = scoring.fuse(base, dev_sim)
    sms_sim = scoring.similarity_scores(index, sms, sms_base["flag_keep"])[1] if sms else None

    # 1. Regularization, by group-aware CV on corpus + dev.
    best_c, c_table = tune_c(corpus + dev)
    print(f"[tune] C={best_c}", c_table)

    # 2. Final model on the corpus split.
    model = train(corpus, best_c)
    dev_clf = clf.scores(model, dev_texts)

    # 3. Fusion weight on dev, and the engine with vs without the classifier.
    results = {"engine without classifier": scoring.compare(dev, engine_without, SEED),
               "classifier alone": scoring.compare(dev, dev_clf, SEED)}
    for w in WEIGHTS:
        results[f"engine + classifier (weight {w})"] = scoring.compare(dev, scoring.fuse(base, dev_sim, dev_clf, w), SEED)
    weight = max(WEIGHTS, key=lambda w: (results[f"engine + classifier (weight {w})"]["recall_caution"]["value"], -w))
    model["fusion_weight"] = weight
    chosen = f"engine + classifier (weight {weight})"

    # Trivial baseline: message length and whether there is a link, nothing else.
    def simple(rows):
        return np.array([[np.log1p(len(r["text"].split())), float("zzlink" in clf.prepare(r["text"]))] for r in rows])
    yb = labels(corpus)
    lr = LogisticRegression(class_weight="balanced").fit(simple(corpus), yb)
    results["baseline: length + has link"] = scoring.compare(dev, lr.decision_function(simple(dev)), SEED)

    sms_res = {}
    if sms:
        sms_clf = clf.scores(model, [r["text"] for r in sms])
        sms_res["engine without classifier"] = scoring.sms_false_alarms(
            scoring.fuse(sms_base, sms_sim), sms, results["engine without classifier"]["thresholds"], SEED)
        sms_res[chosen] = scoring.sms_false_alarms(
            scoring.fuse(sms_base, sms_sim, sms_clf, weight), sms, results[chosen]["thresholds"], SEED)
        sms_res["classifier alone"] = scoring.sms_false_alarms(sms_clf, sms, results["classifier alone"]["thresholds"], SEED)
    table = [scoring.summary_row(k, v, sms_res.get(k)) for k, v in results.items()]
    for row in table:
        print(f"[dev] {row['candidate']:38s} recall {row['recall_caution']:.1%}  fpr {row['fpr_caution']:.1%}  "
              f"auc {row['roc_auc']:.3f}  sms {row.get('real_sms_false_alarms', float('nan')):.1%}")

    # 4. Shortcut audit: strongest coefficients and the watch list.
    names = clf.feature_names(model)
    coef = model["model"].coef_[0]
    order = np.argsort(coef)
    top = {"toward scam": [order[::-1][:50]], "toward honest": [order[:50]]}
    audit_rows = []
    for direction, (idx,) in top.items():
        for rank, j in enumerate(idx, 1):
            block, term = names[j]
            audit_rows.append({"direction": direction, "rank": rank, "block": block, "term": readable(term),
                               "coefficient": float(coef[j]), "flag": watch_kind(term) if block == "words" else
                               ("marker" if any(m in term for m in WATCH["marker"]) else "")})
    flagged_words = sorted({w for r in audit_rows if r["flag"] and r["block"] == "words"
                            for w in r["term"].replace("<link>", "zzlink").replace("<phone>", "zzphone")
                            .replace("<amount>", "zzamount").replace("<number>", "zznum").split()
                            if watch_kind(w)})
    audited = train(corpus, best_c, removed=tuple(flagged_words))
    audited_clf = clf.scores(audited, dev_texts)
    audit_cmp = {"classifier alone, flagged words removed": scoring.compare(dev, audited_clf, SEED),
                 "engine + classifier, flagged words removed": scoring.compare(
                     dev, scoring.fuse(base, dev_sim, audited_clf, weight), SEED)}
    table += [scoring.summary_row(k, v) for k, v in audit_cmp.items()]
    by_group = []
    bands_alone = results["classifier alone"]["thresholds"]
    for field, get in (("evasion_type", lambda r: r["evasion_type"]), ("length", lambda r: length_bucket(r["text"])),
                       ("language", lambda r: r["language"])):
        groups = {}
        for i, r in enumerate(dev):
            groups.setdefault((get(r), r["label"]), []).append(i)
        for (value, label), idx in sorted(groups.items()):
            rate = float(metrics.hits(dev_clf[idx], bands_alone["caution"]).mean())
            by_group.append({"field": field, "value": value, "label": label, "n": len(idx),
                             "flagged_by_classifier_alone": rate})

    # 5. Three ways: (a) random CV on corpus, (b) dev (above), (c) leave-one-type-out.
    three = {"(a) random 5-fold CV on corpus (in-distribution)": cv_recall(corpus, best_c, random_folds(len(corpus))),
             "(a2) group 5-fold CV on corpus (families held out)": cv_recall(corpus, best_c, group_folds(corpus, 5, SEED)),
             "(b) dev (families held out)": results["classifier alone"]}
    loco_rows = []
    rng = np.random.default_rng(SEED)
    for cat in sorted({r["category"] for r in dev if r["label"] == "scam"}):
        m = train([r for r in corpus if r["category"] != cat or r["label"] == "legit"], best_c)
        idx = np.where(is_legit | np.array([r["category"] == cat for r in dev]))[0]
        rows = [dev[i] for i in idx]
        alone = clf.scores(m, [r["text"] for r in rows])
        cat_index = sim.build_index({k: v for k, v in sim_scams.items() if k != cat}, sim_legit, sim_norm) \
            if cat in sim_scams else index
        sub = {k: v[idx] for k, v in base.items()}
        eng = scoring.fuse(sub, scoring.similarity_scores(cat_index, rows, sub["flag_keep"])[1], alone, weight)
        eng_wo = scoring.fuse(sub, scoring.similarity_scores(cat_index, rows, sub["flag_keep"])[1])
        legit_mask = np.array([r["label"] == "legit" for r in rows])
        row = {"category": cat, "n": int((~legit_mask).sum()), "unseen_in_evaluation": cat in unseen}
        for key, s in (("classifier_alone", alone), ("engine_with_classifier", eng), ("engine_without", eng_wo)):
            bands = metrics.calibrate(s[legit_mask])
            row[key] = metrics.rate(metrics.hits(s[~legit_mask], bands["caution"]), rng)["value"]
        loco_rows.append(row)
        print(f"[loco] {cat:45s} alone {row['classifier_alone']:.0%}  engine+clf {row['engine_with_classifier']:.0%}  "
              f"engine {row['engine_without']:.0%}")
    loco_mean = {k: float(np.mean([r[k] for r in loco_rows]))
                 for k in ("classifier_alone", "engine_with_classifier", "engine_without")}
    three["(c) leave-one-type-out, mean over 29 types"] = loco_mean["classifier_alone"]

    # 6. Clean novelty check: trained without the 16 types, scored on them.
    known = train([r for r in corpus if r["label"] == "legit" or r["category"] not in unseen], best_c)
    known_clf = clf.scores(known, dev_texts)
    unseen_mask = np.array([r["label"] == "scam" and r["category"] in unseen for r in dev])
    novelty = {}
    for name, s in (("engine without classifier", engine_without),
                    ("classifier alone (13 types only)", known_clf),
                    ("engine + classifier (13 types only)", scoring.fuse(base, dev_sim, known_clf, weight))):
        bands = metrics.calibrate(s[is_legit])
        novelty[name] = metrics.rate(metrics.hits(s[unseen_mask], bands["caution"]), rng)["value"]
    print("[novelty]", novelty)

    # 7. Decision against the adoption rules (engine + classifier vs engine without).
    cur, new = results["engine without classifier"], results[chosen]
    rules = {
        "1. dev recall at Caution up at least 3 points":
            new["recall_caution"]["value"] - cur["recall_caution"]["value"] >= 0.03,
        "2. mean leave-one-type-out recall not lower":
            loco_mean["engine_with_classifier"] >= loco_mean["engine_without"],
        "3. High-band dev false alarms not higher": new["fpr_high"]["value"] <= cur["fpr_high"]["value"] + 1e-9,
        "4. all tests pass": None,
        "5. real-SMS false alarms up at most 2 points":
            (sms_res[chosen]["value"] - sms_res["engine without classifier"]["value"] <= 0.02) if sms else None,
    }
    beats_baseline = results["classifier alone"]["roc_auc"] - results["baseline: length + has link"]["roc_auc"] >= 0.05
    caveat = new["recall_caution"]["value"] - loco_mean["engine_with_classifier"] > 0.15
    hard = [v for v in rules.values() if v is not None] + [beats_baseline]
    verdict = ("adopt with caveats" if caveat else "adopt") if all(hard) else "reject"

    # 8. Bundle, with the engine's live cut-offs when the classifier is on.
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "classifier.joblib"
        joblib.dump(model, path)
        saved_env = {k: os.environ.get(k) for k in ("TRUSTGRAPH_CLASSIFIER", "TRUSTGRAPH_CLASSIFIER_MODEL")}
        saved_index = sim._index
        os.environ["TRUSTGRAPH_CLASSIFIER"], os.environ["TRUSTGRAPH_CLASSIFIER_MODEL"] = "1", str(path)
        clf_detector._bundle, sim._index = None, index
        try:
            bands = live_bands()
        finally:
            for k, v in saved_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            clf_detector._bundle, sim._index = None, saved_index
        dev_m = {"recall_caution": new["recall_caution"]["value"], "fpr_caution": new["fpr_caution"]["value"],
                 "fpr_high": new["fpr_high"]["value"], "loco_mean": loco_mean["engine_with_classifier"],
                 "real_sms_false_alarms": sms_res[chosen]["value"] if sms else None,
                 "current_engine": {"recall_caution": cur["recall_caution"]["value"],
                                    "fpr_caution": cur["fpr_caution"]["value"], "fpr_high": cur["fpr_high"]["value"],
                                    "loco_mean": loco_mean["engine_without"],
                                    "real_sms_false_alarms": sms_res["engine without classifier"]["value"] if sms else None},
                 "verdict": verdict}
        requires = "TRUSTGRAPH_CLASSIFIER=1" + (" and similarity_v2 promoted first (its cut-offs assume both)" if on_b else "")
        card = card_text(best_c, weight, results, chosen, three, loco_mean, novelty, flagged_words, audit_cmp,
                         verdict, on_b, len(corpus))
        bundle = write_bundle("classifier_v1", {"classifier.joblib": path}, {"classifier.joblib": "models/classifier.joblib"},
                              bands, data_hash=data_hash(corpus), n_train=len(corpus),
                              seeds={"cv_folds": SEED, "model": SEED, "bootstrap": SEED}, dev_metrics=dev_m,
                              card=card, requires=requires)

    out.mkdir(parents=True, exist_ok=True)
    res = {"on_top_of_track_b": on_b, "C": best_c, "c_table": c_table, "fusion_weight": weight,
           "three_ways": {k: (v["recall_caution"]["value"] if isinstance(v, dict) else v) for k, v in three.items()},
           "loco_mean": loco_mean, "novelty": novelty, "flagged_words": flagged_words,
           "beats_baseline": beats_baseline, "rules": rules, "verdict": verdict, "bundle": str(bundle),
           "live_bands": bands}
    (out / "track_c.json").write_text(json.dumps(res, indent=1, default=float))
    write_csv(out / "track_c.csv", table)
    write_csv(out / "track_c_loco.csv", loco_rows)
    write_csv(out / "track_c_coefficients.csv", audit_rows)
    write_csv(out / "track_c_groups.csv", by_group)
    with open(out / "runlog.md", "a", encoding="utf-8") as f:
        f.write(f"- {time.strftime('%H:%M:%S')} `PYTHONPATH=src python -m training.track_c` (seed {SEED}, "
                f"{time.time() - t0:.0f}s): C={best_c}, weight {weight}, verdict {verdict}\n")
    print(json.dumps(res, indent=1, default=float))
    print(f"{time.time() - t0:.0f}s")


def card_text(c, weight, results, chosen, three, loco_mean, novelty, flagged, audit_cmp, verdict, on_b, n) -> str:
    cur, new, alone = results["engine without classifier"], results[chosen], results["classifier alone"]
    base = results["baseline: length + has link"]
    t3 = {k: (v["recall_caution"]["value"] if isinstance(v, dict) else v) for k, v in three.items()}
    return f"""## What it is
A logistic-regression text classifier (TF-IDF word 1-2 grams + character 3-5 grams, balanced class weights,
C={c}, Platt-scaled on out-of-fold scores) trained on the {n} corpus-split messages. Text is normalized first
(disguise tricks undone; links, phones, amounts, numbers replaced by markers). It is a fifth signal named
"classifier", appended after the other four only when TRUSTGRAPH_CLASSIFIER=1, with fusion weight {weight}
(chosen on dev from 0.3 / 0.5 / 1.0). Built on top of {'Track B examples (similarity_v2)' if on_b else 'the current similarity examples'}.

## How it was tested (dev, each at its own ~10% / ~1% dev false-alarm cut-offs)

| | Scams caught at Caution | Honest flagged at High | ROC-AUC |
|---|---|---|---|
| Engine without classifier | {cur['recall_caution']['value']:.1%} | {cur['fpr_high']['value']:.1%} | {cur['roc_auc']:.3f} |
| Engine with classifier | {new['recall_caution']['value']:.1%} [{new['recall_caution']['lo']:.1%}, {new['recall_caution']['hi']:.1%}] | {new['fpr_high']['value']:.1%} | {new['roc_auc']:.3f} |
| Classifier alone | {alone['recall_caution']['value']:.1%} | {alone['fpr_high']['value']:.1%} | {alone['roc_auc']:.3f} |
| Baseline: length + has link | {base['recall_caution']['value']:.1%} | {base['fpr_high']['value']:.1%} | {base['roc_auc']:.3f} |

Classifier alone, three ways: random CV {t3['(a) random 5-fold CV on corpus (in-distribution)']:.1%},
group CV {t3['(a2) group 5-fold CV on corpus (families held out)']:.1%}, dev {t3['(b) dev (families held out)']:.1%},
leave-one-type-out {t3['(c) leave-one-type-out, mean over 29 types']:.1%}.
Engine leave-one-type-out mean: {loco_mean['engine_without']:.1%} without, {loco_mean['engine_with_classifier']:.1%} with.
Trained without the 16 types the engine had no examples for, scored on them: classifier alone
{novelty['classifier alone (13 types only)']:.1%}; engine {novelty['engine without classifier']:.1%} without,
{novelty['engine + classifier (13 types only)']:.1%} with.

Shortcut audit: {len(flagged)} watch-list words among the 50 strongest terms each way ({', '.join(flagged) or 'none'});
retrained without them, classifier alone catches
{audit_cmp['classifier alone, flagged words removed']['recall_caution']['value']:.1%} (was {alone['recall_caution']['value']:.1%}).

Verdict: **{verdict}**.

## Limits
- Trained and tested on messages from one generator: it can learn that generator's style. The leave-one-type-out
  and 13-types-only numbers are the honest ones.
- Cut-offs in risk_bands.json assume the classifier is ON{' and similarity_v2 is promoted' if on_b else ''}.
- The website shows it as a fifth row; teammates' tools that expect exactly four signals must be checked first.

## Promote / roll back
Set TRUSTGRAPH_CLASSIFIER=1, run `python scripts/promote_model.py models/candidate/classifier_v1 --yes`,
restart the server. `python scripts/promote_model.py --rollback` undoes it.
"""


if __name__ == "__main__":
    main()
