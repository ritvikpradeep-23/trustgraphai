from uuid import uuid4
import os

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import SubmissionRecord, get_db
from app.schemas.detection import (
    DetectionRequest,
    DetectionResponse,
    DetectionSignals,
    PatternComparisonResponse,
)
from app.services.pattern_detection import verdict
from app.ai.scam_engine import analyze as scam_analyze
from app.services.previous_report_matcher import (
    MATCH_THRESHOLD,
    similarity_tier,
    find_previous_report_matches,
    store_previous_report_matches,
)


router = APIRouter(tags=["Detection"])



@router.post("/detect", response_model=DetectionResponse)
def detect(request: DetectionRequest, db: Session = Depends(get_db), http_request: Request = None):

    hosted = bool(os.getenv("VERCEL")) or os.getenv("AUTH_COOKIE_SECURE") == "true" or (http_request is not None and http_request.url.scheme == "https")
    if hosted and request.submission_id:
        raise HTTPException(403, "Hosted checks cannot attach to unowned legacy submissions.")

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
    model = scam_analyze(request.text, request.sender, request.url)
    model_score = model["score"] if model else None
    # A known pattern is separate evidence; never average an unavailable model
    # into zero or let a model dismiss a qualified catalog match.
    ranks = {"UNKNOWN": -1, "LOW": 0, "CAUTION": 1, "HIGH": 2}
    if model and ranks.get(model["level"], -1) > ranks.get(level, -1):
        level = model["level"]
    result_score = max(v for v in (model_score, similarity) if v is not None) if model or similarity is not None else None
    if model:
        reasons = model["reasons"] + reasons
    return DetectionResponse(
        detection_id=f"det_{uuid4().hex[:12]}",
        risk_score=result_score,
        risk_level=level,
        signals=DetectionSignals(
            anomaly=model["signals"].get("anomaly") if model else None,
            continuity=model["signals"].get("continuity") if model else None,
            similarity=max(similarity or 0, model["signals"].get("similarity", 0)) if model else similarity,
            precedent=model["signals"].get("precedent") if model else similarity,
        ),
        reasons=reasons,
        previous_report_matches=previous_report_matches,
        pattern_comparisons=[PatternComparisonResponse(
            **vars(match), rank=index + 1, tier=similarity_tier(match.similarity_score)
        ) for index, match in enumerate(comparisons)],
        comparison_count=len(comparisons),
        match_threshold=MATCH_THRESHOLD,
        ai_written=None,
        method="original-scam-engine+database-pattern-matching" if model else "database-pattern-matching",
        model_available=bool(model),
        score_kind="review-score" if model else "text-similarity",
    )
