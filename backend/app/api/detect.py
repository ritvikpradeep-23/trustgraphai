from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import SubmissionRecord, get_db
from app.schemas.detection import (
    DetectionRequest,
    DetectionResponse,
    DetectionSignals,
)
from app.services.pattern_detection import verdict
from app.services.previous_report_matcher import (
    find_previous_report_matches,
    store_previous_report_matches,
)


router = APIRouter(tags=["Detection"])



@router.post("/detect", response_model=DetectionResponse)
def detect(request: DetectionRequest, db: Session = Depends(get_db)):

    if request.submission_id and db.get(SubmissionRecord, request.submission_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    previous_report_matches = find_previous_report_matches(
        db,
        text=request.text,
        url=request.url,
        submission_id=request.submission_id,
    )
    if request.submission_id:
        store_previous_report_matches(
            db,
            submission_id=request.submission_id,
            matches=previous_report_matches,
        )

    similarity, level, reasons = verdict(previous_report_matches)
    return DetectionResponse(
        detection_id=f"det_{uuid4().hex[:12]}",
        risk_score=similarity,
        risk_level=level,
        signals=DetectionSignals(
            anomaly=None,
            continuity=None,
            similarity=similarity,
            precedent=similarity,
        ),
        reasons=reasons,
        previous_report_matches=previous_report_matches,
        ai_written=None,
    )
