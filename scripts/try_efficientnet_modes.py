"""Run one image through all three deepfake modes and print what each gives.

    python scripts/try_efficientnet_modes.py --image path/to/face.jpg
    python scripts/try_efficientnet_modes.py                    # uses a drawn test image
    python scripts/try_efficientnet_modes.py --random-weights   # plumbing check, no download

Modes:
  mine          your TorchScript model at DEEPFAKE_MODEL_PATH (models/deepfake.pt)
  efficientnet  EfficientNet-B0 features + the trained head at EFFICIENTNET_HEAD_PATH
  both          the average of the two scores

A mode whose model is missing says so instead of printing a made-up score.
--random-weights uses an UNTRAINED EfficientNet-B0 of the same shape (and a
random head if none is trained): it only proves the code runs end to end.
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import Settings  # noqa: E402
from app.deepfake_engine import efficientnet_wrapper as effnet  # noqa: E402
from app.deepfake_engine.combined_model import (CombinedDeepfakeModel, EfficientNetDeepfakeModel,  # noqa: E402
                                                new_head, save_head)
from app.deepfake_engine.model import TorchScriptDeepfakeModel  # noqa: E402


def drawn_test_image() -> np.ndarray:
    """A simple drawn face-like picture (BGR), so the script runs without a photo."""
    img = np.full((240, 200, 3), (200, 210, 230), np.uint8)
    cv2.ellipse(img, (100, 120), (70, 95), 0, 0, 360, (150, 180, 220), -1)
    for x in (75, 125):
        cv2.circle(img, (x, 100), 9, (40, 40, 40), -1)
    cv2.ellipse(img, (100, 165), (28, 12), 0, 0, 180, (60, 60, 160), 3)
    return img


def use_random_weights(model_id: str):
    """Fill the wrapper's cache with an untrained EfficientNet-B0 (no download)."""
    from transformers import EfficientNetConfig, EfficientNetForImageClassification, EfficientNetImageProcessor
    config = EfficientNetConfig(image_size=224, width_coefficient=1.0, depth_coefficient=1.0, hidden_dim=1280,
                                num_labels=1000, id2label={i: f"class_{i}" for i in range(1000)})
    processor = EfficientNetImageProcessor(size={"height": 224, "width": 224}, do_center_crop=False)
    model = EfficientNetForImageClassification(config)
    # The library starts an untrained model with near-zero weights, so every
    # feature would come out 0. A standard random start keeps numbers flowing.
    for module in model.modules():
        if isinstance(module, torch.nn.Conv2d):
            torch.nn.init.kaiming_normal_(module.weight)
        elif isinstance(module, torch.nn.BatchNorm2d):
            torch.nn.init.ones_(module.weight)
    effnet._loaded[model_id] = (processor, model.eval())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--image", help="image file (a face crop works best)")
    ap.add_argument("--random-weights", action="store_true", help="untrained EfficientNet, no download")
    args = ap.parse_args(argv)
    s = Settings()
    image = cv2.imread(args.image) if args.image else drawn_test_image()
    if image is None:
        raise SystemExit(f"could not read {args.image}")
    print(f"Image: {args.image or 'drawn test face'} {image.shape[1]}x{image.shape[0]}")
    if args.random_weights:
        use_random_weights(s.efficientnet_model_id)
        print("!! --random-weights: UNTRAINED EfficientNet. Numbers below only prove the code runs.")

    # --- mine
    mine = None
    if s.deepfake_model_path and os.path.exists(s.deepfake_model_path):
        mine = TorchScriptDeepfakeModel(s.deepfake_model_path, s.deepfake_input_size)
        print(f"\n[mine] fake score: {mine.predict_fake_score(image):.4f}")
    else:
        print(f"\n[mine] not configured: no model at DEEPFAKE_MODEL_PATH ({s.deepfake_model_path or 'unset'})")

    # --- efficientnet
    try:
        features = effnet.extract_features(image, s.efficientnet_model_id)
    except OSError as exc:  # no internet, or huggingface.co blocked
        raise SystemExit(f"\nCould not download {s.efficientnet_model_id} from Hugging Face ({type(exc).__name__}). "
                         "Check your internet connection, or run with --random-weights to check the code "
                         "without downloading.") from None
    print(f"\n[efficientnet] features: {features.shape[0]} numbers, first 5: {[round(float(v), 4) for v in features[:5]]}")
    print(f"[efficientnet] ImageNet top-3 (not a deepfake verdict): {effnet.classify_imagenet(image, 3, s.efficientnet_model_id)}")
    head_path = s.efficientnet_head_path
    if not os.path.exists(head_path) and args.random_weights:
        head_path = os.path.join(tempfile.mkdtemp(), "random_head.pt")
        save_head(new_head(), head_path, note="random, untrained")
        print("[efficientnet] no trained head: using a RANDOM head for this plumbing check")
    eff = None
    if os.path.exists(head_path):
        eff = EfficientNetDeepfakeModel(head_path, s.efficientnet_model_id)
        frozen = all(not p.requires_grad for p in eff.backbone.parameters())
        print(f"[efficientnet] fake score: {eff.predict_fake_score(image):.4f}  (backbone frozen: {frozen})")
    else:
        print(f"[efficientnet] no deepfake score: train the head first (scripts/train_efficientnet_head.py); "
              f"looked for {head_path}")

    # --- both
    if mine and eff:
        both = CombinedDeepfakeModel("both", mine, eff, s.deepfake_weight_mine)
        branches = {k: round(v, 4) for k, v in both.scores_by_branch(image).items()}
        print(f"\n[both] fake score: {both.predict_fake_score(image):.4f}  (branches: {branches}, "
              f"weight mine {s.deepfake_weight_mine})")
    else:
        print("\n[both] needs both models: " + ", ".join(n for n, m in (("your model", mine), ("EfficientNet head", eff))
                                                       if not m) + " missing")


if __name__ == "__main__":
    main()
