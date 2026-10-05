"""Scam correlation: is this message like ones people already reported?

report():  clean the text, embed it, store it.
analyze(): clean, embed, find the most similar stored reports, and turn the
           best similarity into LOW / MEDIUM / HIGH using the config thresholds.
The text being analyzed is NOT stored: only explicit reports are kept.
"""
import re
import unicodedata

from app.config import Settings
from app.scam_engine.embedder import Embedder
from app.scam_engine.repository import ReportRepository
from app.schemas import AnalyzeOut, MatchEvidence

_ZERO_WIDTH = re.compile("[​‌‍⁠﻿]")


def normalize_text(text: str) -> str:
    """Make trivially different copies of a message look the same:
    NFKC turns look-alike characters (full-width letters, fancy digits) into
    plain ones, invisible zero-width characters are removed, and runs of
    whitespace become one space."""
    text = unicodedata.normalize("NFKC", text)
    text = _ZERO_WIDTH.sub("", text)
    return " ".join(text.split())


def risk_level(similarity: float, settings: Settings) -> str:
    if similarity >= settings.scam_high_threshold:
        return "HIGH"
    if similarity >= settings.scam_medium_threshold:
        return "MEDIUM"
    return "LOW"


class ScamService:
    def __init__(self, embedder: Embedder, repository: ReportRepository, settings: Settings):
        self.embedder, self.repository, self.settings = embedder, repository, settings

    def report(self, text: str, source: str) -> str:
        clean = normalize_text(text)
        vector = self.embedder.embed([clean])[0]
        return self.repository.add(clean, source, vector).id

    def analyze(self, text: str) -> AnalyzeOut:
        vector = self.embedder.embed([normalize_text(text)])[0]
        hits = self.repository.search(vector, self.settings.scam_top_k)
        top = max((sim for _, sim in hits), default=0.0)
        # Evidence = reports similar enough to matter (MEDIUM or above).
        # Only id, similarity and source go out, never the reported text.
        evidence = [MatchEvidence(id=r.id, similarity=round(sim, 4), source=r.source)
                    for r, sim in hits if sim >= self.settings.scam_medium_threshold]
        return AnalyzeOut(risk_level=risk_level(top, self.settings), top_similarity=round(top, 4),
                          similar_reports=len(evidence), matches=evidence)
