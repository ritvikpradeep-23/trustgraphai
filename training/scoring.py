"""Score candidates on dev (and the real-SMS check) at matched false-alarm rates.

Every candidate gets its own Caution/High cut-offs, set on dev honest
messages (about 10% and 1% flagged), and is then compared on recall. Never
at the old fixed cut-offs: a model could look better just by flagging more.

The text-only setting is used throughout (what the website sends): the
continuity, precedent and anomaly scores don't depend on the candidate, so
they are computed once and cached; only similarity and the classifier change.
"""
import csv
import math
import pickle
from pathlib import Path

import numpy as np

from eval import engine, metrics
from trustgraph.similarity import detector as sim

CACHE = Path("training/.cache")
SMS_PATH = Path("eval/external/sms.tsv")


def _cached(name: str, make):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.pkl"
    if path.exists():
        return pickle.loads(path.read_bytes())
    value = make()
    path.write_bytes(pickle.dumps(value))
    return value


def sms_rows() -> list[dict]:
    """Real UK texts (UCI SMS Spam Collection): a false-alarm CHECK only, never
    used to train or to set cut-offs. Returns [] if the file isn't on disk."""
    if not SMS_PATH.exists():
        return []
    with open(SMS_PATH, encoding="utf-8") as f:
        return [{"id": f"sms{i}", "text": t, "label": "legit" if lab == "ham" else "spam"}
                for i, (lab, t) in enumerate(csv.reader(f, delimiter="\t"))]


def base_signals(name: str, rows: list[dict]) -> dict[str, np.ndarray]:
    """Continuity, precedent and anomaly scores plus red-flag evidence per
    message (none of these depend on the reference examples or classifier)."""
    def make():
        sc = engine.score_rows(rows, "text_only")
        flags = [sim._flag_hits(" ".join(r["text"].split())[:sim.MAX_CHARS]) for r in rows]
        return {"continuity": np.array([s["continuity"] for s in sc]),
                "precedent": np.array([s["precedent"] for s in sc]),
                "anomaly": np.array([s["anomaly"] for s in sc]),
                "flag_keep": np.array([math.prod(1.0 - e for e, _ in f) for f in flags])}
    return _cached(f"base_{name}_{len(rows)}", make)


def similarity_scores(index: dict, rows: list[dict], flag_keep: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Same maths as similarity/detector.py components(), for many messages at
    once: (wording-match score, full similarity score)."""
    texts = [" ".join(r["text"].split())[:sim.MAX_CHARS] for r in rows]
    if index.get("normalized"):
        texts = [sim.normalize(t) for t in texts]
    q = index["vectorizer"].transform(texts)
    scam = (q @ index["scam"].T).toarray().max(axis=1) / 2.0
    legit = (q @ index["legit"].T).toarray().max(axis=1) / 2.0
    match = 1.0 / (1.0 + np.exp(-((scam - legit) - sim.MARGIN_MID) / sim.MARGIN_SCALE))
    match = np.where(scam < sim.MIN_SCAM_SIMILARITY, 0.0, np.minimum(match, sim.MATCH_CAP))
    return match, 1.0 - (1.0 - match) * flag_keep


def fuse(base: dict, similarity: np.ndarray, classifier: np.ndarray | None = None, weight: float = 0.0) -> np.ndarray:
    """Noisy-OR, as in fusion.py (all current weights are 1.0)."""
    keep = (1 - base["continuity"]) * (1 - similarity) * (1 - base["precedent"]) * (1 - base["anomaly"])
    if classifier is not None:
        keep = keep * (1 - weight * classifier)
    return 1.0 - keep


def compare(rows: list[dict], scores: np.ndarray, seed: int = 0) -> dict:
    """Recall at this score's own dev cut-offs, with bootstrap 95% CIs."""
    legit = [s for s, r in zip(scores, rows) if r["label"] == "legit"]
    bands = metrics.calibrate(legit)
    out = metrics.evaluate(rows, [{"s": float(s)} for s in scores], "s", bands, seed)
    out["by_language"] = {g["language"]: g["caution"] for g in
                          metrics.by_group(rows, [{"s": float(s)} for s in scores], "s", bands, "language", seed=seed)}
    return out


def sms_false_alarms(scores: np.ndarray, rows: list[dict], bands: dict, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    legit = np.array([r["label"] == "legit" for r in rows])
    return metrics.rate(metrics.hits(scores[legit], bands["caution"]), rng)


def summary_row(name: str, res: dict, sms: dict | None = None) -> dict:
    """One line of a before/after table."""
    row = {"candidate": name,
           "recall_caution": res["recall_caution"]["value"], "lo": res["recall_caution"]["lo"],
           "hi": res["recall_caution"]["hi"],
           "recall_known_types": res["recall_caution_seen"]["value"],
           "recall_types_engine_had_no_examples_for": res["recall_caution_unseen"]["value"],
           "fpr_caution": res["fpr_caution"]["value"], "fpr_high": res["fpr_high"]["value"],
           "recall_high": res["recall_high"]["value"], "roc_auc": res["roc_auc"]}
    row.update({f"recall_{k}": v for k, v in res["by_language"].items()})
    if sms is not None:
        row["real_sms_false_alarms"] = sms["value"]
    return row
