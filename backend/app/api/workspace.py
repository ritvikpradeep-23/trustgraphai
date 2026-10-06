"""Read-only, verdict-only projection for the React workspace.

Preserve the existing /api/detections contract. Never send stored submission
text, captions, senders, media references, or URL query strings to this UI.
"""
from datetime import datetime, timedelta, timezone
import math
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import (
    DetectionRecord,
    ExtensionHeartbeatRecord,
    ExtensionResultRecord,
    ExtensionTokenRecord,
    get_db,
)

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


# Verdicts synced by the paired browser extension (app/api/extension_sync.py).
# They carry no message text: only level, score, signal types, channel, domain.
SIGNAL_NAMES = {
    "urgency": "Urgency pressure", "money_request": "Request for money, gift cards or crypto",
    "credential_request": "Credential or OTP request", "suspicious_link": "Suspicious link or lookalike domain",
    "sender_mismatch": "Sender mismatch", "impersonation": "Impersonation of a contact or brand",
    "continuity_break": "Unusual continuity break", "pattern_similarity": "Similar to known scam patterns",
}
EXTENSION_CHANNELS = {"whatsapp", "gmail", "messenger", "instagram"}


def extension_view(record):
    ts = record.timestamp if record.timestamp.tzinfo else record.timestamp.replace(tzinfo=timezone.utc)
    names = [SIGNAL_NAMES.get(s, s.replace("_", " ").capitalize()) for s in (record.signal_ids or [])]
    explanation = ("Signs found by the browser extension: " + ", ".join(n.lower() for n in names) + "."
                   if names else "The browser extension found no scam signs.")
    return {
        "id": record.result_id, "createdAt": ts.isoformat(),
        "channel": record.channel if record.channel in EXTENSION_CHANNELS else "other",
        "site": record.domain or "Browser extension",
        "riskLevel": record.risk_level.upper(), "riskScore": max(0, min(100, record.score)) / 100,
        "explanation": explanation,
        "signals": [{"name": n, "score": None, "explanation": "Found by the browser extension"} for n in names],
        "engineVersion": "browser-extension", "status": "new",
        "feedback": "false_alarm" if record.feedback == "false_alarm" else "none",
        "isDemo": False, "editable": False,
    }


@router.get("/detections")
def detections(db: Session = Depends(get_db)):
    statement = select(DetectionRecord).options(selectinload(DetectionRecord.submission)).order_by(DetectionRecord.created_at.desc())
    items = [detection_view(record) for record in db.scalars(statement).all()]
    items += [extension_view(record) for record in db.scalars(select(ExtensionResultRecord)).all()]
    return sorted(items, key=lambda item: item["createdAt"], reverse=True)


@router.get("/detections/{detection_id}")
def detection(detection_id: str, db: Session = Depends(get_db)):
    statement = select(DetectionRecord).options(selectinload(DetectionRecord.submission)).where(DetectionRecord.detection_id == detection_id)
    record = db.scalar(statement)
    if record is not None:
        return detection_view(record)
    synced = db.get(ExtensionResultRecord, detection_id)
    if synced is not None:
        return extension_view(synced)
    raise HTTPException(status_code=404, detail="Detection not found")


# The extension sends a heartbeat every 15 s while a supported page is open.
CONNECTED_WITHIN = timedelta(minutes=2)


@router.get("/status")
def status(db: Session = Depends(get_db)):
    last = db.scalar(select(ExtensionHeartbeatRecord.last_seen).order_by(ExtensionHeartbeatRecord.last_seen.desc()).limit(1))
    paired = db.scalar(select(ExtensionTokenRecord.token_id).limit(1)) is not None
    if last is not None and last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    if last is None:
        state = "UNKNOWN"
    else:
        state = "CONNECTED" if datetime.now(timezone.utc) - last <= CONNECTED_WITHIN else "NOT CONNECTED"
    return {"state": state, "lastSeen": last.isoformat() if last else None, "authentication": False,
            "extensionPairing": paired, "aiAvailable": False}
