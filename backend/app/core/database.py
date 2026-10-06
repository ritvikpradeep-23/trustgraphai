import os
from datetime import datetime
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class SubmissionRecord(Base):
    __tablename__ = "submissions"

    submission_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    text: Mapped[str | None] = mapped_column(Text)
    caption: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    media_reference: Mapped[str | None] = mapped_column(Text)
    sender: Mapped[str | None] = mapped_column(String(512))
    source_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user_consent: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    detections: Mapped[list["DetectionRecord"]] = relationship(back_populates="submission")
    reports: Mapped[list["ReportRecord"]] = relationship(back_populates="submission")


class DetectionRecord(Base):
    __tablename__ = "detections"

    detection_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    submission_id: Mapped[str] = mapped_column(
        ForeignKey("submissions.submission_id"), nullable=False, index=True
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)
    signals: Mapped[dict] = mapped_column(JSON, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    submission: Mapped[SubmissionRecord] = relationship(back_populates="detections")


class ReportRecord(Base):
    __tablename__ = "reports"

    report_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    submission_id: Mapped[str] = mapped_column(
        ForeignKey("submissions.submission_id"), nullable=False, index=True
    )
    report_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    submission: Mapped[SubmissionRecord] = relationship(back_populates="reports")


class ReportMatchRecord(Base):
    __tablename__ = "report_matches"
    __table_args__ = (
        UniqueConstraint("submission_id", "report_id", name="uq_report_matches_submission_report"),
    )

    match_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    submission_id: Mapped[str] = mapped_column(
        ForeignKey("submissions.submission_id"), nullable=False, index=True
    )
    report_id: Mapped[str] = mapped_column(
        ForeignKey("reports.report_id"), nullable=False, index=True
    )
    matched_submission_id: Mapped[str] = mapped_column(
        ForeignKey("submissions.submission_id"), nullable=False, index=True
    )
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RelationshipRecord(Base):
    __tablename__ = "relationships"
    __table_args__ = (
        CheckConstraint(
            "relationship_type IN ('similar_content', 'same_reported_content', "
            "'same_sender', 'same_url_domain', 'related_report')",
            name="ck_relationships_type",
        ),
        CheckConstraint(
            "source_entity_type IN ('submission', 'report', 'detection') AND "
            "target_entity_type IN ('submission', 'report', 'detection')",
            name="ck_relationships_entity_types",
        ),
        UniqueConstraint(
            "relationship_type", "source_entity_type", "source_entity_id",
            "target_entity_type", "target_entity_id", name="uq_relationships_edge",
        ),
    )

    relationship_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target_entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FingerprintRecord(Base):
    """Perceptual fingerprint of a known fake (app/fingerprint). Only the
    hashes, a label and a source are kept, never the image itself. Each
    64-bit hash is also split into four indexed 16-bit bands so a lookup
    by Hamming distance doesn't scan the table."""

    __tablename__ = "fingerprints"
    __table_args__ = (
        CheckConstraint("kind IN ('image', 'text')", name="ck_fingerprints_kind"),
        Index("ix_fingerprints_b0", "kind", "b0"),
        Index("ix_fingerprints_b1", "kind", "b1"),
        Index("ix_fingerprints_b2", "kind", "b2"),
        Index("ix_fingerprints_b3", "kind", "b3"),
        Index("ix_fingerprints_hash", "kind", "hash"),
    )

    fingerprint_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    source: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    hash: Mapped[int] = mapped_column(BigInteger, nullable=False)  # pHash, signed 64-bit
    hash2: Mapped[int | None] = mapped_column(BigInteger)  # dHash
    b0: Mapped[int] = mapped_column(Integer, nullable=False)
    b1: Mapped[int] = mapped_column(Integer, nullable=False)
    b2: Mapped[int] = mapped_column(Integer, nullable=False)
    b3: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
