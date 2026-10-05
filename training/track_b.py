"""Track B: grow the similarity signal's reference examples with corpus-split messages.

    PYTHONPATH=src python -m training.track_b

Candidates (all compared on dev at their own matched ~10% / ~1% false-alarm cut-offs):
  current         the built-in examples (similarity/corpus.py), as the live engine
  grown           + corpus-split scam and honest messages, near-copies removed
  grown_norm      the same, compared after trustgraph.textnorm.normalize
                  (disguise tricks undone; links, phones, amounts, numbers as markers)
  13 types only   the chosen variant built WITHOUT the 16 scam types the engine
                  had no examples for, scored on those 16: a clean novelty check

Leave-one-type-out rebuilds the examples without type X and measures dev recall
on X, for all 29 types. The negation handling and the wording-only cap are
unchanged (they live in the detector). Writes reports/<date>-training/track_b*
and the bundle models/candidate/similarity_v2/.
"""
import argparse
import copy
import json
import tempfile
import time
from datetime import date
from pathlib import Path

import numpy as np

from eval import metrics
from eval.leakage import filter_leaks
from training import scoring
from training.bundle import live_bands, write_bundle
from training.data import data_hash, dedupe, held_out_texts, load
from trustgraph.similarity import detector as sim
from trustgraph.similarity.corpus import LEGIT_MESSAGES, SCAM_SCRIPTS

SEED = 0


def additions(corpus_rows: list[dict], scam_categories: set | None = None) -> tuple[dict, list, dict]:
    """Built-in examples plus corpus-split messages (optionally only some scam
    types), with near-copies and anything close to a dev/test message removed."""
    rows = [r for r in corpus_rows if r["label"] == "legit" or scam_categories is None
            or r["category"] in scam_categories]
    rows, dup = dedupe(rows)
    rows, leaked = filter_leaks(rows, held_out_texts())
    scams = copy.deepcopy(SCAM_SCRIPTS)
    for r in rows:
        if r["label"] == "scam":
            scams.setdefault(r["category"], []).append(r["text"])
    legit = list(LEGIT_MESSAGES) + [r["text"] for r in rows if r["label"] == "legit"]
    stats = {"added_scam": sum(r["label"] == "scam" for r in rows),
             "added_legit": sum(r["label"] == "legit" for r in rows),
             "near_copies_dropped": len(dup), "close_to_dev_or_test_dropped": len(leaked)}
    return scams, legit, stats, rows


def dev_scores(index: dict, dev: list[dict], base: dict) -> np.ndarray:
    _, similarity = scoring.similarity_scores(index, dev, base["flag_keep"])
    return scoring.fuse(base, similarity)


