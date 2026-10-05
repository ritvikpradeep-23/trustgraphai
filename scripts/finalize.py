"""Final step of the fast routine: score the frozen test rounds 13-14 ONCE.

    PYTHONPATH=src:. python scripts/finalize.py

1. Check every round file (including 13-14) against its SHA-256 manifest.
2. Score rounds 13-14 with the best candidate and with the demo-safe engine,
   each at its own cut-offs set on dev rounds 01-02 (~10% / ~1% of honest
   messages flagged): recall per scam type, false alarms, bootstrap 95% CIs,
   the 10 worst remaining misses with the engine's explanation.
3. Write reports/fast/final_test.json and reports/fast/final_summary.md.
4. Promote nothing; print the commands for you to run.

Refuses to run twice: after the test result has been seen, nothing may change.
All numbers are on synthetic data, not real-world accuracy.
"""
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path[:0] = ["src", "."]
from eval import metrics  # noqa: E402
from routine import core  # noqa: E402
from routine.generate import FINAL  # noqa: E402

RESULT = core.REPORTS / "final_test.json"
SUMMARY = core.REPORTS / "final_summary.md"


def pct(x):
    return "n/a" if x is None else f"{x:.1%}"


def ci(r):
    return f"{pct(r['value'])} [{pct(r['lo'])}, {pct(r['hi'])}]"


def evaluate(cand: dict, rows: list[dict], dev: list[dict]) -> dict:
    index = core.index_for(cand)
    dev_m = core.dev_recall(index, dev)
    bands = dev_m["bands"]
    s = core.scores(index, rows, "fast_final_13_14")
    scam = np.array([r["label"] == "scam" for r in rows])
    rng = np.random.default_rng(0)
    out = {"name": cand["name"], "bands": bands, "dev_recall_caution": dev_m["recall_caution"]}
    for band in ("caution", "high"):
        hit = metrics.hits(s, bands[band])
        out[f"recall_{band}"] = metrics.rate(hit[scam], rng)
        out[f"false_alarms_{band}"] = metrics.rate(hit[~scam], rng)
    out.update(metrics.ranking(s, scam.astype(int), rng))
    caution = metrics.hits(s, bands["caution"])
    per_cat, per_lang = {}, {}
    for i, r in enumerate(rows):
        if r["label"] != "scam":
            continue
        c = per_cat.setdefault(r["category"], {"n": 0, "caught": 0, "in_corpus": r["in_corpus"]})
        c["n"] += 1
        c["caught"] += int(caution[i])
        g = per_lang.setdefault(r["language"], {"n": 0, "caught": 0})
        g["n"] += 1
        g["caught"] += int(caution[i])
    out["per_category"], out["per_language"] = per_cat, per_lang
    misses = sorted((float(s[i]), r) for i, r in enumerate(rows) if scam[i] and not caution[i])
    out["n_missed"] = len(misses)
    out["worst_misses"] = [{"score": round(sc, 3), "category": r["category"], "language": r["language"],
                            "evasion": r["evasion_type"], "text": r["text"].replace("\n", " ")[:160],
                            "engine_explanation": core.explain(index, r)[:200]} for sc, r in misses[:10]]
    out["real_sms_false_alarms"] = core.sms_false_alarms(index, bands)
    return out


