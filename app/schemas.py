"""Request and response shapes for the API (validated by Pydantic)."""
from typing import Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
VideoResult = Literal["likely_fake", "likely_real", "inconclusive"]
AiTextResult = Literal["likely_ai", "likely_human"]


class TextIn(BaseModel):
    # The length cap protects the server; the configured MAX_TEXT_CHARS is
    # checked again in the endpoint so it can be changed without code edits.
    text: str = Field(min_length=1, max_length=20000, examples=["Your account will be suspended today..."])
    source: str = Field(min_length=1, max_length=50, examples=["website", "extension", "telegram"])


class ReportOut(BaseModel):
    id: str
    status: Literal["stored"] = "stored"


class MatchEvidence(BaseModel):
    """One similar earlier report. Deliberately has NO text field: another
    user's report text is never sent back (privacy)."""
    id: str
    similarity: float
    source: str


class AnalyzeOut(BaseModel):
    risk_level: RiskLevel
    top_similarity: float
    similar_reports: int  # reports at or above the MEDIUM threshold
    matches: list[MatchEvidence]


class VideoAnalysisOut(BaseModel):
    result: VideoResult
    confidence: float
    frames_examined: int
    faces_examined: int
    fake_frame_ratio: float
    mock: bool | None = None  # only present (true) when the demo mock model produced the result


class ErrorOut(BaseModel):
    error: str
    detail: str | None = None


class HealthOut(BaseModel):
    status: Literal["ok"] = "ok"
    reports_stored: int
    embedding_model_loaded: bool  # false until the first text request (the model loads lazily)
    deepfake_model: Literal["configured", "mock", "not_configured"]
    deepfake_mode: str
    ai_text_model: Literal["configured", "not_configured"]


class AiCheckIn(BaseModel):
    text: str = Field(min_length=1, max_length=20000, examples=["Certainly! Here is a summary of the key points."])


class AiCheckOut(BaseModel):
    """Whether a text reads as AI-written. This is NOT a scam verdict."""
    result: AiTextResult
    ai_score: float  # 0-1, from the fine-tuned text model