def loco(dev: list[dict], base: dict, scams: dict, legit: list, normalized: bool) -> list[dict]:
    """For every scam type: rebuild the examples without it, recalibrate on dev
    honest messages, measure dev recall on that type."""
    rng = np.random.default_rng(SEED)
    legit_idx = [i for i, r in enumerate(dev) if r["label"] == "legit"]
    table = []
    for cat in sorted({r["category"] for r in dev if r["label"] == "scam"}):
        idx = legit_idx + [i for i, r in enumerate(dev) if r["category"] == cat]
        rows = [dev[i] for i in idx]
        sub = {k: v[idx] for k, v in base.items()}
        index = sim.build_index({k: v for k, v in scams.items() if k != cat}, legit, normalized)
        s = dev_scores(index, rows, sub)
        bands = metrics.calibrate(s[:len(legit_idx)])
        r = metrics.rate(metrics.hits(s[len(legit_idx):], bands["caution"]), rng)
        table.append({"category": cat, "n": len(idx) - len(legit_idx), "recall_left_out": r["value"],
                      "lo": r["lo"], "hi": r["hi"]})
    return table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=f"reports/{date.today().isoformat()}-training")
    ap.add_argument("--retry", action="store_true", help="second attempt: capped examples (+ casual honest texts)")
    args = ap.parse_args()
    out = Path(args.out)
    if args.retry:
        return retry(out)
    t0 = time.time()
    corpus, dev = load("corpus"), load("dev")
    base = scoring.base_signals("dev", dev)
    sms = scoring.sms_rows()
    sms_base = scoring.base_signals("sms", sms) if sms else None
    unseen = {r["category"] for r in dev if r["label"] == "scam" and r["novelty"] == "unseen"}

    grown_scams, grown_legit, stats, added_rows = additions(corpus)
    candidates = {
        "current": (SCAM_SCRIPTS, LEGIT_MESSAGES, False),
        "grown": (grown_scams, grown_legit, False),
        "grown_norm": (grown_scams, grown_legit, True),
    }
    results, table, indexes = {}, [], {}
    for name, (scams, legit, norm) in candidates.items():
        indexes[name] = sim.build_index(scams, legit, norm)
        s = dev_scores(indexes[name], dev, base)
        res = scoring.compare(dev, s, SEED)
        sms_res = None
        if sms:
            sms_s = scoring.fuse(sms_base, scoring.similarity_scores(indexes[name], sms, sms_base["flag_keep"])[1])
            sms_res = scoring.sms_false_alarms(sms_s, sms, res["thresholds"], SEED)
        results[name] = {"dev": res, "sms": sms_res}
        table.append(scoring.summary_row(name, res, sms_res))
        print(f"[{name}] dev recall@Caution {res['recall_caution']['value']:.1%} at false alarms "
              f"{res['fpr_caution']['value']:.1%}; real SMS false alarms {sms_res['value']:.1%}" if sms_res else "")

    chosen = max(("grown", "grown_norm"), key=lambda n: results[n]["dev"]["recall_caution"]["value"])
    scams, legit, norm = candidates[chosen]

    # Clean novelty check: built without the 16 types, scored on them.
    k_scams, k_legit, _, _ = additions(corpus, scam_categories={c for c in SCAM_SCRIPTS})
    k_index = sim.build_index(k_scams, k_legit, norm)
    novelty = {}
    for name, index in (("current", indexes["current"]), (f"{chosen} (13 types only)", k_index)):
        s = dev_scores(index, dev, base)
        bands = metrics.calibrate(s[[r["label"] == "legit" for r in dev]])
        m = [r["label"] == "scam" and r["category"] in unseen for r in dev]
        novelty[name] = metrics.rate(metrics.hits(s[m], bands["caution"]), np.random.default_rng(SEED))
    print("[novelty, 16 types left out]", {k: f"{v['value']:.1%}" for k, v in novelty.items()})

    loco_current = loco(dev, base, SCAM_SCRIPTS, LEGIT_MESSAGES, False)
    loco_chosen = loco(dev, base, scams, legit, norm)
    loco_rows = [{"category": a["category"], "n": a["n"], "unseen_in_evaluation": a["category"] in unseen,
                  "current_left_out": a["recall_left_out"], f"{chosen}_left_out": b["recall_left_out"],
                  f"{chosen}_lo": b["lo"], f"{chosen}_hi": b["hi"]} for a, b in zip(loco_current, loco_chosen)]
    loco_mean = {"current": float(np.mean([r["recall_left_out"] for r in loco_current])),
                 chosen: float(np.mean([r["recall_left_out"] for r in loco_chosen]))}
    print("[leave-one-type-out mean]", {k: f"{v:.1%}" for k, v in loco_mean.items()})

    # Decision against the adoption rules.
    cur, new = results["current"], results[chosen]
    gain = new["dev"]["recall_caution"]["value"] - cur["dev"]["recall_caution"]["value"]
    in_dist = new["dev"]["recall_caution"]["value"]
    rules = {
        "1. dev recall at Caution up at least 3 points": gain >= 0.03,
        "2. mean leave-one-type-out recall not lower": loco_mean[chosen] >= loco_mean["current"],
        "3. High-band dev false alarms not higher": new["dev"]["fpr_high"]["value"] <= cur["dev"]["fpr_high"]["value"] + 1e-9,
        "4. all tests pass": None,  # checked by pytest before committing
        "5. real-SMS false alarms up at most 2 points": (new["sms"]["value"] - cur["sms"]["value"] <= 0.02) if new["sms"] else None,
    }
    caveat = in_dist - loco_mean[chosen] > 0.15
    hard = [v for k, v in rules.items() if v is not None]
    verdict = ("adopt with caveats" if caveat else "adopt") if all(hard) else "reject"

    # Bundle: the promoted example list plus the engine's live cut-offs with it.
    with tempfile.TemporaryDirectory() as tmp:
        corpus_file = Path(tmp) / "similarity_corpus.json"
        corpus_file.write_text(json.dumps({"scam_scripts": scams, "legit_messages": legit, "normalized": norm},
                                          ensure_ascii=False, indent=1), encoding="utf-8")
        saved = sim._index
        sim._index = indexes[chosen]
        try:
            bands = live_bands()
        finally:
            sim._index = saved
        dev_m = {"recall_caution": in_dist, "fpr_caution": new["dev"]["fpr_caution"]["value"],
                 "fpr_high": new["dev"]["fpr_high"]["value"], "loco_mean": loco_mean[chosen],
                 "real_sms_false_alarms": new["sms"]["value"] if new["sms"] else None,
                 "current_engine": {"recall_caution": cur["dev"]["recall_caution"]["value"],
                                    "fpr_caution": cur["dev"]["fpr_caution"]["value"],
                                    "fpr_high": cur["dev"]["fpr_high"]["value"], "loco_mean": loco_mean["current"],
                                    "real_sms_false_alarms": cur["sms"]["value"] if cur["sms"] else None},
                 "verdict": verdict}
        card = card_text(chosen, stats, results, loco_mean, novelty, verdict, norm)
        bundle = write_bundle("similarity_v2", {"similarity_corpus.json": corpus_file},
                              {"similarity_corpus.json": "models/similarity_corpus.json"}, bands,
                              data_hash=data_hash(added_rows), n_train=len(added_rows), seeds={"bootstrap": SEED},
                              dev_metrics=dev_m, card=card)

    res = {"stats": stats, "chosen": chosen, "table": table, "novelty": {k: v for k, v in novelty.items()},
           "loco_mean": loco_mean, "rules": rules, "verdict": verdict, "bundle": str(bundle),
           "live_bands": bands}
    out.mkdir(parents=True, exist_ok=True)
    (out / "track_b.json").write_text(json.dumps(res, indent=1, default=float))
    write_csv(out / "track_b.csv", table)
    write_csv(out / "track_b_loco.csv", loco_rows)
    with open(out / "runlog.md", "a", encoding="utf-8") as f:
        f.write(f"- {time.strftime('%H:%M:%S')} `PYTHONPATH=src python -m training.track_b` (seed {SEED}, "
                f"{time.time() - t0:.0f}s): chosen {chosen}, verdict {verdict}\n")
    print(f"verdict: {verdict}; bundle {bundle}; {time.time() - t0:.0f}s")


