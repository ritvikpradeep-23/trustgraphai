"""Load the trained AI engines once, and only if they can really run.

An engine is used only when BOTH are true:
  - the AI packages are installed (pip install -r requirements-ai.txt), and
  - its trained model exists (made on your computer by train_text.py / train_video.py).
Otherwise its check stays unavailable and no score is invented.

Model locations (repository root by default; override with environment variables):
  AI_TEXT_MODEL_DIR       models/text_detector          (train_text.py)
  EFFICIENTNET_HEAD_PATH  models/efficientnet_head.pt   (train_video.py)
  AI_THRESHOLD            0.5: a score at or above this counts as AI-written / fake
"""
import logging
import os
import tempfile
import threading
from pathlib import Path

logger = logging.getLogger("trustgraph.ai")
REPO = Path(__file__).resolve().parents[3]          # backend/app/ai/engines.py -> repository root
FRAMES_PER_VIDEO = 16                                # same as the accuracy routine (detection_config.json)
FACE_MARGIN = 0.2

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
        folder = _path("AI_TEXT_MODEL_DIR", "models/text_detector")
        if not (folder / "config.json").exists():
            return None
        from app.ai.text_detector import TextDetector
        return TextDetector(str(folder))
    return _load("text", make)


def video_engine():
    """EfficientNet-B0 + your trained head (and the face detector), or None."""
    def make():
        head = _path("EFFICIENTNET_HEAD_PATH", "models/efficientnet_head.pt")
        if not head.exists():
            return None
        from app.ai.combined_model import EfficientNetDeepfakeModel
        from app.ai.face_detector import FaceDetector
        return {"model": EfficientNetDeepfakeModel(str(head)), "faces": FaceDetector(FACE_MARGIN), "head": head.name}
    return _load("video", make)


def reset():
    """Forget loaded engines (tests, or after training a new model)."""
    with _lock:
        _cache.clear()


# ---------------------------------------------------------------- scoring
def score_text(text: str) -> float:
    return float(text_engine().score([text])[0])


def score_faces(images) -> dict:
    """images: OpenCV BGR arrays or PIL images (frames). Largest face per frame,
    each scored, then averaged. No face in any frame -> no score."""
    import numpy as np
    eng = video_engine()
    faces = []
    for img in images:
        bgr = np.asarray(img.convert("RGB"))[:, :, ::-1].copy() if hasattr(img, "convert") else img
        face = eng["faces"].largest_face(bgr)
        if face is not None:
            faces.append(face)
    if not faces:
        return {"score": None, "frames": len(images), "faces": 0}
    scores = [eng["model"].predict_fake_score(f) for f in faces]
    return {"score": float(np.mean(scores)), "frames": len(images), "faces": len(faces)}


def score_video_file(fileobj, suffix: str = ".mp4") -> dict:
    """An uploaded video: 16 frames spread over the whole clip, then score_faces()."""
    from app.ai.frame_extractor import extract_evenly
    fd, tmp = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as out:
            while chunk := fileobj.read(1 << 20):
                out.write(chunk)
        return score_faces(extract_evenly(tmp, FRAMES_PER_VIDEO))
    finally:
        Path(tmp).unlink(missing_ok=True)  # the upload is never kept
