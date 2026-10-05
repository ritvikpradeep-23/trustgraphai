"""Step 7: print the latest accuracy run and the trend over time.

    python show_report.py            # latest run + last 10 runs per detector
    python show_report.py --last 30  # longer trend
"""
import argparse
import csv

from detection_common import KINDS, load_manifest, used_batches
from run_cycle import HISTORY, LATEST


def trend(rows: list[dict], last: int) -> list[str]:
    out = []
    for kind in KINDS:
        mine = [r for r in rows if r["detector"] == kind][-last:]
        manifest = load_manifest(kind)
        left = len(manifest["batches"]) - len(used_batches(kind)) if manifest else 0
        out.append(f"\n{kind.capitalize()}: {len(mine)} run(s) shown, {left} unused test batch(es) left")
        if not mine:
            continue
        out.append(f"  {'run at':19}  {'batch':9}  {'n':>5}  {'accuracy':>8}  {'F1':>5}  {'ROC-AUC':>7}  model")
        for r in mine:
            auc = r["roc_auc"] and f"{float(r['roc_auc']):.3f}" or "n/a"
            out.append(f"  {r['run_at']:19}  {r['batch']:9}  {r['n']:>5}  {float(r['accuracy']):>8.1%}  "
                       f"{float(r['f1']):>5.2f}  {auc:>7}  {r['model']}")
        accs = [float(r["accuracy"]) for r in mine]
        if len(accs) > 1:
            out.append(f"  accuracy range {min(accs):.1%} to {max(accs):.1%}, mean {sum(accs) / len(accs):.1%}. "
                       "Runs with the same model differ only because the batches differ.")
    return out


LEARNING_HISTORY = HISTORY.parent / "learning" / "history.csv"


def learning_trend(last: int) -> list[str]:
    """The new-scam learning runs: how many new scams were caught BEFORE learning them."""
    if not LEARNING_HISTORY.exists():
        return ["\n# New-scam learning", "No learning runs yet (python learn_cycle.py, or the hourly schedule)."]
    with open(LEARNING_HISTORY, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))[-last:]
    out = ["\n# New-scam learning (new scams caught before learning them)",
           f"  {'run':15}  {'new scams':>9}  {'caught':>7}  {'learned':>7}  {'gate':9}  version"]
    total = caught = 0
    for r in rows:
        n = int(r["new_scams"] or 0)
        c = round(float(r["caught_before"]) * n) if r["caught_before"] else 0
        total, caught = total + n, caught + c
        out.append(f"  {r['run_at']:15}  {n:>9}  {c:>7}  {int(r['added_scams'] or 0):>7}  {r['gate']:9}  "
                   f"{r['new_version'] or '-'}")
    if total:
        out.append(f"  Overall: {caught} of {total} new scams caught before learning ({caught / total:.1%}). "
                   "Small samples of unverified reports: not real-world accuracy.")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--last", type=int, default=10)
    args = ap.parse_args(argv)
    if not LATEST.exists():
        print("No accuracy runs yet. Run: python run_cycle.py")
    else:
        print(LATEST.read_text(encoding="utf-8"))
        rows = []
        if HISTORY.exists():
            with open(HISTORY, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        print("# Trend", *trend(rows, args.last), sep="\n")
    print(*learning_trend(args.last), sep="\n")


if __name__ == "__main__":
    main()
