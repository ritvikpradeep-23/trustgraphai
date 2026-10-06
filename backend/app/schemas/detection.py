from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DetectionRequest(BaseModel):
    channel: str
    sender: Optional[str] = None
    text: str = Field(min_length=1, max_length=20000)
    url: Optional[str] = None
    submission_id: Optional[str] = None


class DetectionSignals(BaseModel):
    anomaly: float | None
    continuity: float | None
    similarity: float | None
    precedent: float | None


class AIWrittenCheckRequest(BaseModel):
    text: str


class ModalityCheckResponse(BaseModel):
    ai_written_score: float | None = None
    available: bool
    model: str
    reasons: list[str]


class VideoAnalyzeResponse(BaseModel):
    fake_score: float | None = None
    available: bool
    model: str
    reasons: list[str]


class DetectionResponse(BaseModel):
    detection_id: str
    risk_score: float | None
    risk_level: str
    signals: DetectionSignals
    reasons: list[str]
    previous_report_matches: list["PreviousReportMatchResponse"] = Field(default_factory=list)
    pattern_comparisons: list["PatternComparisonResponse"] = Field(default_factory=list)
    comparison_count: int = 0
    match_threshold: float = 0.712
    ai_written: ModalityCheckResponse | None = None
    method: str = "database-pattern-matching"
    model_available: bool = False
    model_used: bool = False
    decision_source: str = "records"
    score_kind: str = "text-similarity"


class PreviousReportMatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: str
    submission_id: str
    report_type: str
    status: str
    similarity_score: float


class PatternComparisonResponse(PreviousReportMatchResponse):
    rank: int
    tier: str


class StoredSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    submission_id: str
    source: str
    content_type: str
    text: Optional[str]
    caption: Optional[str]
    url: Optional[str]
    media_reference: Optional[str]
    sender: Optional[str]
    source_timestamp: Optional[datetime]
    user_consent: bool
    created_at: datetime


class DetectionHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    detection_id: str
    submission_id: str
    risk_score: float
    risk_level: str
    signals: dict[str, float]
    reasons: list[str]
    created_at: datetime


class DetectionDetailResponse(DetectionHistoryResponse):
    submission: StoredSubmissionResponse
