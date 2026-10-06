"""Account-scoped verdict history; no raw messages are exposed or stored."""
from datetime import datetime, timedelta, timezone
import math
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.accounts import Account, AccountCheck, AccountExtension, aware, current_user, require_csrf
from app.core.database import ExtensionResultRecord, get_db
from app.api.detect import detect
from app.schemas.detection import DetectionRequest

router = APIRouter(prefix="/workspace", tags=["Workspace"])
CHANNELS = {"whatsapp", "gmail", "messenger", "instagram", "linkedin", "telegram", "discord", "slack", "generic", "test", "other"}


def score(value):
    return value if not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and 0 <= value <= 1 else None


def detection_view(record):
    # Compatibility projection only; unowned legacy data is not an account's history.
    from urllib.parse import urlsplit
    submission = record.submission
    site = submission.source if submission else "Backend result"
    if submission and submission.url:
        try:
            site = urlsplit(submission.url).hostname or site
        except ValueError:
            pass
    level = {"MEDIUM": "CAUTION"}.get(record.risk_level.upper(), record.risk_level.upper())
    risk = score(record.risk_score)
    if level not in {"SAFE", "LOW", "CAUTION", "HIGH", "CRITICAL", "UNKNOWN"} or risk is None:
        level, risk = "UNKNOWN" if level == "UNKNOWN" else "PENDING", None
    return {"id": record.detection_id, "createdAt": aware(record.created_at).isoformat(),
            "channel": next((c for c in ("whatsapp", "gmail", "messenger", "instagram") if submission and c in submission.source.lower()), "other"),
            "site": site, "riskLevel": level, "riskScore": risk,
            "explanation": " ".join(record.reasons or []) or "No explanation available.",
            "signals": [{"name": n, "score": score(v), "explanation": "Signal unavailable" if score(v) is None else "Score returned by the backend"} for n, v in (record.signals or {}).items()],
            "engineVersion": "backend", "status": "new", "feedback": "none", "isDemo": False, "editable": False}


def extension_view(record):
    names = [s.replace("_", " ") for s in record.signal_ids or []]
    return {"id": record.result_id, "createdAt": aware(record.timestamp).isoformat(),
            "channel": record.channel if record.channel in CHANNELS else "other",
            "site": record.domain or "Browser extension", "riskLevel": record.risk_level.upper(),
            "riskScore": score(record.score / 100), "scoreMetric": "Review score",
            "explanation": "Extension signals: " + ", ".join(names) if names else "No configured rule raised concern; this is not proof of safety.",
            "signals": [{"name": n, "score": None, "explanation": "Extension signal"} for n in names],
            "engineVersion": "browser-extension", "status": "new", "feedback": record.feedback,
            "isDemo": False, "editable": False}


def owned_extensions(user, db):
    return select(AccountExtension.token_id).where(AccountExtension.user_id == user.user_id)


@router.get("/detections")
def detections(response: Response, user: Account = Depends(current_user), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    items = [row.view for row in db.scalars(select(AccountCheck).where(AccountCheck.user_id == user.user_id)).all()]
    items += [extension_view(row) for row in db.scalars(
        select(ExtensionResultRecord).where(ExtensionResultRecord.token_id.in_(owned_extensions(user, db)))).all()]
    return sorted(items, key=lambda i: i["createdAt"], reverse=True)


@router.get("/detections/{detection_id}")
def detection(detection_id: str, response: Response, user: Account = Depends(current_user), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    row = db.scalar(select(AccountCheck).where(AccountCheck.detection_id == detection_id, AccountCheck.user_id == user.user_id))
    if row:
        return row.view
    row = db.scalar(select(ExtensionResultRecord).where(
        ExtensionResultRecord.result_id == detection_id,
        ExtensionResultRecord.token_id.in_(owned_extensions(user, db))))
    if row:
        return extension_view(row)
    raise HTTPException(404, "Detection not found")


@router.post("/checks", dependencies=[Depends(require_csrf)])
def check(body: DetectionRequest, user: Account = Depends(current_user), db: Session = Depends(get_db)):
    if body.submission_id:
        raise HTTPException(400, "Account checks do not attach to legacy submissions.")
    result = detect(body, db)
    view = {"id": result.detection_id, "createdAt": datetime.now(timezone.utc).isoformat(),
            "channel": body.channel if body.channel in CHANNELS else "other",
            "site": "Web analysis", "riskLevel": result.risk_level, "riskScore": result.risk_score,
            "scoreMetric": "Text similarity" if result.method == "database-pattern-matching" else "Review score",
            "explanation": f"Account check via {result.method}; {len(result.previous_report_matches)} catalog matches. Scores are review signals, not a fraud probability. Raw analysis text and model explanations are not retained.", "signals": [
                {"name": n, "score": v, "explanation": "Backend signal" if v is not None else "Unavailable"}
                for n, v in result.signals.model_dump().items()],
            "engineVersion": result.method, "status": "new", "feedback": "none", "isDemo": False, "editable": False}
    db.add(AccountCheck(detection_id=result.detection_id, user_id=user.user_id, view=view))
    db.commit()
    return result


@router.get("/status")
def status(response: Response, user: Account = Depends(current_user), db: Session = Depends(get_db)):
    from app.ai.scam_engine import engine
    response.headers["Cache-Control"] = "no-store"
    records = db.scalars(select(AccountExtension).where(AccountExtension.user_id == user.user_id)).all()
    last = max((aware(r.last_seen) for r in records if r.last_seen), default=None)
    state = "CONNECTED" if last and datetime.now(timezone.utc) - last <= timedelta(minutes=2) else "NOT CONNECTED"
    return {"state": state, "lastSeen": last.isoformat() if last else None, "authentication": True,
            "extensionPairing": bool(records), "aiAvailable": engine() is not None}
