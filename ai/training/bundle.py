"""Save a candidate model as a bundle under models/candidate/<name>/.

A bundle holds everything that must change together, so it can be promoted
and rolled back as one unit by scripts/promote_model.py:

  <model files>       e.g. similarity_corpus.json, classifier.joblib
  risk_bands.json     Low/Caution/High cut-offs for the engine WITH this model,
                      set the same way as the live ones (src/trustgraph/evaluate.py)
  MODEL_CARD.md       what it is, what data, how it was tested, the limits
  manifest.json       training-data hash, date, library versions, seeds, files,
                      dev metrics (for the side-by-side shown before promotion)

Nothing outside models/candidate/ is written here.
"""
import hashlib
import json
import platform
import shutil
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import sklearn

CANDIDATES = Path("models/candidate")
SYNTHETIC = ("**All training and test data for this model is synthetic** (written by the generator in `eval/`). "
             "The numbers below show how it behaves on that data, not real-world accuracy.")


def live_bands() -> dict:
    """Cut-offs for the engine as currently loaded in this process, calibrated on
    the same held-out legit interactions as src/trustgraph/evaluate.py
    (Caution flags 10% of them, High 1%)."""
    from trustgraph.evaluate import CAUTION_FPR, HIGH_FPR, _fused_scores, _legit
    scores = _fused_scores(_legit("calibration"))
    return {"caution": float(np.quantile(scores, 1 - CAUTION_FPR)), "high": float(np.quantile(scores, 1 - HIGH_FPR))}


def _sha(path: Path) -> str:
    from eval.leakage import sha256 as line_ending_safe_sha256
    return line_ending_safe_sha256(path)


def write_bundle(name: str, files: dict[str, Path], targets: dict[str, str], bands: dict, *,
                 data_hash: str, n_train: int, seeds: dict, dev_metrics: dict, card: str,
                 requires: str = "", root: Path = CANDIDATES) -> Path:
    """files: {file name in bundle: local source}. targets: {file name: where
    promotion copies it, e.g. 'models/similarity_corpus.json'}."""
    out = root / name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for fname, src in files.items():
        shutil.copyfile(src, out / fname)
    (out / "risk_bands.json").write_text(json.dumps(bands, indent=2))
    targets = {**targets, "risk_bands.json": "models/risk_bands.json"}
    manifest = {
        "name": name, "created": date.today().isoformat(),
        "training_data_sha256": data_hash, "training_rows": n_train, "seeds": seeds,
        "library_versions": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                             "numpy": np.__version__, "joblib": joblib.__version__},
        "files": {f: {"target": targets[f], "sha256": _sha(out / f)} for f in [*files, "risk_bands.json"]},
        "dev_metrics": dev_metrics,
        "requires": requires,
        "synthetic_data": True,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=float))
    (out / "MODEL_CARD.md").write_text(f"# Model card: {name}\n\n> {SYNTHETIC}\n\n{card}\n", encoding="utf-8")
    return out
