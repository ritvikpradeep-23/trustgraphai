"""Shared pieces of the fast routine: hash check, scoring, the gate, bundles.

Everything is text-only (what the website sends). Continuity, precedent and
anomaly don't change between candidates, so they are computed once per batch
and cached; only the similarity examples change from round to round.

Cut-offs: each candidate gets its own Caution/High cut-offs, set on the
honest messages of the development rounds 01-02 (~10% and ~1% flagged).
These are used for every round report and every comparison. The bundle's
risk_bands.json is set the way the live engine's is (src/trustgraph/evaluate.py),
so the website and the named demo scenarios behave consistently.

All numbers are on synthetic data, not real-world accuracy.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from eval import metrics
from routine.generate import DEV, FINAL, MANIFEST, OUT, sha256
from training import scoring
from training.bundle import live_bands, write_bundle
from trustgraph.similarity import detector as sim
from trustgraph.similarity.corpus import LEGIT_MESSAGES, SCAM_SCRIPTS

RUNS = Path("runs")
BEST = RUNS / "best.json"
REPORTS = Path("reports/fast")
CANDIDATES = Path("models/candidate")
SMS_TOLERANCE = 0.02  # real-SMS false alarms may rise at most 2 points over demo-safe


# ------------------------------------------------------------ data
def verify_manifest(path: Path = MANIFEST) -> dict:
    """Every round file must match its SHA-256 in the manifest."""
    manifest = json.loads(Path(path).read_text())
    for name, info in manifest["files"].items():
        actual = sha256(Path(path).parent / name)
        if actual != info["sha256"]:
            raise RuntimeError(f"Round file changed since it was frozen: {name} "
                               f"(manifest {info['sha256'][:12]}…, now {actual[:12]}…)")
    return manifest


def load_round(n: int, allow_final: bool = False) -> list[dict]:
    if n in FINAL and not allow_final:
        raise ValueError(f"round {n:02d} is the frozen final test; only scripts/finalize.py may read it")
    with open(OUT / f"round_{n:02d}.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def dev_rows() -> list[dict]:
    return [r for n in DEV for r in load_round(n)]


# ------------------------------------------------------------ candidates
def baseline() -> dict:
    """The demo-safe engine: built-in examples, live cut-offs."""
    return {"name": "demo-safe", "dir": None, "scams": SCAM_SCRIPTS, "legit": list(LEGIT_MESSAGES)}


def load_best() -> dict:
    if not BEST.exists():
        return baseline()
    info = json.loads(BEST.read_text())
    if info["dir"] is None:
        return baseline()
    folder = Path(info["dir"].replace("\\", "/"))  # saved on Windows with backslashes
    scams, legit, _ = sim.load_corpus(str(folder / "similarity_corpus.json"))
    return {"name": info["name"], "dir": info["dir"], "scams": scams, "legit": legit}


def index_for(cand: dict) -> dict:
    return sim.build_index(cand["scams"], cand["legit"], False)


def scores(index: dict, rows: list[dict], cache_name: str) -> np.ndarray:
    base = scoring.base_signals(cache_name, rows)
    return scoring.fuse(base, scoring.similarity_scores(index, rows, base["flag_keep"])[1])


def dev_cutoffs(index: dict, dev: list[dict]) -> tuple[dict, np.ndarray]:
    s = scores(index, dev, "fast_dev")
    legit = np.array([r["label"] == "legit" for r in dev])
    return metrics.calibrate(s[legit]), s


def dev_recall(index: dict, dev: list[dict]) -> dict:
    bands, s = dev_cutoffs(index, dev)
    scam = np.array([r["label"] == "scam" for r in dev])
    return {"bands": bands,
            "recall_caution": float(metrics.hits(s[scam], bands["caution"]).mean()),
            "recall_high": float(metrics.hits(s[scam], bands["high"]).mean()),
            "fpr_caution": float(metrics.hits(s[~scam], bands["caution"]).mean()),
            "fpr_high": float(metrics.hits(s[~scam], bands["high"]).mean())}


def sms_false_alarms(index: dict, bands: dict) -> float | None:
    rows = scoring.sms_rows()
    if not rows:
        return None
    s = scores(index, rows, "sms")
    legit = np.array([r["label"] == "legit" for r in rows])
    return float(metrics.hits(s[legit], bands["caution"]).mean())


def with_index(index: dict):
    """Context manager: run the live pipeline with this similarity index."""
    class _Swap:
        def __enter__(self):
            self.saved = sim._index
            sim._index = index

        def __exit__(self, *exc):
            sim._index = self.saved
    return _Swap()


def explain(index: dict, row: dict) -> str:
    from eval.engine import explain as engine_explain
    with with_index(index):
        return engine_explain(row, "text_only")


# ------------------------------------------------------------ gate
def scenario_check(index: dict, bands: dict) -> dict:
    """All named demo scenarios: scams Caution or above, honest controls Low."""
    from trustgraph.fusion import risk_band
    from trustgraph.pipeline import score_interaction
    from trustgraph.scenarios import SCENARIOS
    failures = []
    with with_index(index):
        for name, kind, inter in SCENARIOS:
            band = risk_band(score_interaction(dict(inter))[1].score, bands)
            if (kind == "scam") != (band != "Low"):
                failures.append(f"{name} ({kind}) -> {band}")
    return {"n": len(SCENARIOS), "failures": failures}


def run_tests(model_dir: str | None) -> tuple[bool, str]:
    """The whole test suite, with the engine loading from this bundle."""
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(["src", "."])}  # ";" on Windows, ":" elsewhere
    if model_dir:
        env["TRUSTGRAPH_MODEL_DIR"] = model_dir
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], env=env, capture_output=True, text=True)
    return p.returncode == 0, p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[-300:]


def gate(tests_ok: bool, scenarios: dict, dev_new: dict, dev_prev: dict, sms_new, sms_base) -> dict:
    """A candidate is accepted only if every check passes."""
    checks = {
        "all tests pass": tests_ok,
        f"all {scenarios['n']} named scenarios keep their result": not scenarios["failures"],
        "dev recall at Caution not lower": dev_new["recall_caution"] >= dev_prev["recall_caution"] - 1e-9,
        "dev High false alarms not higher": dev_new["fpr_high"] <= dev_prev["fpr_high"] + 1e-9,
        "real-SMS false alarms at most +2 points over demo-safe":
            True if sms_new is None or sms_base is None else sms_new <= sms_base + SMS_TOLERANCE + 1e-9,
    }
    return {"checks": checks, "passed": all(checks.values())}


# ------------------------------------------------------------ bundles
def save_bundle(name: str, cand: dict, index: dict, dev_m: dict, base_m: dict, verdict: str, card: str) -> Path:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "similarity_corpus.json"
        path.write_text(json.dumps({"scam_scripts": cand["scams"], "legit_messages": cand["legit"],
                                    "normalized": False}, ensure_ascii=False, indent=1), encoding="utf-8")
        with with_index(index):
            bands = live_bands()
        added = [t for v in cand["scams"].values() for t in v] + cand["legit"]
        return write_bundle(name, {"similarity_corpus.json": path},
                            {"similarity_corpus.json": "models/similarity_corpus.json"}, bands,
                            data_hash=__import__("hashlib").sha256("\n".join(added).encode()).hexdigest(),
                            n_train=len(added), seeds={"rounds_generator": 0},
                            dev_metrics={**{k: v for k, v in dev_m.items() if k != "bands"},
                                         "current_engine": {k: v for k, v in base_m.items() if k != "bands"},
                                         "verdict": verdict},
                            card=card, root=CANDIDATES)
