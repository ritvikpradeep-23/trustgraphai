"""Pretrained EfficientNet-B0 from Hugging Face (google/efficientnet-b0).

Two functions:
  extract_features(image)  -> 1280 numbers that describe the image. The
                              deepfake layer (combined_model.py) learns real vs
                              fake from these.
  classify_imagenet(image) -> EfficientNet's own guesses from the 1,000
                              everyday ImageNet classes ("wig", "jersey"...).
                              Useful to check the model works; it is NOT a
                              deepfake verdict.

The model is public: no Hugging Face account, token or API key is needed. It
is downloaded once (~21 MB) on first use, cached on disk by the transformers
library, and loaded only once per process.
"""
import threading

import numpy as np

MODEL_ID = "google/efficientnet-b0"
FEATURE_SIZE = 1280

_lock = threading.Lock()
_loaded: dict = {}  # model_id -> (processor, model); filled on first use


def load(model_id: str = MODEL_ID):
    """(image processor, classification model), loaded once and then reused.

    EfficientNetForImageClassification is EfficientNetModel (the feature
    extractor, at .efficientnet) plus ImageNet's final layer, so one download
    serves both functions in this file."""
    with _lock:
        if model_id not in _loaded:
            from transformers import AutoImageProcessor, EfficientNetForImageClassification  # heavy, so imported late
            processor = AutoImageProcessor.from_pretrained(model_id)
            model = EfficientNetForImageClassification.from_pretrained(model_id).eval()
            _loaded[model_id] = (processor, model)
    return _loaded[model_id]


def to_pil(image):
    """Accept a file path, a PIL image, or an OpenCV image (NumPy array in BGR
    colour order, which is what OpenCV gives us) and return an RGB PIL image."""
    from PIL import Image
    if isinstance(image, str):
        return Image.open(image).convert("RGB")
    if isinstance(image, np.ndarray):
        return Image.fromarray(np.ascontiguousarray(image[:, :, ::-1]))  # BGR -> RGB
    return image.convert("RGB")


def pixel_inputs(image, model_id: str = MODEL_ID):
    """EfficientNet's own preprocessing (resize, crop, scale, normalise), exactly
    as the model was trained with. My-model preprocessing lives in model.py."""
    processor, _ = load(model_id)
    return processor(images=to_pil(image), return_tensors="pt")


def extract_features(image, model_id: str = MODEL_ID) -> np.ndarray:
    import torch
    _, model = load(model_id)
    with torch.inference_mode():
        out = model.efficientnet(**pixel_inputs(image, model_id))
    return out.pooler_output[0].numpy()  # shape (1280,)


def classify_imagenet(image, top_k: int = 3, model_id: str = MODEL_ID) -> list[tuple[str, float]]:
    import torch
    _, model = load(model_id)
    with torch.inference_mode():
        probs = model(**pixel_inputs(image, model_id)).logits.softmax(-1)[0]
    best = probs.argsort(descending=True)[:top_k]
    return [(model.config.id2label[int(i)], round(float(probs[i]), 4)) for i in best]
