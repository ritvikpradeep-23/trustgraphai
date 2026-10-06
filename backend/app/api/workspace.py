"""Read-only, verdict-only projection for the React workspace.

Preserve the existing /api/detections contract. Never send stored submission
text, captions, senders, media references, or URL query strings to this UI.
"""
from datetime import timezone
import math
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import DetectionRecord, get_db

router = APIRouter(prefix="/workspace", tags=["Workspace"])


def score(value):
    if not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and 0 <= value <= 1:
        return value
    return None


def detection_view(record):
    submission = record.submission
    source = submission.source.lower() if submission else "other"
    channel = next((name for name in ("whatsapp", "gmail", "messenger", "instagram") if name in source), "other")
    site = submission.source.replace("_", " ") if submission else "Backend result"
    if submission and submission.url:
        try:
            site = urlsplit(submission.url).hostname or site
        except ValueError:
            pass
    level = {"MEDIUM": "CAUTION"}.get(record.risk_level.upper(), record.risk_level.upper())
    risk_score = score(record.risk_score)
    if level not in {"SAFE", "LOW", "CAUTION", "HIGH", "CRITICAL"} or risk_score is None:
        level, risk_score = "PENDING", None
    created = record.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return {
        "id": record.detection_id, "createdAt": created.isoformat(),
        "channel": channel, "site": site, "riskLevel": level,
        "riskScore": risk_score, "explanation": " ".join(record.reasons or []) or "No explanation is available.",
        "signals": [{"name": name, "score": score(value), "explanation": "Signal unavailable" if score(value) is None else "Score returned by the backend"} for name, value in (record.signals or {}).items()],
        "engineVersion": "backend-v0.1.0", "status": "new", "feedback": "none",
        "isDemo": False, "editable": False,
    }


@router.get("/detections")
def detections(db: Session = Depends(get_db)):
    statement = select(DetectionRecord).options(selectinload(DetectionRecord.submission)).order_by(DetectionRecord.created_at.desc())
    return [detection_view(record) for record in db.scalars(statement).all()]


@router.get("/detections/{detection_id}")
def detection(detection_id: str, db: Session = Depends(get_db)):
    statement = select(DetectionRecord).options(selectinload(DetectionRecord.submission)).where(DetectionRecord.detection_id == detection_id)
    record = db.scalar(statement)
    if record is None:
        raise HTTPException(status_code=404, detail="Detection not found")
    return detection_view(record)


@router.get("/status")
def status():
    return {"state": "CONNECTED", "lastSeen": None, "authentication": False, "extensionPairing": False, "aiAvailable": False}
