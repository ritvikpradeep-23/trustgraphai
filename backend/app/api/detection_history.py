from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import DetectionRecord, get_db
from app.schemas.detection import DetectionDetailResponse, DetectionHistoryResponse


router = APIRouter(tags=["Detection History"])


@router.get("/detections", response_model=list[DetectionHistoryResponse])
def list_detections(db: Session = Depends(get_db)):
    statement = select(DetectionRecord).order_by(DetectionRecord.created_at.desc())
    return db.scalars(statement).all()


@router.get("/detections/{detection_id}", response_model=DetectionDetailResponse)
def get_detection(detection_id: str, db: Session = Depends(get_db)):
    statement = (
        select(DetectionRecord)
        .options(selectinload(DetectionRecord.submission))
        .where(DetectionRecord.detection_id == detection_id)
    )
    detection = db.scalar(statement)

    if detection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found",
        )

    return detection
