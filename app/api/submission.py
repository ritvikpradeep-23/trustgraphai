from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import SubmissionRecord, get_db
from app.schemas.submission import Submission
from app.services.submission_processor import process_submission


router = APIRouter(tags=["Submission"])


@router.post("/submit")
def submit(submission: Submission, db: Session = Depends(get_db)):

    submission.submission_id = f"sub_{uuid4().hex[:12]}"

    processed_submission = process_submission(submission)
    db.add(SubmissionRecord(**processed_submission))
    db.commit()

    return {
        "message": "Submission received successfully",
        "submission": processed_submission,
    }
