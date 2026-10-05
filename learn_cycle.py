"""The new-scam learning routine. A plain Python script; it never calls Claude.

    python learn_cycle.py              # one run (the schedule runs it every LEARN_INTERVAL_HOURS)
    python learn_cycle.py --dry-run    # measure only: nothing is learned or marked as used

Where new examples come from (all stay on this computer):
  - data/learning/inbox.jsonl   added with add_examples.py or POST /api/feedback
                                (scams, and honest messages that were wrongly flagged)
  - data/scam_reports.json      scams reported through POST /api/text/report
Each example is used once.

Each run:
 1. Collects examples not used before. Fewer than MIN_NEW_EXAMPLES: nothing to do.
 2. TEST BEFORE LEARNING: scores them with the current best version at its own
    cut-offs. The share of new scams it already catches is the live answer to
    "how often does it catch a scam it hasn't seen?".
 3. LEARN: missed scams join the scam examples; honest messages it flagged join
    the honest examples. (Honest ones matter: learning from scam reports alone
    made results worse in the report-once experiment.)
 4. Rebuild, recalibrate on dev rounds 01-02, then the same gate as the
    improvement rounds: all tests pass, all demo scenarios keep their result,
    dev recall not lower, dev High false alarms not higher, real UK SMS false
    alarms at most +2 points. The SMS file must be present, or nothing is accepted.
 5. Passed: it becomes the best version (models/candidate/learn_<time>/). The live
    engine only changes when you promote it, or automatically if AUTO_PROMOTE is
    true in detection_config.json (a backup is made first; --rollback undoes it).
 6. Writes reports/learning/latest.md and reports/learning/history.csv;
    logs to logs/learn_cycle.log.
"""
import argparse
import copy
import csv
import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)  # the engine, dev rounds and candidates use paths relative to the project folder
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

import numpy as np  # noqa: E402

from detection_common import LOGS_DIR, load_config  # noqa: E402
from run_cycle import RunLock  # noqa: E402

log = logging.getLogger("learn_cycle")
LEARN_DIR = Path("data/learning")
INBOX = LEARN_DIR / "inbox.jsonl"
USED = LEARN_DIR / "used.json"
REJECTED = LEARN_DIR / "rejected.jsonl"  # examples whose version failed the gate, kept for you to review
SCAM_REPORTS = Path("data/scam_reports.json")   # the API's report store (app/config.py reports_path)
BEST = Path("runs/learning_best.json")
OUT = Path("reports/learning")
HISTORY_FIELDS = ["run_at", "base_version", "new_scams", "caught_before", "new_honest", "flagged_before", "retried",
                  "added_scams", "added_honest", "dev_recall_before", "dev_recall_after", "real_sms_false_alarms",
                  "gate", "failed_checks", "new_version", "promoted"]
DEFAULTS = {"LEARN_INTERVAL_HOURS": 1, "MIN_NEW_EXAMPLES": 5, "AUTO_PROMOTE": False,
            "DEV_RECALL_TOLERANCE": 0.0}  # 0 = dev recall may not drop at all (the improvement rounds' rule)


def learning_config() -> dict:
    from detection_common import check_interval
    cfg = {**DEFAULTS, **load_config().get("learning", {})}
    cfg["LEARN_INTERVAL_HOURS"] = check_interval(cfg["LEARN_INTERVAL_HOURS"])  # whole hours, at least 1
    return cfg


