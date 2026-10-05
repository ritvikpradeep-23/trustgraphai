"""The deepfake model behind a one-method interface.

DeepfakeModel.predict_fake_score(face_bgr) -> float between 0 (real) and 1
(fake). Anything that implements it can be plugged in. The real adapter loads
a TorchScript file (no weights are bundled with this project); the mock
exists only for demos and is labelled in every response.
"""
import logging
import os
from abc import ABC, abstractmethod

import cv2
import numpy as np

from app.config import Settings

logger = logging.getLogger("trustgraph.deepfake")

# The usual ImageNet normalisation. Must match how the model was trained:
# see models/README.md.
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class DeepfakeModel(ABC):
    is_mock = False

    @abstractmethod
    def predict_fake_score(self, face_bgr: np.ndarray) -> float:
        """Probability-like score that this face crop is fake, 0..1."""


class TorchScriptDeepfakeModel(DeepfakeModel):
    """Loads a TorchScript file (torch.jit.save output). TorchScript needs no
    Python model code to run, so any team's trained model can be dropped in."""

    def __init__(self, path: str, input_size: int):
        import torch  # imported here so the server starts fast when no model is configured
        self._torch = torch
        self.input_size = input_size
        self.model = torch.jit.load(path, map_location="cpu").eval()

    def _preprocess(self, face_bgr: np.ndarray):
        rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)  # OpenCV is BGR, models are trained on RGB
        rgb = cv2.resize(rgb, (self.input_size, self.input_size), interpolation=cv2.INTER_AREA)
        x = (rgb.astype(np.float32) / 255.0 - _MEAN) / _STD
        return self._torch.from_numpy(x.transpose(2, 0, 1)).unsqueeze(0)  # 1 x 3 x S x S

    def predict_fake_score(self, face_bgr: np.ndarray) -> float:
        with self._torch.inference_mode():
            out = self.model(self._preprocess(face_bgr)).flatten()
        if out.numel() == 1:   # one logit
            return float(self._torch.sigmoid(out[0]))
        if out.numel() == 2:   # [real, fake] logits
            return float(self._torch.softmax(out, dim=0)[1])
        raise ValueError(f"model returned {out.numel()} values; expected 1 or 2")


class MockDeepfakeModel(DeepfakeModel):
    """DEMO ONLY. The score is derived from pixel values and means nothing.
    Every API response produced with it carries "mock": true."""
    is_mock = True

    def predict_fake_score(self, face_bgr: np.ndarray) -> float:
        return float(int(face_bgr.mean() * 997) % 100) / 100.0


def _load_mine(settings: Settings) -> DeepfakeModel | None:
    """Your own model: a TorchScript file at DEEPFAKE_MODEL_PATH."""
    path = settings.deepfake_model_path
    if not path:
        return None
    if not os.path.exists(path):
        logger.warning("DEEPFAKE_MODEL_PATH=%s does not exist", path)
        return None
    try:
        return TorchScriptDeepfakeModel(path, settings.deepfake_input_size)
    except Exception as exc:  # corrupt or wrong file type
        logger.error("could not load deepfake model %s: %s", path, exc)
        return None


def _load_efficientnet(settings: Settings) -> DeepfakeModel | None:
    """EfficientNet-B0 plus the trained real/fake head at EFFICIENTNET_HEAD_PATH.
    Without a trained head there is no deepfake score, so no model."""
    path = settings.efficientnet_head_path
    if not path or not os.path.exists(path):
        logger.warning("EFFICIENTNET_HEAD_PATH=%s does not exist: train it with scripts/train_efficientnet_head.py", path)
        return None
    try:
        from app.deepfake_engine.combined_model import EfficientNetDeepfakeModel  # pulls in transformers
        return EfficientNetDeepfakeModel(path, settings.efficientnet_model_id)
    except Exception as exc:  # download blocked, corrupt head file...
        logger.error("could not load EfficientNet deepfake model: %s", exc)
        return None


def load_deepfake_model(settings: Settings) -> tuple[DeepfakeModel | None, str]:
    """(model, status), where status is "configured", "mock" or "not_configured".

    DEEPFAKE_MODE picks the model: "mine" (default, your TorchScript file),
    "efficientnet" (EfficientNet-B0 + trained head) or "both" (average of the
    two). A real model always wins over the mock, so fake scores can't appear
    while a real model is installed."""
    mode = settings.deepfake_mode
    model = None
    if mode == "mine":
        model = _load_mine(settings)
    elif mode == "efficientnet":
        model = _load_efficientnet(settings)
    elif mode == "both":
        mine, eff = _load_mine(settings), _load_efficientnet(settings)
        if mine and eff:
            from app.deepfake_engine.combined_model import CombinedDeepfakeModel
            model = CombinedDeepfakeModel("both", mine, eff, settings.deepfake_weight_mine)
        else:
            logger.warning("DEEPFAKE_MODE=both needs both models; missing: %s",
                           ", ".join(n for n, m in (("your model", mine), ("EfficientNet head", eff)) if not m))
    else:
        logger.error("DEEPFAKE_MODE=%s is not one of mine, efficientnet, both", mode)

    if model is not None:
        if settings.deepfake_mock:
            logger.warning("DEEPFAKE_MOCK ignored: a real model is configured")
        return model, "configured"
    if settings.deepfake_mock:
        logger.warning("Using the MOCK deepfake model: scores are meaningless (demo only)")
        return MockDeepfakeModel(), "mock"
    return None, "not_configured"
