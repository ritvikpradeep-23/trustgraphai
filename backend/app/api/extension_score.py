"""Adapter for the packaged extension's existing remote scorer."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.detect import detect
from app.core.database import get_db
from app.schemas.detection import DetectionRequest
router = APIRouter(tags=["Extension"])


class ScoreRequest(BaseModel):
    message_text: str = Field(min_length=1, max_length=20000)
    channel: str = "other"


@router.post("/score")
def score(request: ScoreRequest, db: Session = Depends(get_db)):
    result = detect(DetectionRequest(text=request.message_text, channel=request.channel), db)
    if result.risk_score is None:
        raise HTTPException(503, "No database match; use the extension's local rule fallback.")
    return {"band": "High", "score": result.risk_score,
            "explanation": " ".join(result.reasons),
            "signals": [{"name": "similarity", "score": result.risk_score}],
            "method": result.method}
