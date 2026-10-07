"""Bridge to the repository's existing four-signal engine, not a new model.

Loads only the original promoted model, never a rejected candidate. Missing
packages/weights leave it unavailable and preserve database matching.
"""
from functools import lru_cache
import logging
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
AI = ROOT / "ai"  # the AI folder: models/, src/trustgraph and data/precedent live here
URGENCY = re.compile(r"\b(urgent(?:ly)?|immediately|right now|asap|today|tonight|quickly|hurry|final (?:notice|warning)|act now)\b", re.I)
logger = logging.getLogger("trustgraph.scam")


@lru_cache(maxsize=1)
def engine():
    if not (AI / "models/anomaly_isolation_forest.joblib").is_file():
        return None
    try:
        source = str(AI / "src")
        if source not in sys.path:
            sys.path.insert(0, source)
        from trustgraph import paths
        paths.DEFAULT_DIR = str(AI / "models")
        from trustgraph.pipeline import score_interaction
        # Resolve the baseline paths without changing process working directory.
        from trustgraph.precedent import detector as precedent
        precedent.REPORTS_PATH = str(AI / "data/precedent/reports.json")
        from trustgraph.anomaly import detector as anomaly
        anomaly._load_bundle()
        # Levels use the app's one score rule (app/core/risk_bands.py), not the
        # model's calibration file, so the website and extension agree.
        from app.core.risk_bands import band
        return score_interaction, band
    except Exception as error:
        logger.warning("Original scam engine unavailable (%s); database matcher remains active.", type(error).__name__)
        return None


def analyze(text, sender=None, url=None):
    loaded = engine()
    if not loaded:
        return None
    try:
        # Urgency is observed wording; call/payment history is NOT invented.
        interaction = {"message_text": text, "urgency_score": len(URGENCY.findall(text))}
        if sender:
            interaction["sender"] = sender
        if url:
            interaction["url"] = url
        signals, fused = loaded[0](interaction)
        if not math.isfinite(fused.score) or not 0 <= fused.score <= 1:
            return None
        return {"score": fused.score, "level": loaded[1](fused.score).upper(),
                "signals": {s.signal_name: s.score for s in signals},
                "reasons": [fused.explanation,
                    "Original TrustGraph engine: learned anomaly signal plus deterministic continuity, similarity and precedent. Synthetic training; not a calibrated fraud probability. Missing interaction history is not fabricated."]}
    except Exception as error:
        logger.warning("Original scam inference unavailable (%s).", type(error).__name__)
        return None
