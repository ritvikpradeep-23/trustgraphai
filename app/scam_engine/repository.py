"""Where reported scam messages are kept, and how we find similar ones.

ReportRepository is the small interface the rest of the code uses (add,
search, count). InMemoryReportRepository implements it with a NumPy matrix and
a JSON file, which is plenty for a demo. Later a pgvector-backed class with
the same three methods can replace it without touching the service or API.
"""
import json
import os
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


@dataclass
class StoredReport:
    id: str
    text: str           # kept so reports can be re-embedded if the model changes; never returned by the API
    source: str
    embedding: np.ndarray
    created_at: str


class ReportRepository(ABC):
    @abstractmethod
    def add(self, text: str, source: str, embedding: np.ndarray) -> StoredReport: ...

    @abstractmethod
    def search(self, embedding: np.ndarray, k: int) -> list[tuple[StoredReport, float]]:
        """The k most similar reports with their cosine similarity, best first."""

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def contains_text(self, text: str) -> bool: ...


class InMemoryReportRepository(ReportRepository):
    def __init__(self, path: str | None):
        self.path = Path(path) if path else None
        self._reports: list[StoredReport] = []
        self._matrix = np.zeros((0, 0), dtype=np.float32)  # one row per report, for fast search
        self._lock = threading.Lock()  # requests run in parallel threads
        if self.path and self.path.exists():
            self._load()

    def add(self, text: str, source: str, embedding: np.ndarray) -> StoredReport:
        report = StoredReport(id=uuid.uuid4().hex, text=text, source=source,
                              embedding=np.asarray(embedding, dtype=np.float32),
                              created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        with self._lock:
            self._reports.append(report)
            self._rebuild_matrix()
            self._save()
        return report

    def search(self, embedding: np.ndarray, k: int) -> list[tuple[StoredReport, float]]:
        with self._lock:
            if not self._reports:
                return []
            # Embeddings are length 1, so the dot product IS the cosine similarity.
            sims = self._matrix @ np.asarray(embedding, dtype=np.float32)
            best = np.argsort(-sims)[:k]
            return [(self._reports[i], float(sims[i])) for i in best]

    def count(self) -> int:
        return len(self._reports)

    def contains_text(self, text: str) -> bool:
        return any(r.text == text for r in self._reports)

    # --- persistence --------------------------------------------------------
    def _rebuild_matrix(self):
        self._matrix = np.vstack([r.embedding for r in self._reports]) if self._reports else np.zeros((0, 0))

    def _save(self):
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [{"id": r.id, "text": r.text, "source": r.source, "created_at": r.created_at,
                 "embedding": [round(float(x), 6) for x in r.embedding]} for r in self._reports]
        # Write to a temporary file, then swap it in: a crash mid-write can't
        # leave a half-written (corrupt) reports file behind.
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        os.replace(tmp, self.path)

    def _load(self):
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self._reports = [StoredReport(id=d["id"], text=d["text"], source=d["source"], created_at=d["created_at"],
                                      embedding=np.asarray(d["embedding"], dtype=np.float32)) for d in data]
        self._rebuild_matrix()
