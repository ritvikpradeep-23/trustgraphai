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


def load_deepfake_model(settings: Settings) -> tuple[DeepfakeModel | None, str]:
    """(model, status), where status is "configured", "mock" or "not_configured".
    A real model file always wins over the mock, so fake scores can't appear
    while a real model is installed."""
    path = settings.deepfake_model_path
    if path:
        if os.path.exists(path):
            try:
                model = TorchScriptDeepfakeModel(path, settings.deepfake_input_size)
                if settings.deepfake_mock:
                    logger.warning("DEEPFAKE_MOCK ignored: a real model is configured")
                return model, "configured"
            except Exception as exc:  # corrupt or wrong file type
                logger.error("could not load deepfake model %s: %s", path, exc)
        else:
            logger.warning("DEEPFAKE_MODEL_PATH=%s does not exist", path)
    if settings.deepfake_mock:
        logger.warning("Using the MOCK deepfake model: scores are meaningless (demo only)")
        return MockDeepfakeModel(), "mock"
    return None, "not_configured"
