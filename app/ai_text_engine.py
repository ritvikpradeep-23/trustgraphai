"""The AI-written text detector inside the API.

Loads the model that train_text.py saved (AI_TEXT_MODEL_DIR, default
models/text_detector) once at startup. Without a trained model there is no
score: the endpoint answers 503 and /api/score simply leaves out ai_written.
"""
import logging
import os

from app.config import Settings

logger = logging.getLogger("trustgraph.ai_text")


def load_text_detector(settings: Settings):
    """(detector, status), where status is "configured" or "not_configured"."""
    path = settings.ai_text_model_dir
    if not path or not os.path.isdir(path):
        logger.info("No AI-text model at %s (train it with train_text.py)", path or "AI_TEXT_MODEL_DIR (unset)")
        return None, "not_configured"
    try:
        from text_detector import TextDetector  # pulls in transformers
        return TextDetector(path), "configured"
    except Exception as exc:  # corrupt or half-written model folder
        logger.error("could not load the AI-text model at %s: %s", path, exc)
        return None, "not_configured"


def check(detector, text: str, settings: Settings) -> dict:
    """{"result": "likely_ai" | "likely_human", "ai_score": 0-1}. The text itself is never logged."""
    score = float(detector.score([text])[0])
    return {"result": "likely_ai" if score >= settings.ai_text_threshold else "likely_human",
            "ai_score": round(score, 4)}