def card_text(chosen, stats, results, loco_mean, novelty, verdict, norm) -> str:
    cur, new = results["current"]["dev"], results[chosen]["dev"]
    nov = list(novelty.values())
    return f"""## What it is
The similarity signal's reference examples, grown from {sum(len(v) for v in SCAM_SCRIPTS.values())} scam and
{len(LEGIT_MESSAGES)} honest hand-written examples by {stats['added_scam']} scam and {stats['added_legit']} honest
messages from the corpus split ({stats['near_copies_dropped']} near-copies and {stats['close_to_dev_or_test_dropped']}
messages close to a dev/test message removed). Comparison after text normalization: {'yes' if norm else 'no'}.
Same detector code, red flags, negation handling and wording-only cap.

## How it was tested
Dev split (452 scams, 1,498 honest; template families never shared with the corpus split), at this model's
own cut-offs flagging about 10% (Caution) and 1% (High) of dev honest messages.

| | Current examples | This bundle |
|---|---|---|
| Dev scams caught at Caution | {cur['recall_caution']['value']:.1%} | {new['recall_caution']['value']:.1%} [{new['recall_caution']['lo']:.1%}, {new['recall_caution']['hi']:.1%}] |
| Dev honest flagged at High | {cur['fpr_high']['value']:.1%} | {new['fpr_high']['value']:.1%} |
| Mean leave-one-type-out recall | {loco_mean['current']:.1%} | {loco_mean[chosen]:.1%} |
| 16 types built without, scored on | {nov[0]['value']:.1%} | {nov[1]['value']:.1%} |
| Real UK SMS honest texts flagged | {results['current']['sms']['value']:.1%} | {results[chosen]['sms']['value']:.1%} |

Verdict: **{verdict}**.

## Limits
- Every added example comes from the same generator as the dev and test messages, so dev recall flatters it;
  leave-one-type-out is the honest novelty number.
- Cut-offs in risk_bands.json are set on synthetic honest messages (src/trustgraph/evaluate.py's calibration set).

## Promote / roll back
`python scripts/promote_model.py models/candidate/similarity_v2 --yes`, then restart the server.
`python scripts/promote_model.py --rollback` undoes it.
"""


