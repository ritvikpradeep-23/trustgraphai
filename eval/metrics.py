"""Calibration and metrics with bootstrap 95% confidence intervals.

Thresholds come from dev legit messages only (same method as
src/trustgraph/evaluate.py: Caution flags 10% of legit, High flags 1%). They
are returned and written to reports/, never to models/.
"""
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

CAUTION_FPR = 0.10
HIGH_FPR = 0.01
N_BOOT = 1000


def calibrate(legit_scores) -> dict:
    s = np.asarray(legit_scores, dtype=float)
    return {"caution": float(np.quantile(s, 1 - CAUTION_FPR)), "high": float(np.quantile(s, 1 - HIGH_FPR))}


def _ci(values, rng, stat, n=N_BOOT) -> tuple[float, float]:
    values = np.asarray(values)
    if len(values) == 0:
        return float("nan"), float("nan")
    boots = [stat(values[rng.integers(0, len(values), len(values))]) for _ in range(n)]
    return float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def rate(flags, rng) -> dict:
    """Share of True with a bootstrap CI (used for recall and false-positive rate)."""
    flags = np.asarray(flags, dtype=float)
    lo, hi = _ci(flags, rng, np.mean)
    return {"value": float(flags.mean()) if len(flags) else float("nan"), "lo": lo, "hi": hi, "n": int(len(flags))}


def ranking(scores, labels, rng) -> dict:
    """ROC-AUC and PR-AUC of a score, with bootstrap CIs."""
    scores, labels = np.asarray(scores, dtype=float), np.asarray(labels, dtype=int)
    out = {"roc_auc": float(roc_auc_score(labels, scores)), "pr_auc": float(average_precision_score(labels, scores))}
    roc, pr = [], []
    for _ in range(N_BOOT):
        i = rng.integers(0, len(scores), len(scores))
        if labels[i].min() == labels[i].max():
            continue
        roc.append(roc_auc_score(labels[i], scores[i]))
        pr.append(average_precision_score(labels[i], scores[i]))
    out["roc_auc_ci"] = [float(np.percentile(roc, 2.5)), float(np.percentile(roc, 97.5))]
    out["pr_auc_ci"] = [float(np.percentile(pr, 2.5)), float(np.percentile(pr, 97.5))]
    return out


def precision(scam_hits: int, legit_hits: int, rng, n_scam: int, n_legit: int) -> dict:
    """Precision at a threshold. Depends on the scam:legit ratio of this synthetic set."""
    flags = np.array([1] * scam_hits + [0] * legit_hits)
    p = scam_hits / max(scam_hits + legit_hits, 1)
    lo, hi = _ci(flags, rng, np.mean) if len(flags) else (float("nan"), float("nan"))
    return {"value": p, "lo": lo, "hi": hi, "note": f"at {n_scam} scam : {n_legit} legit in this synthetic test set"}


def evaluate(rows: list[dict], scores: list[dict], key: str, bands: dict, seed: int = 0) -> dict:
    """Headline metrics for one score column on one split."""
    rng = np.random.default_rng(seed)
    s = np.array([sc[key] for sc in scores])
    is_scam = np.array([r["label"] == "scam" for r in rows])
    out = {"thresholds": bands, "n_scam": int(is_scam.sum()), "n_legit": int((~is_scam).sum())}
    for band in ("caution", "high"):
        hit = s >= bands[band]
        out[f"recall_{band}"] = rate(hit[is_scam], rng)
        out[f"fpr_{band}"] = rate(hit[~is_scam], rng)
        out[f"precision_{band}"] = precision(int(hit[is_scam].sum()), int(hit[~is_scam].sum()), rng,
                                             int(is_scam.sum()), int((~is_scam).sum()))
        for nov in ("seen", "unseen"):
            m = is_scam & np.array([r["novelty"] == nov for r in rows])
            out[f"recall_{band}_{nov}"] = rate(hit[m], rng)
    out.update(ranking(s, is_scam.astype(int), rng))
    return out


def by_group(rows: list[dict], scores: list[dict], key: str, bands: dict, field: str, label: str = "scam",
             seed: int = 0) -> list[dict]:
    """Recall (or false-positive rate for legit) at both bands, per value of a field."""
    rng = np.random.default_rng(seed)
    s = np.array([sc[key] for sc in scores])
    groups = {}
    for i, r in enumerate(rows):
        if r["label"] == label:
            groups.setdefault(r[field], []).append(i)
    table = []
    for g, idx in sorted(groups.items()):
        idx = np.array(idx)
        row = {field: g, "n": len(idx)}
        if field == "category":
            row["novelty"] = rows[idx[0]]["novelty"]
        for band in ("caution", "high"):
            r_ = rate(s[idx] >= bands[band], rng)
            row[f"{band}"] = r_["value"]
            row[f"{band}_lo"], row[f"{band}_hi"] = r_["lo"], r_["hi"]
        table.append(row)
    return table
