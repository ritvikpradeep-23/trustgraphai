"""Step 5: AI-written text detector.

A small pretrained language model from Hugging Face (distilroberta-base by
default, ~82M parameters, fits easily on a laptop GPU) with a 2-class layer,
fine-tuned by train_text.py on human-vs-AI examples.

    python text_detector.py "Certainly! Here is a summary of the key points."

It loads the fine-tuned model from models/text_detector (text.model_dir in
detection_config.json). Label 1 = AI-written, label 0 = human.
"""
import argparse
import sys
from pathlib import Path

# The detector itself lives in backend/app/ai (the server uses the same code).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))  # the website backend holds the engine code
from app.ai.text_detector import TextDetector as _Engine  # noqa: E402
from detection_common import load_config, resolve  # noqa: E402


class TextDetector(_Engine):
    """The backend's text detector, with defaults from detection_config.json."""

    def __init__(self, model_dir: str | None = None, device: str | None = None, max_length: int | None = None):
        cfg = load_config()["text"]
        super().__init__(str(resolve(model_dir or cfg["model_dir"])), device, max_length or cfg["max_length"])


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
