from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import RelationshipRecord, get_db
from app.services.correlation import ENTITY_MODELS, RELATIONSHIP_TYPES, validate_relationship


router = APIRouter(tags=["Scam Graph"])


class RelationshipCreateRequest(BaseModel):
    relationship_type: str = Field(min_length=1, max_length=64)
    source_entity_type: str = Field(min_length=1, max_length=32)
    source_entity_id: str = Field(min_length=1, max_length=64)
    target_entity_type: str = Field(min_length=1, max_length=32)
    target_entity_id: str = Field(min_length=1, max_length=64)


class RelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    relationship_id: str
    relationship_type: str
    source_entity_type: str
    source_entity_id: str
    target_entity_type: str
    target_entity_id: str
    evidence: dict
    created_at: datetime


def _canonical_pair(source_type, source_id, target_type, target_id):
    left, right = (source_type, source_id), (target_type, target_id)
    return (left, right) if left <= right else (right, left)


@router.post("/relationships", response_model=RelationshipResponse, status_code=status.HTTP_201_CREATED)
def create_relationship(request: RelationshipCreateRequest, db: Session = Depends(get_db)):
    if request.relationship_type not in RELATIONSHIP_TYPES:
        raise HTTPException(status_code=422, detail="Unsupported relationship type")
    try:
        evidence = validate_relationship(
            db, request.relationship_type, request.source_entity_type, request.source_entity_id,
            request.target_entity_type, request.target_entity_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    (source_type, source_id), (target_type, target_id) = _canonical_pair(
        request.source_entity_type, request.source_entity_id,
        request.target_entity_type, request.target_entity_id,
    )
    statement = select(RelationshipRecord).where(
        RelationshipRecord.relationship_type == request.relationship_type,
        RelationshipRecord.source_entity_type == source_type,
        RelationshipRecord.source_entity_id == source_id,
        RelationshipRecord.target_entity_type == target_type,
        RelationshipRecord.target_entity_id == target_id,
    )
    existing = db.scalar(statement)
    if existing is not None:
        return existing

    record = RelationshipRecord(
        relationship_id=f"rel_{uuid4().hex[:12]}",
        relationship_type=request.relationship_type,
        source_entity_type=source_type,
        source_entity_id=source_id,
        target_entity_type=target_type,
        target_entity_id=target_id,
        evidence=evidence,
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(statement)
        if existing is not None:
            return existing
        raise
    db.refresh(record)
    return record


@router.get("/relationships", response_model=list[RelationshipResponse])
def list_relationships(
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    relationship_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if entity_type is not None and entity_type not in ENTITY_MODELS:
        raise HTTPException(status_code=422, detail="Unsupported entity type")
    if relationship_type is not None and relationship_type not in RELATIONSHIP_TYPES:
        raise HTTPException(status_code=422, detail="Unsupported relationship type")
    statement = select(RelationshipRecord).order_by(RelationshipRecord.created_at.desc())
    if entity_type and entity_id:
        statement = statement.where(
            ((RelationshipRecord.source_entity_type == entity_type) & (RelationshipRecord.source_entity_id == entity_id))
            | ((RelationshipRecord.target_entity_type == entity_type) & (RelationshipRecord.target_entity_id == entity_id))
        )
    if relationship_type:
        statement = statement.where(RelationshipRecord.relationship_type == relationship_type)
    return db.scalars(statement).all()