def key(text: str, label: str) -> str:
    """Same message with the same label = same example, whatever the spacing or case."""
    return hashlib.sha1(f"{label}\n{' '.join(text.lower().split())}".encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- collecting
def collect() -> list[dict]:
    """Every inbox example and API scam report not used before (duplicates dropped)."""
    used = set(json.loads(USED.read_text(encoding="utf-8"))) if USED.exists() else set()
    items = []
    if INBOX.exists():
        for line in INBOX.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                items.append({"text": d["text"], "label": d["label"], "retry": bool(d.get("retry")),
                              "scam_type": d.get("scam_type") or "reported scam", "source": d.get("source", "inbox")})
    if SCAM_REPORTS.exists():
        for d in json.loads(SCAM_REPORTS.read_text(encoding="utf-8")):
            items.append({"text": d["text"], "label": "scam", "scam_type": "reported scam", "retry": False,
                          "source": f"report ({d.get('source', 'api')})"})
    out = {}
    for it in items:
        k = key(it["text"], it["label"])
        if not it["text"].strip() or it["label"] not in ("scam", "legit") or k in used:
            continue
        if k in out:  # the same message twice (e.g. its original line plus a retry): one example,
            out[k]["retry"] = out[k]["retry"] or it["retry"]  # and a retry if either copy is one
        else:
            out[k] = {**it, "key": k, "id": f"learn_{k[:12]}"}
    return list(out.values())


def mark_used(items: list[dict]):
    used = json.loads(USED.read_text(encoding="utf-8")) if USED.exists() else []
    LEARN_DIR.mkdir(parents=True, exist_ok=True)
    tmp = USED.with_suffix(".tmp")
    tmp.write_text(json.dumps(used + [it["key"] for it in items]), encoding="utf-8")
    os.replace(tmp, USED)


# ---------------------------------------------------------------- versions
def current_best(core) -> dict:
    """The latest accepted learning version; before the first one, the best improvement-round version."""
    if BEST.exists():
        info = json.loads(BEST.read_text(encoding="utf-8"))
        from trustgraph.similarity import detector as sim
        scams, legit, _ = sim.load_corpus(str(Path(info["dir"].replace("\\", "/")) / "similarity_corpus.json"))
        return {"name": info["name"], "dir": info["dir"], "scams": scams, "legit": legit}
    return core.load_best()


def pct(x):
    return "n/a" if x is None else f"{x:.1%}"


# ---------------------------------------------------------------- one run
def run(dry_run: bool = False) -> dict:
    from routine import core   # imported here: loading the engine takes a few seconds
    from eval import metrics
    cfg = learning_config()
    items = collect()
    if len(items) < cfg["MIN_NEW_EXAMPLES"]:
        log.info("%d new example(s), fewer than MIN_NEW_EXAMPLES=%d: nothing to learn yet.", len(items),
                 cfg["MIN_NEW_EXAMPLES"])
        return {"status": "skipped", "reason": f"only {len(items)} new example(s)"}

    stamp = time.strftime("%Y%m%d_%H%M%S")
    best = current_best(core)
    index = core.index_for(best)
    dev = core.dev_rows()
    dev_prev = core.dev_recall(index, dev)
    bands = dev_prev["bands"]

    # ---- test before learning
    rows = [{"id": it["id"], "text": it["text"], "label": it["label"]} for it in items]
    s = core.scores(index, rows, f"learn_{stamp}")
    caution = metrics.hits(s, bands["caution"])
    # The catch rate counts only examples seen for the first time (retried ones were tested before).
    fresh = np.array([not it["retry"] for it in items])
    scam = np.array([r["label"] == "scam" for r in rows])
    caught = float(caution[scam & fresh].mean()) if (scam & fresh).any() else None
    flagged = float(caution[~scam & fresh].mean()) if (~scam & fresh).any() else None
    n_scam = int((scam & fresh).sum())
    misses = [it for i, it in enumerate(items) if it["label"] == "scam" and not caution[i]]
    alarms = [it for i, it in enumerate(items) if it["label"] == "legit" and caution[i]]
    log.info("Before learning: caught %s of %d new scams, flagged %s of %d new honest messages (at Caution); "
             "%d retried example(s) not counted.", pct(caught), n_scam, pct(flagged), int((~scam & fresh).sum()),
             int((~fresh).sum()))
    result = {"status": "measured", "new_scams": n_scam, "caught_before": caught,
              "new_honest": int((~scam & fresh).sum()), "retried": int((~fresh).sum()),
              "flagged_before": flagged, "base_version": best["name"]}
    if dry_run:
        return result

    # ---- learn
    new = {"name": f"learn_{stamp}", "scams": copy.deepcopy(best["scams"]), "legit": list(best["legit"])}
    for it in misses:
        new["scams"].setdefault(it["scam_type"], []).append(it["text"])
    new["legit"] += [it["text"] for it in alarms]
    verdict, g, dev_new, sms_new, promoted = "nothing to add", None, dev_prev, None, False
    if misses or alarms:
        new_index = core.index_for(new)
        dev_new = core.dev_recall(new_index, dev)
        sms_new = core.sms_false_alarms(new_index, dev_new["bands"])
        sms_base = core.sms_false_alarms(core.index_for(core.baseline()),
                                         core.dev_recall(core.index_for(core.baseline()), dev)["bands"])
        card = (f"## What it is\n{best['name']} plus {len(misses)} new scams it missed and {len(alarms)} honest "
                f"messages it flagged, from the learning inbox and API reports.\n\n## How it was tested\nDev rounds "
                f"01-02 (synthetic data): scams caught {pct(dev_new['recall_caution'])} (was "
                f"{pct(dev_prev['recall_caution'])}). Real UK SMS honest texts flagged {pct(sms_new)}.\n\n## Limits\n"
                f"Reported examples are not verified by anyone; the gate limits the harm a wrong one can do.\n\n"
                f"## Promote\n`python scripts/promote_model.py models/candidate/{new['name']}` (dry run), "
                f"then add `--yes`. `--rollback` undoes it.\n")
        bundle = core.save_bundle(new["name"], new, new_index, dev_new, dev_prev, "pending gate", card)
        with core.with_index(new_index):
            scen = core.scenario_check(new_index, json.loads((bundle / "risk_bands.json").read_text()))
        tests_ok, tests_line = core.run_tests(str(bundle))
        g = core.gate(tests_ok, scen, dev_new, dev_prev, sms_new, sms_base)
        tol = float(cfg["DEV_RECALL_TOLERANCE"])
        if tol > 0:  # only if you chose to allow a small drop (e.g. 0.01 = one point)
            g["checks"].pop("dev recall at Caution not lower")
            g["checks"][f"dev recall at Caution at most {tol:.1%} lower"] = (
                dev_new["recall_caution"] >= dev_prev["recall_caution"] - tol - 1e-9)
        g["checks"]["real UK SMS check file present (eval/external/sms.tsv)"] = sms_new is not None
        g["passed"] = all(g["checks"].values())
        verdict = "accepted" if g["passed"] else "rejected"
        if g["passed"]:
            BEST.parent.mkdir(exist_ok=True)
            BEST.write_text(json.dumps({"name": new["name"], "dir": bundle.as_posix(),
                                        "dev_recall_caution": dev_new["recall_caution"],
                                        "real_sms_false_alarms": sms_new}, indent=1), encoding="utf-8")
            if cfg["AUTO_PROMOTE"]:
                from scripts.promote_model import promote
                promoted = promote(bundle, Path("."), yes=True) == 0
        else:  # nothing is lost: what it would have learned is kept for you to look at
            with open(REJECTED, "a", encoding="utf-8") as f:
                for it in misses + alarms:
                    f.write(json.dumps({k: it[k] for k in ("text", "label", "scam_type", "source")} |
                                       {"rejected_run": stamp}, ensure_ascii=False) + "\n")
    mark_used(items)  # each example is used once, whatever the gate decided

    result.update({"added_scams": len(misses), "added_honest": len(alarms), "gate": verdict,
                   "failed_checks": [k for k, v in (g or {"checks": {}})["checks"].items() if not v],
                   "dev_recall_before": dev_prev["recall_caution"], "dev_recall_after": dev_new["recall_caution"],
                   "real_sms_false_alarms": sms_new, "new_version": new["name"] if verdict == "accepted" else "",
                   "promoted": promoted, "status": verdict})
    write_reports(result, misses, alarms, g, stamp)
    return result


def write_reports(r: dict, misses, alarms, g, stamp: str):
    OUT.mkdir(parents=True, exist_ok=True)
    hist = OUT / "history.csv"
    new_file = not hist.exists()
    with open(hist, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HISTORY_FIELDS, extrasaction="ignore")
        if new_file:
            w.writeheader()
        w.writerow({**r, "run_at": stamp, "failed_checks": "; ".join(r["failed_checks"]),
                    **{k: (round(r[k], 4) if isinstance(r.get(k), float) else r.get(k))
                       for k in ("caught_before", "flagged_before", "dev_recall_before", "dev_recall_after",
                                 "real_sms_false_alarms")}})
    L = [f"# New-scam learning run {stamp}", "",
         f"Version before: **{r['base_version']}**.", "",
         "## Test before learning (the live new-scam catch rate)", "",
         f"- New scams already caught at Caution or above: **{pct(r['caught_before'])}** of {r['new_scams']}.",
         f"- New honest messages flagged at Caution: {pct(r['flagged_before'])} of {r['new_honest']}.", "",
         f"## Learned\n\n{len(misses)} missed scams and {len(alarms)} flagged honest messages "
         f"(their text stays in data/learning and the new version's examples, on this computer only).", ""]
    if g:
        L += ["## Gate", "", "| Check | Result |", "|---|---|"]
        L += [f"| {k} | {'pass' if v else '**fail**'} |" for k, v in g["checks"].items()]
        L += ["", f"Dev recall at Caution {pct(r['dev_recall_before'])} → {pct(r['dev_recall_after'])} (synthetic "
              f"data); real UK SMS honest texts flagged {pct(r['real_sms_false_alarms'])}.", ""]
    L += [f"**Result: {r['gate']}.**"]
    if r["gate"] == "rejected":
        L += ["", f"The {len(misses) + len(alarms)} examples it would have learned are saved in "
              "`data/learning/rejected.jsonl`. They are not retried automatically: check them, delete lines you "
              "don't trust, then `python add_examples.py --retry-rejected` (with more examples, the next version "
              "may pass)."]
    if r["gate"] == "accepted":
        L += ["", f"New best version: `models/candidate/{r['new_version']}`. " +
              ("It was promoted to the live engine: restart the server to use it." if r["promoted"] else
               f"To use it: `python scripts/promote_model.py models/candidate/{r['new_version']} --yes`, then restart "
               "the server. `--rollback` undoes it.")]
    L += ["", "Reported examples are unverified, and a handful per run is a small sample: read the trend in "
          "`reports/learning/history.csv`, not one run. Not real-world accuracy.", ""]
    (OUT / "latest.md").write_text("\n".join(L), encoding="utf-8")


def setup_logging():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if sys.stdout is None:  # pythonw (Task Scheduler): no console
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(LOGS_DIR / "learn_cycle.stderr.log", "a", encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handlers = [logging.FileHandler(LOGS_DIR / "learn_cycle.log", encoding="utf-8"), logging.StreamHandler(sys.stdout)]
    for h in handlers:
        h.setFormatter(fmt)
    log.handlers[:] = handlers
    log.setLevel(logging.INFO)


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="measure the new examples only; learn nothing")
    args = ap.parse_args(argv)
    setup_logging()
    with RunLock(LOGS_DIR / "learn_cycle.lock", load_config().get("LOCK_STALE_HOURS", 6)) as lock:
        if not lock.held:
            log.warning("Another learning run is still going. Skipping this run.")
            return {"status": "skipped", "reason": "another run is going"}
        try:
            result = run(args.dry_run)
        except Exception:
            log.exception("Learning run failed")
            raise
        log.info("Learning run: %s", {k: v for k, v in result.items() if k != "failed_checks"})
        return result


if __name__ == "__main__":
    main()
