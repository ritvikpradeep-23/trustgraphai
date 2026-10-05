"""Run one improvement round of the fast routine.

    PYTHONPATH=src:. python scripts/run_round.py 3            # rounds 3..12, in order
    PYTHONPATH=src:. python scripts/run_round.py 3 --commit   # also git-commit the result

1. Check every round file against its SHA-256; load the current best candidate.
2. TEST BEFORE FIX: score round N at the candidate's dev cut-offs. Report
   recall per scam type (Caution and High), false alarms on its honest messages,
   and every miss and false alarm with the engine's explanation
   (reports/fast/round_NN.md, one row in runs/history.csv).
3. FIX: add the round's missed scams to the scam examples and its false-alarm
   honest messages to the honest examples (what a user report does). Rule or
   code changes are never made here: they go to reports/fast/proposed_rules.md
   for review.
4. Rebuild, recalibrate on rounds 01-02, run the gate. Pass: the new bundle
   becomes the best. Fail: it is kept for reference but the best is unchanged.

Synthetic data throughout; numbers are not real-world accuracy.
"""
import argparse
import csv
import copy
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path[:0] = ["src", "."]
from eval import metrics  # noqa: E402
from routine import core  # noqa: E402
from routine.generate import DEV, FINAL, IMPROVE  # noqa: E402

FIELDS = ["round", "time", "candidate_before", "scams", "honest", "prefix_recall_caution", "prefix_recall_high",
          "prefix_false_alarms_caution", "misses", "false_alarms", "added_scam", "added_honest",
          "dev_recall_before", "dev_recall_after", "real_sms_false_alarms_after", "gate", "failed_checks",
          "candidate_after"]


def pct(x):
    return "n/a" if x is None else f"{x:.1%}"


