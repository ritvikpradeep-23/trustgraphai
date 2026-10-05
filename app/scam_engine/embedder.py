"""Turns text into a vector so similar messages land close together.

Uses sentence-transformers all-MiniLM-L6-v2 (small, CPU-friendly, 384 numbers
per text). The model is loaded the first time it is needed, not at import:
loading takes a few seconds and downloads ~90 MB on first use, and /health or
the video endpoint shouldn't pay for that.
"""
import threading

import numpy as np


class EmbeddingUnavailable(RuntimeError):
    """The model couldn't be loaded (e.g. no internet on first run)."""


class Embedder:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        # FastAPI runs normal (def) endpoints in a thread pool, so two first
        # requests could arrive together; the lock makes sure we load once.
        self._lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def _load(self):
        with self._lock:
            if self._model is None:
                from sentence_transformers import SentenceTransformer  # heavy import, only when needed
                try:
                    self._model = SentenceTransformer(self.model_name, device="cpu")
                except Exception as exc:  # download blocked, wrong name, corrupt cache...
                    raise EmbeddingUnavailable(f"could not load {self.model_name}: {type(exc).__name__}") from exc
        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        """One row per text, each scaled to length 1, so a dot product between
        two rows is their cosine similarity."""
        vectors = self._load().encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return np.asarray(vectors, dtype=np.float32)