def write_csv(path: Path, rows: list[dict]):
    import csv
    fields = list(dict.fromkeys(k for r in rows for k in r))  # union of keys, first-seen order
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)



# ---------------------------------------------------------------- retry
# Second attempt, after the first was rejected on real-SMS false alarms. The
# variants were fixed before running: (1) cap each type at its K most varied
# examples, so generator-style text doesn't swamp the reference list; (2)
# optionally add short casual everyday texts on the honest side, since the
# generated honest messages contain no casual chat. These are hand-written
# here, not taken from the real SMS set. Because the real-SMS result motivated
# this retry and gates the choice, the chosen variant's real-SMS number is
# slightly optimistic.
CASUAL_HONEST = [
    "ok see you at 7", "on my way, 10 mins", "lol yes that was so funny", "can't talk now, call you later",
    "haha no way! tell me everything tomorrow", "did you get home ok?", "thanks for today, had a great time",
    "sure, sounds good to me", "what time is the movie?", "running late sorry, start without me",
    "good night, sleep well", "where are you guys?", "i'm at the shop, need anything?", "yes please, milk and bread",
    "happy birthday!! have an amazing day", "miss you, come visit soon", "k cool", "no worries at all",
    "just woke up, give me 20 mins", "the match was brilliant last night", "is the class cancelled today?",
    "can you pick up the kids at 4?", "dinner's ready, come down", "i'll bring the cake", "send me the pics from the trip",
    "good luck for the exam tomorrow!", "how was the interview?", "aaj kya plan hai?", "main 5 baje tak aa jaunga",
    "khana kha liya?", "kal milte hain bhai", "theek hai, koi baat nahi", "ghar pahunch gaye?",
    "njan ippo varam", "nale kanam", "veettil ethiyo?", "sheri, kuzhappamilla", "evide aanu ippo?",
    "food kazhicho?", "ok da, call cheyyam",
]
RETRY_K = (5, 10)


def diverse(rows: list[dict], k: int) -> list[dict]:
    """At most k rows, picked one at a time to be as different as possible from
    those already picked (word TF-IDF), starting from the first row."""
    if len(rows) <= k:
        return rows
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    sims = cosine_similarity(TfidfVectorizer(sublinear_tf=True).fit_transform([r["text"] for r in rows]))
    picked = [0]
    while len(picked) < k:
        closest = sims[:, picked].max(axis=1)
        closest[picked] = np.inf
        picked.append(int(np.argmin(closest)))
    return [rows[i] for i in picked]


def capped_additions(corpus_rows: list[dict], k: int, casual: bool, scam_categories: set | None = None):
    _, _, stats, rows = additions(corpus_rows, scam_categories)
    kept = []
    for label in ("scam", "legit"):
        for cat in sorted({r["category"] for r in rows if r["label"] == label}):
            kept += diverse([r for r in rows if r["label"] == label and r["category"] == cat], k)
    scams = copy.deepcopy(SCAM_SCRIPTS)
    for r in kept:
        if r["label"] == "scam":
            scams.setdefault(r["category"], []).append(r["text"])
    legit = list(LEGIT_MESSAGES) + [r["text"] for r in kept if r["label"] == "legit"]
    if casual:
        casual_rows, _ = filter_leaks([{"text": t} for t in CASUAL_HONEST], held_out_texts())
        legit += [r["text"] for r in casual_rows]
    stats = {**stats, "kept_scam": sum(r["label"] == "scam" for r in kept),
             "kept_legit": sum(r["label"] == "legit" for r in kept), "casual_added": len(legit) - len(LEGIT_MESSAGES)
             - sum(r["label"] == "legit" for r in kept)}
    return scams, legit, stats, kept


