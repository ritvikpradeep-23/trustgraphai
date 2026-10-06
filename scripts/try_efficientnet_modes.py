"""Run one image through the deepfake model (EfficientNet-B0 + your trained layer).

    python scripts/try_efficientnet_modes.py --image path/to/face.jpg
    python scripts/try_efficientnet_modes.py                    # uses a drawn test image
    python scripts/try_efficientnet_modes.py --random-weights   # plumbing check, no download

Prints EfficientNet's 1280 features, its ImageNet top-3 (a check that the model
works, NOT a deepfake verdict) and the fake score from your trained layer at
EFFICIENTNET_HEAD_PATH (models/efficientnet_head.pt). Without a trained layer it
says so instead of printing a made-up score. --random-weights uses an UNTRAINED
EfficientNet-B0 of the same shape (and a random layer if none is trained): it
only proves the code runs end to end.
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]
from app.ai import efficientnet_wrapper as effnet  # noqa: E402
from app.ai.combined_model import EfficientNetDeepfakeModel, new_head, save_head  # noqa: E402


def drawn_test_image() -> np.ndarray:
    """A simple drawn face-like picture (BGR), so the script runs without a photo."""
    img = np.full((240, 200, 3), (200, 210, 230), np.uint8)
    cv2.ellipse(img, (100, 120), (70, 95), 0, 0, 360, (150, 180, 220), -1)
    for x in (75, 125):
        cv2.circle(img, (x, 100), 9, (40, 40, 40), -1)
    cv2.ellipse(img, (100, 165), (28, 12), 0, 0, 180, (60, 60, 160), 3)
    return img


def use_random_weights(model_id: str = effnet.MODEL_ID):
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
    image = cv2.imread(args.image) if args.image else drawn_test_image()
    if image is None:
        raise SystemExit(f"could not read {args.image}")
    print(f"Image: {args.image or 'drawn test face'} {image.shape[1]}x{image.shape[0]}")
    if args.random_weights:
        use_random_weights()
        print("!! --random-weights: UNTRAINED EfficientNet. Numbers below only prove the code runs.")
    try:
        features = effnet.extract_features(image)
    except OSError as exc:  # no internet, or huggingface.co blocked
        raise SystemExit(f"\nCould not download {effnet.MODEL_ID} from Hugging Face ({type(exc).__name__}). "
                         "Check your internet connection, or run with --random-weights.") from None
    print(f"\nfeatures: {features.shape[0]} numbers, first 5: {[round(float(v), 4) for v in features[:5]]}")
    print(f"ImageNet top-3 (not a deepfake verdict): {effnet.classify_imagenet(image, 3)}")
    head_path = os.environ.get("EFFICIENTNET_HEAD_PATH", str(ROOT / "models" / "efficientnet_head.pt"))
    if not os.path.exists(head_path) and args.random_weights:
        head_path = os.path.join(tempfile.mkdtemp(), "random_head.pt")
        save_head(new_head(), head_path, note="random, untrained")
        print("no trained layer: using a RANDOM one for this plumbing check")
    if os.path.exists(head_path):
        model = EfficientNetDeepfakeModel(head_path)
        frozen = all(not p.requires_grad for p in model.backbone.parameters())
        print(f"fake score: {model.predict_fake_score(image):.4f}  (backbone frozen: {frozen})")
    else:
        print(f"no deepfake score: train your layer first (python train_video.py); looked for {head_path}")


if __name__ == "__main__":
    main()
