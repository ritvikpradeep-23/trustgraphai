from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import SubmissionRecord, get_db
from app.schemas.detection import (
    DetectionRequest,
    DetectionResponse,
    DetectionSignals,
    PatternComparisonResponse,
)
from app.services.pattern_detection import verdict
from app.services.previous_report_matcher import (
    MATCH_THRESHOLD,
    similarity_tier,
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

    comparisons = find_previous_report_matches(
        db,
        text=request.text,
        url=request.url,
        submission_id=request.submission_id,
        include_below_threshold=True,
    )
    previous_report_matches = [match for match in comparisons if match.similarity_score >= MATCH_THRESHOLD]
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
        pattern_comparisons=[PatternComparisonResponse(
            **vars(match), rank=index + 1, tier=similarity_tier(match.similarity_score)
        ) for index, match in enumerate(comparisons)],
        comparison_count=len(comparisons),
        match_threshold=MATCH_THRESHOLD,
        ai_written=None,
    )
