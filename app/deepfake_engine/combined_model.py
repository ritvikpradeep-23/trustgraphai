"""Combine your own deepfake model with EfficientNet-B0.

Two pieces:

EfficientNetDeepfakeModel - transfer learning. EfficientNet-B0 (pretrained on
  ImageNet) turns a face into 1280 features; a small trained layer (the
  "head", one Linear layer) turns those into a fake score. The backbone is
  FROZEN by default: only the head learns, which needs little data and can't
  damage what EfficientNet already knows. unfreeze_last_blocks() lets the last
  blocks adapt later, at a much lower learning rate (see the training script).

CombinedDeepfakeModel - a simple ensemble with a mode:
  "mine"          your model only (models/deepfake.pt, TorchScript)
  "efficientnet"  EfficientNet + head only
  "both"          weighted average of the two fake scores
  Averaging scores works with your model as a closed TorchScript file (it only
  gives a score, not its internal features), keeps each model usable alone,
  and each branch keeps its own preprocessing.
"""
import copy
import logging

import numpy as np
import torch

from app.deepfake_engine import efficientnet_wrapper as effnet
from app.deepfake_engine.model import DeepfakeModel

logger = logging.getLogger("trustgraph.deepfake")
MODES = ("mine", "efficientnet", "both")


def new_head() -> torch.nn.Linear:
    """The trainable part: 1280 EfficientNet features -> 1 logit (sigmoid gives the fake score)."""
    return torch.nn.Linear(effnet.FEATURE_SIZE, 1)


def save_head(head: torch.nn.Linear, path: str, **info):
    torch.save({"state_dict": head.state_dict(), **info}, path)


class EfficientNetDeepfakeModel(DeepfakeModel):
    def __init__(self, head_path: str, model_id: str = effnet.MODEL_ID, freeze_backbone: bool = True):
        self.model_id = model_id
        _, full = effnet.load(model_id)
        saved = torch.load(head_path, map_location="cpu", weights_only=True)
        self.backbone = full.efficientnet  # the 1280-feature extractor, without the ImageNet layer
        if "backbone_state_dict" in saved:
            # Trained with --unfreeze-last: use the fine-tuned blocks the head was trained with,
            # on a private copy so the shared pretrained model stays unchanged.
            self.backbone = copy.deepcopy(self.backbone)
            self.backbone.load_state_dict(saved["backbone_state_dict"])
        self.head = new_head()
        self.head.load_state_dict(saved["state_dict"])
        self.head.eval()
        self.info = {k: v for k, v in saved.items() if k not in ("state_dict", "backbone_state_dict")}
        if freeze_backbone:
            self.freeze_backbone()

    def freeze_backbone(self):
        for p in self.backbone.parameters():
            p.requires_grad = False
        self.backbone.eval()

    def unfreeze_last_blocks(self, n: int = 2):
        """Let the last n blocks (plus the final conv) adapt during fine-tuning.
        The early blocks detect generic edges and textures and stay frozen."""
        self.freeze_backbone()
        encoder = self.backbone.encoder
        for module in [*encoder.blocks[-n:], encoder.top_conv, encoder.top_bn]:
            for p in module.parameters():
                p.requires_grad = True

    def features(self, face_bgr: np.ndarray) -> torch.Tensor:
        inputs = effnet.pixel_inputs(face_bgr, self.model_id)  # EfficientNet's own preprocessing
        return self.backbone(**inputs).pooler_output          # 1 x 1280

    def predict_fake_score(self, face_bgr: np.ndarray) -> float:
        with torch.inference_mode():
            return float(torch.sigmoid(self.head(self.features(face_bgr)))[0, 0])


class CombinedDeepfakeModel(DeepfakeModel):
    def __init__(self, mode: str, mine: DeepfakeModel | None = None, efficientnet: DeepfakeModel | None = None,
                 weight_mine: float = 0.5):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
        if mode in ("mine", "both") and mine is None:
            raise ValueError(f"mode {mode!r} needs your model (DEEPFAKE_MODEL_PATH)")
        if mode in ("efficientnet", "both") and efficientnet is None:
            raise ValueError(f"mode {mode!r} needs the EfficientNet head (EFFICIENTNET_HEAD_PATH)")
        self.mode, self.mine, self.efficientnet, self.weight_mine = mode, mine, efficientnet, weight_mine

    def scores_by_branch(self, face_bgr: np.ndarray) -> dict:
        """Each branch's score separately (handy for debugging and the demo script)."""
        out = {}
        if self.mode in ("mine", "both"):
            out["mine"] = self.mine.predict_fake_score(face_bgr)
        if self.mode in ("efficientnet", "both"):
            out["efficientnet"] = self.efficientnet.predict_fake_score(face_bgr)
        return out

    def predict_fake_score(self, face_bgr: np.ndarray) -> float:
        s = self.scores_by_branch(face_bgr)
        if self.mode == "both":
            return self.weight_mine * s["mine"] + (1 - self.weight_mine) * s["efficientnet"]
        return s[self.mode]
