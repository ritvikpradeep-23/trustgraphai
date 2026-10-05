"""GET /api/accuracy: the latest results of the scheduled accuracy routine.

Reads reports/history.csv (written by run_cycle.py) and says how many unused
test batches are left. It never runs or changes anything.
"""
import csv

from fastapi import APIRouter

router = APIRouter(tags=["accuracy"])
NOTE = ("Each number comes from one held-out batch of a public dataset, scored once. "
        "It is not real-world accuracy.")


@router.get("/api/accuracy")
def accuracy() -> dict:
    from detection_common import KINDS, load_manifest, used_batches
    from run_cycle import HISTORY
    rows = []
    if HISTORY.exists():
        with open(HISTORY, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    out = {"note": NOTE}
    for kind in KINDS:
        mine = [r for r in rows if r["detector"] == kind]
        manifest = load_manifest(kind)
        latest = None
        if mine:
            r = mine[-1]
            latest = {"run_at": r["run_at"], "batch": r["batch"], "n": int(r["n"]), "model": r["model"],
                      **{k: (float(r[k]) if r[k] else None) for k in ("accuracy", "precision", "recall", "f1",
                                                                      "roc_auc")},
                      **{k: int(r[k]) for k in ("tn", "fp", "fn", "tp")}}
        out[kind] = {"latest": latest, "runs": len(mine),
                     "unused_batches": len(manifest["batches"]) - len(used_batches(kind)) if manifest else None}
    return out
