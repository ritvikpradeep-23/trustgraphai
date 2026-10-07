"""Load the trained AI engines once, and only if they can really run.

An engine is used only when BOTH are true:
  - the AI packages are installed (pip install -r ai/requirements-ai.txt), and
  - its trained model exists (made on your computer by ai/train_text.py).
Otherwise its check stays unavailable and no score is invented.

Model locations (relative to the repository root; override with environment variables):
  AI_TEXT_MODEL_DIR       ai/models/text_detector          (ai/train_text.py)
  AI_THRESHOLD            0.5: a score at or above this counts as AI-written
"""
import logging
import os
import threading
from pathlib import Path

logger = logging.getLogger("trustgraph.ai")
REPO = Path(__file__).resolve().parents[3]          # backend/app/ai/engines.py -> repository root

_lock = threading.Lock()
_cache: dict = {}


def _path(env: str, default: str) -> Path:
    p = Path(os.environ.get(env, default))
    return p if p.is_absolute() else REPO / p


def threshold() -> float:
    return float(os.environ.get("AI_THRESHOLD", "0.5"))


def _load(name: str, make):
    """make() once per process; None (cached too) if packages or model are missing."""
    with _lock:
        if name not in _cache:
            try:
                _cache[name] = make()
            except ImportError as exc:
                logger.info("%s engine off: AI packages not installed (%s)", name, exc.name)
                _cache[name] = None
            except Exception as exc:  # corrupt or half-written model files
                logger.error("%s engine failed to load: %s", name, exc)
                _cache[name] = None
    return _cache[name]


def text_engine():
    """The fine-tuned AI-written text model, or None."""
    def make():
        folder = _path("AI_TEXT_MODEL_DIR", "ai/models/text_detector")
        if not (folder / "config.json").exists():
            return None
        from app.ai.text_detector import TextDetector
        return TextDetector(str(folder))
    return _load("text", make)


def reset():
    """Forget loaded engines (tests, or after training a new model)."""
    with _lock:
        _cache.clear()


# ---------------------------------------------------------------- scoring
def score_text(text: str) -> float:
    return float(text_engine().score([text])[0])
