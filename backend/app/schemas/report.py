from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.detection import StoredSubmissionResponse


class ReportCreateRequest(BaseModel):
    submission_id: str
    report_type: str
    status: str = "pending"


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: str
    submission_id: str
    report_type: str
    status: str
    created_at: datetime


class ReportDetailResponse(ReportResponse):
    submission: StoredSubmissionResponse