def history() -> list[dict]:
    with open(core.RUNS / "history.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_summary(res: dict):
    base, best, hist = res["demo-safe"], res["best"], history()
    L = ["# TrustGraph fast routine: final summary", "",
         "> **All numbers are on synthetic data** (AI-written messages, fake placeholders), except the real UK SMS "
         "false-alarm check. They show how the engine behaves on this data, **not real-world accuracy**.", "",
         f"Frozen final test: rounds 13-14 ({res['n_scam']} scams across {res['n_types']} types, {res['n_honest']} honest "
         f"messages), verified against the SHA-256 manifest and scored **once** on {res['date']}. Never used for fixes or "
         "tuning. Each engine uses its own cut-offs, set on dev rounds 01-02 to flag ~10% (Caution) and ~1% (High) of "
         "honest messages.", "",
         "## Before-fix recall on each new round (synthetic data)", "",
         "Each improvement round was scored **before** the engine learned from it, so this is the curve that shows "
         "learning. The bar is scams caught at Caution or above.", "", "```"]
    for h in hist:
        v = float(h["prefix_recall_caution"])
        L.append(f"round {int(h['round']):02d}  {'#' * round(v * 40):<40s} {v:6.1%}  {h['gate']:<8s} (engine: {h['candidate_before']})")
    L += ["```", ""]
    first, rest = [float(h["prefix_recall_caution"]) for h in hist[:2]], [float(h["prefix_recall_caution"]) for h in hist[2:]]
    L += [f"Rounds 03-04 averaged **{np.mean(first):.1%}**; rounds 05-12 averaged **{np.mean(rest):.1%}** (synthetic data). "
          "The curve is **not smooth**: each round leans on a different window of scam types, so a round heavy in types "
          "the engine hasn't learned yet (round 07, 11) dips. After round 05 it stopped rising steadily; the gain came "
          "mostly from the first two rounds of learning. "
          f"{sum(h['gate'] == 'accepted' for h in hist)} of {len(hist)} rounds' fixes passed the gate; the rest were "
          "refused (real-SMS false alarms or a drop on dev).", "",
          "## Final test, rounds 13-14 (synthetic data)", "",
          "| | Demo-safe engine | Best candidate (" + best["name"] + ") |", "|---|---|---|",
          f"| Scams caught at Caution or above | {ci(base['recall_caution'])} | **{ci(best['recall_caution'])}** |",
          f"| Scams caught at High | {ci(base['recall_high'])} | {ci(best['recall_high'])} |",
          f"| Honest messages flagged at Caution | {ci(base['false_alarms_caution'])} | {ci(best['false_alarms_caution'])} |",
          f"| Honest messages flagged at High | {ci(base['false_alarms_high'])} | {ci(best['false_alarms_high'])} |",
          f"| ROC-AUC | {base['roc_auc']:.3f} | {best['roc_auc']:.3f} |",
          f"| Real UK SMS honest texts flagged (real data) | {pct(base['real_sms_false_alarms'])} | {pct(best['real_sms_false_alarms'])} |", "",
          "### Per scam type (caught at Caution, synthetic data)", "",
          "| Scam type | Engine had examples before? | Demo-safe | Best candidate |", "|---|---|---|---|"]
    for cat in sorted(best["per_category"], key=lambda c: best["per_category"][c]["caught"] / best["per_category"][c]["n"]):
        b, a = base["per_category"][cat], best["per_category"][cat]
        L.append(f"| {cat} | {a['in_corpus']} | {b['caught']}/{b['n']} | {a['caught']}/{a['n']} |")
    L += ["", "By language (best candidate, synthetic data): " + ", ".join(
        f"{lang} {v['caught']}/{v['n']}" for lang, v in sorted(best["per_language"].items())) + ".", "",
          "### 10 worst remaining misses (best candidate, with the engine's own explanation)", ""]
    for m in best["worst_misses"]:
        L.append(f"- [{m['category']}, {m['language']}] \"{m['text'][:120]}\" → {m['engine_explanation'][:120]}")
    gain = best["recall_caution"]["value"] - base["recall_caution"]["value"]
    L += ["", "## What improved", "",
          f"- Learning the missed scams from 6 accepted rounds raised scams caught on the untouched final test from "
          f"{pct(base['recall_caution']['value'])} to {pct(best['recall_caution']['value'])} ({gain:+.1%}, synthetic data), "
          f"with honest false alarms {pct(base['false_alarms_caution']['value'])} → {pct(best['false_alarms_caution']['value'])}.",
          "- Real-UK-SMS false alarms stayed within 2 points of the demo-safe engine at every accepted round (gate).",
          "- All 24 named demo scenarios kept their result and all tests passed at every accepted round.", "",
          "## What still fails", "",
          f"- {best['n_missed']} of {res['n_scam']} final-test scams are still missed (synthetic data); the weakest types are at "
          "the top of the per-type table.",
          "- Soft scams with no ask at all (a friendly \"wrong number\", \"are you free?\") read like honest messages: wording "
          "can't catch them; sender history (continuity, precedent) has to.",
          "- Hinglish and Manglish are weaker than English; the red-flag rules are English wording.",
          "- Eight proposed red-flag rules (`proposed_rules.md`) were not applied, so this test measures the engine without them.", "",
          "## Five honest bullets for the judges", "",
          f"1. We ran 10 improvement rounds, each on a fresh batch of 180 messages the engine had never seen, scoring each "
          f"one **before** fixing anything; before-fix catches went from about {np.mean(first):.0%} to about {np.mean(rest):.0%} "
          "(synthetic data).",
          "2. Every fix had to pass a safety gate: all tests, all 24 demo scenarios, no drop on a fixed development set, and "
          "no more than +2 points of false alarms on 4,827 real UK text messages. Four rounds' fixes were refused.",
          f"3. On a locked final test (rounds 13-14, used once), the improved engine caught {pct(best['recall_caution']['value'])} "
          f"of scams vs {pct(base['recall_caution']['value'])} for the starting engine, at "
          f"{pct(best['false_alarms_caution']['value'])} false alarms on honest messages (synthetic data).",
          "4. All test messages are synthetic, written by the same AI that built the detector, so these numbers flatter it; "
          "they are not real-world accuracy. The only real data is the UK SMS false-alarm check.",
          "5. What it can't do yet: catch scams that make no request at all, or match English quality in Hinglish and "
          "Manglish. Real reported scams and real honest messages are the next step.", "",
          "## Commands (run these yourself)", "", "```",
          "python -m pytest tests/                                          # all tests",
          "$env:PYTHONPATH=\"src;.\"                                          # Windows PowerShell",
          f"python scripts/promote_model.py models/candidate/{best['name']}       # dry run: shows the comparison",
          f"python scripts/promote_model.py models/candidate/{best['name']} --yes # promote (backs up models/ first)",
          "python scripts/promote_model.py --rollback                       # undo a promotion",
          "python run_website.py                                            # start the demo website",
          "```", "",
          "To run the website on the demo-safe engine instead: `git checkout demo-safe` (the tag; on your computer), "
          "start the server, then `git checkout claude/new-session-ftqy5g` to come back. To try the best candidate without "
          f"promoting it: `$env:TRUSTGRAPH_MODEL_DIR=\"models/candidate/{best['name']}\"` and then start the server.", ""]
    SUMMARY.write_text("\n".join(L), encoding="utf-8")


def main():
    if RESULT.exists():
        raise SystemExit(f"Refusing: the final test was already run ({RESULT}). After its result has been seen, nothing "
                         "may change; a new final test needs new frozen rounds.")
    t0 = time.time()
    core.verify_manifest()
    rows = [r for n in FINAL for r in core.load_round(n, allow_final=True)]
    dev = core.dev_rows()
    best = core.load_best()
    res = {"date": time.strftime("%Y-%m-%d %H:%M"), "rounds": list(FINAL),
           "n_scam": sum(r["label"] == "scam" for r in rows), "n_honest": sum(r["label"] == "legit" for r in rows),
           "n_types": len({r["category"] for r in rows if r["label"] == "scam"}),
           "demo-safe": evaluate(core.baseline(), rows, dev), "best": evaluate(best, rows, dev)}
    core.REPORTS.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(res, indent=1, default=float))
    write_summary(res)
    b, a = res["demo-safe"], res["best"]
    print(f"FINAL TEST (rounds 13-14, synthetic data, run once): demo-safe caught {pct(b['recall_caution']['value'])} "
          f"at {pct(b['false_alarms_caution']['value'])} false alarms; {a['name']} caught "
          f"{pct(a['recall_caution']['value'])} [{pct(a['recall_caution']['lo'])}, {pct(a['recall_caution']['hi'])}] at "
          f"{pct(a['false_alarms_caution']['value'])} false alarms. Real SMS {pct(b['real_sms_false_alarms'])} -> "
          f"{pct(a['real_sms_false_alarms'])}. ({time.time() - t0:.0f}s)")
    print(f"Summary: {SUMMARY}")
    print(f"Nothing promoted. To promote yourself: python scripts/promote_model.py models/candidate/{a['name']} --yes")


if __name__ == "__main__":
    main()
