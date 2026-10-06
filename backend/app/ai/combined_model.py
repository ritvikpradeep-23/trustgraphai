"""Your deepfake model: a trained real/fake layer on top of EfficientNet-B0.

EfficientNet-B0 (pretrained on ImageNet, from Hugging Face) turns a face into
1280 features; a small trained layer (the "head", one Linear layer) turns those
into a fake score. The backbone is FROZEN by default: only the head learns,
which needs little data and can't damage what EfficientNet already knows.
unfreeze_last_blocks() lets the last blocks adapt later, at a much lower
learning rate (see ai/train_video.py).

The head is trained by ai/train_video.py and saved to ai/models/efficientnet_head.pt.
"""
import copy
import logging

import numpy as np
import torch

from app.ai import efficientnet_wrapper as effnet

logger = logging.getLogger("trustgraph.deepfake")


def new_head() -> torch.nn.Linear:
    """The trainable part: 1280 EfficientNet features -> 1 logit (sigmoid gives the fake score)."""
    return torch.nn.Linear(effnet.FEATURE_SIZE, 1)


def save_head(head: torch.nn.Linear, path: str, **info):
    torch.save({"state_dict": head.state_dict(), **info}, path)


class EfficientNetDeepfakeModel:
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
