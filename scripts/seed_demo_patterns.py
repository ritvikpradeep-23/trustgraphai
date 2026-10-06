"""Insert synthetic judge-demo patterns in PostgreSQL; never replace user data."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.core.database import SessionLocal, SubmissionRecord, ReportRecord


def seed(db, patterns):
    added = 0
    now = datetime.now(timezone.utc)
    for item in patterns:
        existing = db.get(SubmissionRecord, item["id"])
        if existing is not None and (existing.source != "demo_pattern" or existing.text != item["text"]):
            raise ValueError("Seed ID collision; existing data was not overwritten")
        if existing is None:
            db.add(SubmissionRecord(submission_id=item["id"], source="demo_pattern",
                content_type="text", text=item["text"], user_consent=True, created_at=now))
            db.flush()
        report_id = "report_" + item["id"]
        report = db.get(ReportRecord, report_id)
        if report is not None and (report.submission_id != item["id"] or report.status != "synthetic_demo" or report.report_type != "Demo: " + item["title"]):
            raise ValueError("Report ID collision; existing data was not overwritten")
        if report is None:
            db.add(ReportRecord(report_id=report_id, submission_id=item["id"],
                report_type="Demo: " + item["title"], status="synthetic_demo", created_at=now))
            added += 1
    db.commit()
    return added


if __name__ == "__main__":
    patterns = json.loads((ROOT / "data/demo_scam_patterns.json").read_text(encoding="utf-8"))
    try:
        with SessionLocal() as db:
            added = seed(db, patterns)
        print(f"Added {added} synthetic demo patterns; catalog size {len(patterns)}. Existing records preserved.")
    except Exception as exc:
        print(f"Seed failed ({type(exc).__name__}); no credentials displayed.")
        sys.exit(1)
