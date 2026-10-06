"""Insert synthetic judge-demo patterns in PostgreSQL; never replace user data."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]
from sqlalchemy import select
from app.core.database import SessionLocal, SubmissionRecord, ReportRecord
from scripts.scam_catalog import load_catalog, seed_metadata, validate_catalog


def seed(db, patterns):
    validate_catalog(patterns)
    ids = [item["id"] for item in patterns]
    submissions = {record.submission_id: record for record in db.scalars(select(SubmissionRecord).where(SubmissionRecord.submission_id.in_(ids))).all()}
    reports = {record.report_id: record for record in db.scalars(select(ReportRecord).where(ReportRecord.report_id.in_(["report_" + key for key in ids]))).all()}
    now = datetime.now(timezone.utc)
    # Check every collision before adding anything; bulk queries avoid hundreds
    # of network round trips against hosted PostgreSQL.
    for item in patterns:
        source, report_status, report_type = seed_metadata(item)
        existing = submissions.get(item["id"])
        if existing is not None and (existing.source != source or existing.text != item["text"]):
            raise ValueError("Seed ID collision; existing data was not overwritten")
        report = reports.get("report_" + item["id"])
        if report is not None and (report.submission_id != item["id"] or report.status != report_status or report.report_type != report_type):
            raise ValueError("Report ID collision; existing data was not overwritten")
    for item in patterns:
        source, _, _ = seed_metadata(item)
        existing = submissions.get(item["id"])
        if existing is None:
            db.add(SubmissionRecord(submission_id=item["id"], source=source,
                content_type="text", text=item["text"], user_consent=True, created_at=now))
    db.flush()
    added = 0
    for item in patterns:
        _, report_status, report_type = seed_metadata(item)
        report_id = "report_" + item["id"]
        report = reports.get(report_id)
        if report is None:
            db.add(ReportRecord(report_id=report_id, submission_id=item["id"],
                report_type=report_type, status=report_status, created_at=now))
            added += 1
    db.commit()
    return added


if __name__ == "__main__":
    patterns = load_catalog()
    try:
        with SessionLocal() as db:
            added = seed(db, patterns)
        print(f"Added {added} synthetic demo patterns; catalog size {len(patterns)}. Existing records preserved.")
    except Exception as exc:
        print(f"Seed failed ({type(exc).__name__}); no credentials displayed.")
        sys.exit(1)
