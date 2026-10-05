"""Step 5: AI-written text detector (EfficientNet is not used for text).

A small pretrained language model from Hugging Face (distilroberta-base by
default, ~82M parameters, fits easily on a laptop GPU) with a 2-class layer,
fine-tuned by train_text.py on human-vs-AI examples.

    python text_detector.py "Certainly! Here is a summary of the key points."

It loads the fine-tuned model from models/text_detector (text.model_dir in
detection_config.json). Label 1 = AI-written, label 0 = human.
"""
import argparse

import numpy as np
import torch

from detection_common import best_device, load_config, resolve


class TextDetector:
    def __init__(self, model_dir: str | None = None, device: str | None = None, max_length: int | None = None):
        from transformers import AutoModelForSequenceClassification, AutoTokenizer  # heavy, so imported late
        cfg = load_config()["text"]
        self.model_dir = str(resolve(model_dir or cfg["model_dir"]))
        self.device = device or best_device()
        self.max_length = max_length or cfg["max_length"]
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir).to(self.device).eval()

    def score(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Probability that each text is AI-written (0-1)."""
        out = []
        with torch.inference_mode():
            for i in range(0, len(texts), batch_size):
                enc = self.tokenizer(texts[i:i + batch_size], truncation=True, max_length=self.max_length,
                                     padding=True, return_tensors="pt").to(self.device)
                out.append(self.model(**enc).logits.softmax(-1)[:, 1].float().cpu().numpy())
        return np.concatenate(out) if out else np.zeros(0)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text", nargs="+")
    ap.add_argument("--model-dir")
    args = ap.parse_args(argv)
    detector = TextDetector(args.model_dir)
    for text, score in zip(args.text, detector.score(args.text)):
        print(f"{score:.3f} ({'likely AI' if score >= 0.5 else 'likely human'})  {text[:80]}")


if __name__ == "__main__":
    main()
