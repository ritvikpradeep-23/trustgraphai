from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import ReportRecord, SubmissionRecord, get_db
from app.schemas.report import ReportCreateRequest, ReportDetailResponse, ReportResponse


router = APIRouter(tags=["Reports"])


@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(report: ReportCreateRequest, db: Session = Depends(get_db)):
    if db.get(SubmissionRecord, report.submission_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    record = ReportRecord(
        report_id=f"rep_{uuid4().hex[:12]}",
        submission_id=report.submission_id,
        report_type=report.report_type,
        status=report.status,
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/reports", response_model=list[ReportResponse])
def list_reports(db: Session = Depends(get_db)):
    statement = select(ReportRecord).order_by(ReportRecord.created_at.desc())
    return db.scalars(statement).all()


@router.get("/reports/{report_id}", response_model=ReportDetailResponse)
def get_report(report_id: str, db: Session = Depends(get_db)):
    statement = (
        select(ReportRecord)
        .options(selectinload(ReportRecord.submission))
        .where(ReportRecord.report_id == report_id)
    )
    report = db.scalar(statement)

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    return report