def retry(out: Path):
    t0 = time.time()
    corpus, dev = load("corpus"), load("dev")
    base = scoring.base_signals("dev", dev)
    sms = scoring.sms_rows()
    sms_base = scoring.base_signals("sms", sms)
    unseen = {r["category"] for r in dev if r["label"] == "scam" and r["novelty"] == "unseen"}
    variants = {"current": (SCAM_SCRIPTS, LEGIT_MESSAGES, {}, [])}
    for k in RETRY_K:
        for casual in (False, True):
            variants[f"capped_{k}{'_casual' if casual else ''}"] = capped_additions(corpus, k, casual)
    results, table, indexes = {}, [], {}
    for name, (scams, legit, stats, _) in variants.items():
        indexes[name] = sim.build_index(scams, legit)
        res = scoring.compare(dev, dev_scores(indexes[name], dev, base), SEED)
        sms_s = scoring.fuse(sms_base, scoring.similarity_scores(indexes[name], sms, sms_base["flag_keep"])[1])
        sms_res = scoring.sms_false_alarms(sms_s, sms, res["thresholds"], SEED)
        results[name] = {"dev": res, "sms": sms_res, "stats": stats}
        table.append({**scoring.summary_row(name, res, sms_res), **{f"n_{k}": v for k, v in stats.items()}})
        print(f"[{name}] dev recall {res['recall_caution']['value']:.1%}  sms {sms_res['value']:.1%}  {stats}")

    cur = results["current"]
    loco_cur = loco(dev, base, SCAM_SCRIPTS, LEGIT_MESSAGES, False)
    loco_mean = {"current": float(np.mean([r["recall_left_out"] for r in loco_cur]))}
    decisions = {}
    for name in (n for n in variants if n != "current"):
        new = results[name]
        scams, legit, _, _ = variants[name]
        loco_mean[name] = float(np.mean([r["recall_left_out"] for r in loco(dev, base, scams, legit, False)]))
        rules = {
            "1. recall +3 points": new["dev"]["recall_caution"]["value"] - cur["dev"]["recall_caution"]["value"] >= 0.03,
            "2. leave-one-type-out not lower": loco_mean[name] >= loco_mean["current"],
            "3. High false alarms not higher": new["dev"]["fpr_high"]["value"] <= cur["dev"]["fpr_high"]["value"] + 1e-9,
            "5. real SMS +2 points at most": new["sms"]["value"] - cur["sms"]["value"] <= 0.02,
        }
        caveat = new["dev"]["recall_caution"]["value"] - loco_mean[name] > 0.15
        decisions[name] = {"rules": rules, "verdict": ("adopt with caveats" if caveat else "adopt")
                           if all(rules.values()) else "reject"}
        print(f"[{name}] loco {loco_mean[name]:.1%}  {decisions[name]}")
    passing = [n for n, d in decisions.items() if d["verdict"] != "reject"]
    chosen = max(passing, key=lambda n: results[n]["dev"]["recall_caution"]["value"]) if passing else None

    novelty = {}
    if chosen:
        k, casual = int(chosen.split("_")[1]), chosen.endswith("casual")
        ks, kl, _, _ = capped_additions(corpus, k, casual, scam_categories=set(SCAM_SCRIPTS))
        for name, index in (("current", indexes["current"]), (f"{chosen} (13 types only)", sim.build_index(ks, kl))):
            s = dev_scores(index, dev, base)
            bands = metrics.calibrate(s[[r["label"] == "legit" for r in dev]])
            m = [r["label"] == "scam" and r["category"] in unseen for r in dev]
            novelty[name] = metrics.rate(metrics.hits(s[m], bands["caution"]), np.random.default_rng(SEED))["value"]
        scams, legit, stats, kept = variants[chosen]
        new = results[chosen]
        with tempfile.TemporaryDirectory() as tmp:
            corpus_file = Path(tmp) / "similarity_corpus.json"
            corpus_file.write_text(json.dumps({"scam_scripts": scams, "legit_messages": legit, "normalized": False},
                                              ensure_ascii=False, indent=1), encoding="utf-8")
            saved = sim._index
            sim._index = indexes[chosen]
            try:
                bands = live_bands()
            finally:
                sim._index = saved
            dev_m = {"recall_caution": new["dev"]["recall_caution"]["value"],
                     "fpr_caution": new["dev"]["fpr_caution"]["value"], "fpr_high": new["dev"]["fpr_high"]["value"],
                     "loco_mean": loco_mean[chosen], "real_sms_false_alarms": new["sms"]["value"],
                     "current_engine": {"recall_caution": cur["dev"]["recall_caution"]["value"],
                                        "fpr_caution": cur["dev"]["fpr_caution"]["value"],
                                        "fpr_high": cur["dev"]["fpr_high"]["value"], "loco_mean": loco_mean["current"],
                                        "real_sms_false_alarms": cur["sms"]["value"]},
                     "verdict": decisions[chosen]["verdict"]}
            card = retry_card(chosen, stats, results, loco_mean, novelty, decisions[chosen]["verdict"])
            write_bundle("similarity_v3", {"similarity_corpus.json": corpus_file},
                         {"similarity_corpus.json": "models/similarity_corpus.json"}, bands,
                         data_hash=data_hash(kept), n_train=len(kept), seeds={"bootstrap": SEED, "diverse_pick": "first row"},
                         dev_metrics=dev_m, card=card)
    res = {"table": table, "loco_mean": loco_mean, "decisions": decisions, "chosen": chosen, "novelty": novelty}
    (out / "track_b_retry.json").write_text(json.dumps(res, indent=1, default=float))
    write_csv(out / "track_b_retry.csv", table)
    with open(out / "runlog.md", "a", encoding="utf-8") as f:
        f.write(f"- {time.strftime('%H:%M:%S')} `PYTHONPATH=src python -m training.track_b --retry` (seed {SEED}, "
                f"{time.time() - t0:.0f}s): chosen {chosen}\n")
    print(json.dumps(res, indent=1, default=float))