def run(n: int, commit: bool):
    if n in DEV or n in FINAL or n not in IMPROVE:
        raise SystemExit(f"round {n} is not an improvement round (03-12)")
    t0 = time.time()
    manifest = core.verify_manifest()
    rows = core.load_round(n)
    dev = core.dev_rows()
    best = core.load_best()
    index = core.index_for(best)
    dev_prev = core.dev_recall(index, dev)
    bands = dev_prev["bands"]
    base_index = core.index_for(core.baseline())
    base_dev = core.dev_recall(base_index, dev)
    sms_base = core.sms_false_alarms(base_index, base_dev["bands"])

    # ---- 2. test before fix
    s = core.scores(index, rows, f"fast_round_{n:02d}")
    scam = np.array([r["label"] == "scam" for r in rows])
    caution, high = metrics.hits(s, bands["caution"]), metrics.hits(s, bands["high"])
    rng = np.random.default_rng(0)
    rec_c = metrics.rate(caution[scam], rng)
    rec_h = float(high[scam].mean())
    fa = float(caution[~scam].mean())
    per_cat = {}
    for i, r in enumerate(rows):
        if r["label"] == "scam":
            c = per_cat.setdefault(r["category"], {"n": 0, "caution": 0, "high": 0, "in_corpus": r["in_corpus"]})
            c["n"] += 1
            c["caution"] += int(caution[i])
            c["high"] += int(high[i])
    misses = [(float(s[i]), r) for i, r in enumerate(rows) if r["label"] == "scam" and not caution[i]]
    alarms = [(float(s[i]), r) for i, r in enumerate(rows) if r["label"] == "legit" and caution[i]]

    # ---- 3. fix: add misses and false alarms to the examples
    new = {"name": f"fast_r{n:02d}", "scams": copy.deepcopy(best["scams"]), "legit": list(best["legit"])}
    for _, r in misses:
        new["scams"].setdefault(r["category"], []).append(r["text"])
    new["legit"] += [r["text"] for _, r in alarms]

    # ---- 4. rebuild, recalibrate, gate
    new_index = core.index_for(new)
    dev_new = core.dev_recall(new_index, dev)
    sms_new = core.sms_false_alarms(new_index, dev_new["bands"])
    card = (f"## What it is\nThe similarity examples after round {n:02d}: the previous best ({best['name']}) plus "
            f"{len(misses)} missed scams and {len(alarms)} false-alarm honest messages from round {n:02d}.\n\n"
            f"## How it was tested\nDev rounds 01-02, at this bundle's own ~10% / ~1% dev false-alarm cut-offs: "
            f"scams caught {pct(dev_new['recall_caution'])} (was {pct(dev_prev['recall_caution'])}), honest flagged "
            f"at High {pct(dev_new['fpr_high'])}. Real UK SMS honest texts flagged {pct(sms_new)} "
            f"(demo-safe {pct(sms_base)}).\n\n## Limits\nSynthetic data from one generator; the added examples come "
            f"from the same generator as later rounds.\n\n## Promote\n`python scripts/promote_model.py "
            f"models/candidate/fast_r{n:02d}` (dry run), then add `--yes`. `--rollback` undoes it.\n")
    bundle = core.save_bundle(new["name"], new, new_index, dev_new, base_dev, "pending gate", card)
    with core.with_index(new_index):
        live = json.loads((bundle / "risk_bands.json").read_text())
        scen = core.scenario_check(new_index, live)
    tests_ok, tests_line = core.run_tests(str(bundle))
    g = core.gate(tests_ok, scen, dev_new, dev_prev, sms_new, sms_base)
    verdict = "accepted" if g["passed"] else "reverted"
    manifest_b = json.loads((bundle / "manifest.json").read_text())
    manifest_b["dev_metrics"]["verdict"] = verdict
    (bundle / "manifest.json").write_text(json.dumps(manifest_b, indent=2, default=float))
    if g["passed"]:
        core.RUNS.mkdir(exist_ok=True)
        core.BEST.write_text(json.dumps({"name": new["name"], "dir": str(bundle), "round": n,
                                         "dev_recall_caution": dev_new["recall_caution"],
                                         "real_sms_false_alarms": sms_new}, indent=1))
    after = new["name"] if g["passed"] else best["name"]

    # ---- report
    core.REPORTS.mkdir(parents=True, exist_ok=True)
    L = [f"# Round {n:02d} (synthetic data)", "",
         f"Round file verified against the manifest (sha256 `{manifest['files'][f'round_{n:02d}.jsonl']['sha256'][:16]}…`). "
         f"Candidate before the fix: **{best['name']}**. Cut-offs set on dev rounds 01-02: Caution {bands['caution']:.3f}, "
         f"High {bands['high']:.3f}.", "",
         "## Test before fix", "",
         f"- Scams caught at Caution or above: **{pct(rec_c['value'])}** [{pct(rec_c['lo'])}, {pct(rec_c['hi'])}] "
         f"of {int(scam.sum())} (synthetic data); at High: {pct(rec_h)}.",
         f"- Honest messages flagged at Caution: {pct(fa)} of {int((~scam).sum())} (synthetic data).", "",
         "| Scam type | Already in examples? | n | Caught (Caution) | Caught (High) |", "|---|---|---|---|---|"]
    for cat, c in sorted(per_cat.items(), key=lambda kv: kv[1]["caution"] / kv[1]["n"]):
        L.append(f"| {cat} | {c['in_corpus']} | {c['n']} | {c['caution']}/{c['n']} | {c['high']}/{c['n']} |")
    L += ["", f"### Missed scams ({len(misses)})", ""]
    for score, r in sorted(misses, key=lambda x: x[0]):
        L.append(f"- [{r['category']}, {r['language']}, {r['evasion_type']}] \"{r['text'][:140].replace(chr(10), ' ')}\" "
                 f"→ {core.explain(index, r)[:160]}")
    L += ["", f"### False alarms ({len(alarms)})", ""]
    for score, r in sorted(alarms, key=lambda x: -x[0]):
        L.append(f"- [{r['category']}, {r['language']}] \"{r['text'][:140].replace(chr(10), ' ')}\" "
                 f"→ {core.explain(index, r)[:160]}")
    L += ["", "## Fix", "",
          f"Added {len(misses)} missed scams to the scam examples and {len(alarms)} false-alarm honest messages to the "
          f"honest examples → bundle `{bundle}`.", "",
          "## Gate", "", "| Check | Result |", "|---|---|"]
    L += [f"| {k} | {'pass' if v else '**fail**'} |" for k, v in g["checks"].items()]
    L += ["", f"Tests: {tests_line}. Scenario failures: {', '.join(scen['failures']) or 'none'}.",
          f"Dev recall at Caution {pct(dev_prev['recall_caution'])} → {pct(dev_new['recall_caution'])}; "
          f"dev High false alarms {pct(dev_prev['fpr_high'])} → {pct(dev_new['fpr_high'])}; real-SMS false alarms "
          f"{pct(sms_new)} (demo-safe {pct(sms_base)}).", "",
          f"**Result: {verdict}.** Best candidate is now **{after}**.", ""]
    (core.REPORTS / f"round_{n:02d}.md").write_text("\n".join(L), encoding="utf-8")

    hist = core.RUNS / "history.csv"
    core.RUNS.mkdir(exist_ok=True)
    new_file = not hist.exists()
    with open(hist, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerow({"round": n, "time": time.strftime("%Y-%m-%d %H:%M"), "candidate_before": best["name"],
                    "scams": int(scam.sum()), "honest": int((~scam).sum()),
                    "prefix_recall_caution": round(rec_c["value"], 4), "prefix_recall_high": round(rec_h, 4),
                    "prefix_false_alarms_caution": round(fa, 4), "misses": len(misses), "false_alarms": len(alarms),
                    "added_scam": len(misses), "added_honest": len(alarms),
                    "dev_recall_before": round(dev_prev["recall_caution"], 4),
                    "dev_recall_after": round(dev_new["recall_caution"], 4),
                    "real_sms_false_alarms_after": None if sms_new is None else round(sms_new, 4),
                    "gate": verdict, "failed_checks": "; ".join(k for k, v in g["checks"].items() if not v),
                    "candidate_after": after})
    print(f"round {n:02d}: before fix caught {pct(rec_c['value'])} (High {pct(rec_h)}), false alarms {pct(fa)}; "
          f"+{len(misses)} scams +{len(alarms)} honest; gate {verdict}; dev {pct(dev_prev['recall_caution'])} → "
          f"{pct(dev_new['recall_caution'])}; SMS {pct(sms_new)} (base {pct(sms_base)}); {time.time() - t0:.0f}s")

    if commit:
        msg = (f"Round {n:02d}: caught {pct(rec_c['value'])} before fix, {verdict}\n\n"
               f"Pre-fix recall at Caution {pct(rec_c['value'])}, High {pct(rec_h)}, false alarms {pct(fa)} "
               f"(synthetic data). Added {len(misses)} missed scams and {len(alarms)} false-alarm honest messages. "
               f"Dev recall {pct(dev_prev['recall_caution'])} -> {pct(dev_new['recall_caution'])}, real-SMS false "
               f"alarms {pct(sms_new)}. Gate: {verdict}.\n\n"
               "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
               "Claude-Session: https://claude.ai/code/session_01XsYRnbGZ62GkLdP8FwjyhU")
        subprocess.run(["git", "add", str(core.REPORTS), str(core.RUNS), str(bundle)], check=True)
        subprocess.run(["git", "commit", "-q", "-m", msg], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("round", type=int)
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    run(args.round, args.commit)


if __name__ == "__main__":
    main()
