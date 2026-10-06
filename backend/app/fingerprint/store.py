"""Known-fakes lookups in PostgreSQL (the `fingerprints` table in
app/core/database.py), by Hamming distance.

Fast as the table grows: each 64-bit hash is also stored as four 16-bit
bands, each indexed. A record within 3 bits of the query shares at least one
band exactly, so the indexed query finds it without a table scan; re-compressed
copies are usually that close. While the table has at most
FINGERPRINT_FULL_SCAN_MAX rows of a kind, the rest are compared directly too,
so every record within the threshold is found.
"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import FingerprintRecord
from app.fingerprint import config
from app.fingerprint.hashing import bands, hamming, similarity, to_signed, to_unsigned

NO_MATCH = {"db_match": False, "similarity": None, "matched_record_id": None}


def add(db: Session, kind: str, hash_: int, label: str, source: str = "", hash2: int | None = None,
        commit: bool = True) -> str:
    b0, b1, b2, b3 = bands(hash_)
    record = FingerprintRecord(
        fingerprint_id=f"fp_{uuid4().hex[:12]}", kind=kind, label=label[:128], source=source[:256],
        hash=to_signed(hash_), hash2=None if hash2 is None else to_signed(hash2),
        b0=b0, b1=b1, b2=b2, b3=b3, created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    if commit:
        db.commit()
    else:
        db.flush()
    return record.fingerprint_id


def count(db: Session, kind: str | None = None) -> int:
    statement = select(func.count()).select_from(FingerprintRecord)
    if kind:
        statement = statement.where(FingerprintRecord.kind == kind)
    return db.scalar(statement) or 0


def _candidates(db: Session, kind: str, hash_: int, full_scan_max: int):
    b0, b1, b2, b3 = bands(hash_)
    F = FingerprintRecord
    rows = db.scalars(select(F).where(F.kind == kind, or_(F.b0 == b0, F.b1 == b1, F.b2 == b2, F.b3 == b3))).all()
    total = count(db, kind)
    if total <= full_scan_max and total > len(rows):
        rows = db.scalars(select(F).where(F.kind == kind)).all()
    return rows


def lookup(db: Session, kind: str, hash_: int, threshold: int, hash2: int | None = None,
           threshold2: int | None = None, full_scan_max: int | None = None) -> dict:
    """Closest record within the threshold(s):
    {db_match, similarity, matched_record_id, distance, label}."""
    best = None
    for row in _candidates(db, kind, hash_, config.FULL_SCAN_MAX if full_scan_max is None else full_scan_max):
        d = hamming(hash_, to_unsigned(row.hash))
        if d > threshold:
            continue
        if hash2 is not None and row.hash2 is not None and threshold2 is not None \
                and hamming(hash2, to_unsigned(row.hash2)) > threshold2:
            continue
        if best is None or d < best[0]:
            best = (d, row)
    if best is None:
        return dict(NO_MATCH)
    d, row = best
    return {"db_match": True, "similarity": similarity(d), "matched_record_id": row.fingerprint_id,
            "distance": d, "label": row.label}


def self_test(db: Session) -> bool:
    """Write a probe fingerprint, find it again, roll it back: proves the
    round trip without leaving anything behind."""
    probe = 0x5A5A_F00D_C0DE_1234
    try:
        record_id = add(db, "text", probe, "health-probe", "health", commit=False)
        found = lookup(db, "text", probe ^ 0b11, threshold=2)
        return found["matched_record_id"] == record_id
    finally:
        db.rollback()
