"""GET /health/database: proves backend -> PostgreSQL round trip.

Counts the reported scams the extension's checks are matched against, and
writes, finds and rolls back a probe fingerprint (nothing is left behind).
The extension calls this to confirm extension -> backend -> database.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.database import ReportRecord, SubmissionRecord, get_db
from app.fingerprint import store

router = APIRouter(tags=["Health"])


@router.get("/health/database")
def database_health(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
        counts = {
            "reports": db.scalar(select(func.count()).select_from(ReportRecord)) or 0,
            "submissions": db.scalar(select(func.count()).select_from(SubmissionRecord)) or 0,
            "image_fingerprints": store.count(db, "image"),
        }
        probe_found = store.self_test(db)
    except Exception as exc:
        db.rollback()
        return {"ok": False, "database": "error", "reason": type(exc).__name__}
    return {"ok": probe_found, "database": "postgresql", "probe_found": probe_found, **counts}
