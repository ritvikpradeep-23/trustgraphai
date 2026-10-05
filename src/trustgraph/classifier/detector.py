"""Classifier signal: wording learned from labeled scam and honest messages.

A fifth signal, OFF unless the environment variable TRUSTGRAPH_CLASSIFIER=1
is set. When on, the pipeline appends it after the four existing signals.
It loads models/classifier.joblib (put there by scripts/promote_model.py),
or the file named by TRUSTGRAPH_CLASSIFIER_MODEL.

Interaction field: message_text. Trained on synthetic messages only.
"""
import os

import joblib

from trustgraph.classifier.model import scores, top_terms
from trustgraph.signal import RiskSignal
from trustgraph.textnorm import readable

FLAG = "TRUSTGRAPH_CLASSIFIER"
MODEL_PATH = "models/classifier.joblib"
MAX_CHARS = 5000
_bundle = None


def enabled() -> bool:
    return os.environ.get(FLAG) == "1"


def _load():
    global _bundle
    if _bundle is None:
        path = os.environ.get("TRUSTGRAPH_CLASSIFIER_MODEL", MODEL_PATH)
        _bundle = joblib.load(path) if os.path.exists(path) else False
    return _bundle


def fusion_weight() -> float:
    bundle = _load()
    return bundle["fusion_weight"] if bundle else 0.0


def classifier_score(interaction: dict) -> RiskSignal:
    text = interaction.get("message_text")
    if not isinstance(text, str) or not text.strip():
        return RiskSignal(signal_name="classifier", score=0.0, explanation="No message text to compare")
    bundle = _load()
    if not bundle:
        return RiskSignal(signal_name="classifier", score=0.0, explanation="Classifier model not installed")
    text = " ".join(text.split())[:MAX_CHARS]
    score = float(scores(bundle, [text])[0])
    terms = [readable(t) for t in top_terms(bundle, text)]
    if score >= 0.5 and terms:
        explanation = "Message: wording like labeled scams (" + ", ".join(f"'{t}'" for t in terms) + ")"
    elif score >= 0.5:
        explanation = "Message: wording like labeled scams"
    else:
        explanation = "Message: wording like labeled honest messages"
    return RiskSignal(signal_name="classifier", score=score, explanation=explanation)