def retry_card(chosen, stats, results, loco_mean, novelty, verdict) -> str:
    cur, new = results["current"], results[chosen]
    nov = list(novelty.values())
    return f"""## What it is
Second Track B attempt ({chosen}). The similarity signal's built-in examples plus, for each scam type and each
honest message type in the corpus split, at most its {chosen.split('_')[1]} most varied messages
({stats['kept_scam']} scam, {stats['kept_legit']} honest){f", plus {stats['casual_added']} short casual everyday texts written by hand" if stats.get('casual_added') else ''}.
Same detector code, red flags, negation handling and wording-only cap.

## How it was tested
Dev split at this model's own ~10% / ~1% dev false-alarm cut-offs; real UK SMS honest texts as a false-alarm check.

| | Current examples | This bundle |
|---|---|---|
| Dev scams caught at Caution | {cur['dev']['recall_caution']['value']:.1%} | {new['dev']['recall_caution']['value']:.1%} [{new['dev']['recall_caution']['lo']:.1%}, {new['dev']['recall_caution']['hi']:.1%}] |
| Dev honest flagged at High | {cur['dev']['fpr_high']['value']:.1%} | {new['dev']['fpr_high']['value']:.1%} |
| Mean leave-one-type-out recall | {loco_mean['current']:.1%} | {loco_mean[chosen]:.1%} |
| 16 types built without, scored on | {nov[0]:.1%} | {nov[1]:.1%} |
| Real UK SMS honest texts flagged | {cur['sms']['value']:.1%} | {new['sms']['value']:.1%} |

Verdict: **{verdict}**.

## Limits
- This retry was designed after the first attempt failed the real-SMS check, and that check gated the choice,
  so the real-SMS number above is slightly optimistic.
- Added examples come from the same generator as dev and test; leave-one-type-out is the honest novelty number.

## Promote / roll back
`python scripts/promote_model.py models/candidate/similarity_v3 --yes`, then restart the server.
`python scripts/promote_model.py --rollback` undoes it.
"""


if __name__ == "__main__":
    main()
