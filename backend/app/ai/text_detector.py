"""AI-written text detector: a small pretrained language model (distilroberta-base
by default) with a 2-class layer, fine-tuned by train_text.py. Label 1 = AI-written."""
import numpy as np


def best_device() -> str:
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


class TextDetector:
    def __init__(self, model_dir: str, device: str | None = None, max_length: int = 256):
        from transformers import AutoModelForSequenceClassification, AutoTokenizer  # heavy, imported late
        self.model_dir = str(model_dir)
        self.device = device or best_device()
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir).to(self.device).eval()

    def score(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Probability that each text is AI-written (0-1)."""
        import torch
        out = []
        with torch.inference_mode():
            for i in range(0, len(texts), batch_size):
                enc = self.tokenizer(texts[i:i + batch_size], truncation=True, max_length=self.max_length,
                                     padding=True, return_tensors="pt").to(self.device)
                out.append(self.model(**enc).logits.softmax(-1)[:, 1].float().cpu().numpy())
        return np.concatenate(out) if out else np.zeros(0)
