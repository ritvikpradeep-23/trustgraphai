"""The browser extension's workspace contract (trustgraph_extension/shared/
api-client.js, TG.WEBAPP), so the extension and the React workspace share
one backend.

  POST   /api/extension/pairing-code  the workspace shows a one-time code
  POST   /api/extension/pair          {code} -> {token, account: {name}}
  POST   /api/results                 a verdict-only Result (Bearer token)
  GET    /api/results                 the paired extension's Results
  DELETE /api/results/{id}, /api/results
  GET    /api/export                  same as GET /api/results
  POST   /api/feedback                {resultId}: "Mark as wrong verdict"
  POST   /api/status                  {source, ts}: extension heartbeat

Privacy: a Result has no field that can hold message text (the request model
forbids extra fields and validates every value's shape), and only a SHA-256 of
each token is stored. Pairing codes require an account session and CSRF token.
Extension tokens and synced results are scoped to that account.
"""
import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import (
    ExtensionResultRecord,
    ExtensionTokenRecord,
    PairingCodeRecord,
    get_db,
)
from app.core.accounts import Account, AccountExtension, AccountPairing, current_user, require_csrf, rate_limit

router = APIRouter(tags=["Extension workspace"])

CODE_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_TTL = timedelta(minutes=10)
TOKEN = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
HOST = re.compile(r"^[a-z0-9.-]{0,253}$")
RESULT_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def paired_extension(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> ExtensionTokenRecord:
    token = (authorization or "").removeprefix("Bearer ").strip()
    record = db.scalar(select(ExtensionTokenRecord).where(ExtensionTokenRecord.token_hash == _hash(token))) if token else None
    if record is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Pair the extension with a code from the workspace first.")
    if db.get(AccountExtension, record.token_id) is None:
        raise HTTPException(401, "This legacy pairing has no account owner. Sign in and pair again.")
    return record


# --- pairing -----------------------------------------------------------------
@router.post("/extension/pairing-code", dependencies=[Depends(require_csrf)])
def pairing_code(request: Request, user: Account = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    rate_limit(db, request, "pairing-code", user.user_id)
    pick = lambda: "".join(secrets.choice(CODE_LETTERS) for _ in range(4))  # noqa: E731
    code = f"{pick()}-{pick()}"
    db.add(PairingCodeRecord(code=code, created_at=_now(), used=False))
    db.flush()
    db.add(AccountPairing(code=code, user_id=user.user_id))
    db.commit()
    return {"code": code, "expiresAt": (_now() + CODE_TTL).isoformat()}


class PairRequest(BaseModel):
    code: str = Field(min_length=1, max_length=16)


@router.post("/extension/pair")
def pair(body: PairRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    rate_limit(db, request, "pair")
    code = body.code.strip().upper()
    record = db.scalar(select(PairingCodeRecord).where(PairingCodeRecord.code == code).with_for_update())
    owner = db.get(AccountPairing, code)
    if record is None or owner is None or record.used or record.created_at.replace(tzinfo=record.created_at.tzinfo or timezone.utc) < _now() - CODE_TTL:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That code didn't work. Get a new one from the workspace and try again.")
    record.used = True
    token = "tg_" + secrets.token_urlsafe(32)
    ext = ExtensionTokenRecord(token_id=f"ext_{secrets.token_hex(6)}", token_hash=_hash(token), name="TrustGraph workspace", created_at=_now())
    db.add(ext)
    db.flush()
    db.add(AccountExtension(token_id=ext.token_id, user_id=owner.user_id, last_seen=_now()))
    db.commit()
    return {"token": token, "account": {"name": "TrustGraph workspace"}}


# --- results (verdicts only) ----------------------------------------------------
class ResultIn(BaseModel):
    """trustgraph_extension/shared/result.js RESULT_FIELDS, nothing else."""

    model_config = ConfigDict(extra="forbid")

    id: str
    timestamp: float = Field(ge=0, le=4102444800000, allow_inf_nan=False)
    riskLevel: Literal["low", "caution", "high"]
    score: int = Field(ge=0, le=100)
    signalIds: list[str] = Field(max_length=8)
    channel: str
    domain: str
    hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @field_validator("id")
    @classmethod
    def _id(cls, v):
        if not RESULT_ID.fullmatch(v):
            raise ValueError("bad id")
        return v

    @field_validator("signalIds")
    @classmethod
    def _signals(cls, v):
        if not all(TOKEN.fullmatch(s) for s in v):
            raise ValueError("signal ids are short tokens, never text")
        return v

    @field_validator("channel")
    @classmethod
    def _channel(cls, v):
        if not TOKEN.fullmatch(v):
            raise ValueError("bad channel")
        return v

    @field_validator("domain")
    @classmethod
    def _domain(cls, v):
        if not HOST.fullmatch(v):
            raise ValueError("domain is a hostname only")
        return v


def result_out(r: ExtensionResultRecord) -> dict:
    ts = r.timestamp if r.timestamp.tzinfo else r.timestamp.replace(tzinfo=timezone.utc)
    return {"id": r.result_id, "timestamp": int(ts.timestamp() * 1000), "riskLevel": r.risk_level, "score": r.score,
            "signalIds": list(r.signal_ids or []), "channel": r.channel, "domain": r.domain}


@router.post("/results", status_code=status.HTTP_201_CREATED)
def save_result(body: ResultIn, ext: ExtensionTokenRecord = Depends(paired_extension), db: Session = Depends(get_db)) -> dict:
    record = db.get(ExtensionResultRecord, body.id)
    if record is not None and record.token_id != ext.token_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Result id already used")
    if record is None:
        record = ExtensionResultRecord(result_id=body.id, token_id=ext.token_id, feedback="none")
        db.add(record)
    record.timestamp = datetime.fromtimestamp(body.timestamp / 1000, tz=timezone.utc)
    record.risk_level, record.score, record.signal_ids = body.riskLevel, body.score, body.signalIds
    record.channel, record.domain = body.channel, body.domain
    db.get(AccountExtension, ext.token_id).last_seen = _now()
    db.commit()
    return {"ok": True, "id": body.id}


def _mine(ext: ExtensionTokenRecord, db: Session):
    return db.scalars(select(ExtensionResultRecord).where(ExtensionResultRecord.token_id == ext.token_id)
                      .order_by(ExtensionResultRecord.timestamp.desc())).all()


@router.get("/results")
def list_results(ext: ExtensionTokenRecord = Depends(paired_extension), db: Session = Depends(get_db)) -> list[dict]:
    return [result_out(r) for r in _mine(ext, db)]


@router.get("/export")
def export_results(ext: ExtensionTokenRecord = Depends(paired_extension), db: Session = Depends(get_db)) -> list[dict]:
    return [result_out(r) for r in _mine(ext, db)]


@router.delete("/results/{result_id}")
def delete_result(result_id: str, ext: ExtensionTokenRecord = Depends(paired_extension), db: Session = Depends(get_db)) -> dict:
    db.execute(delete(ExtensionResultRecord).where(ExtensionResultRecord.result_id == result_id,
                                                   ExtensionResultRecord.token_id == ext.token_id))
    db.commit()
    return {"ok": True}


@router.delete("/results")
def delete_all_results(ext: ExtensionTokenRecord = Depends(paired_extension), db: Session = Depends(get_db)) -> dict:
    db.execute(delete(ExtensionResultRecord).where(ExtensionResultRecord.token_id == ext.token_id))
    db.commit()
    return {"ok": True}


class FeedbackIn(BaseModel):
    resultId: str = Field(min_length=1, max_length=64)


@router.post("/feedback")
def feedback(body: FeedbackIn, ext: ExtensionTokenRecord = Depends(paired_extension), db: Session = Depends(get_db)) -> dict:
    """The verdict id only. Marks a synced Result as a false alarm."""
    record = db.get(ExtensionResultRecord, body.resultId)
    if record is not None and record.token_id == ext.token_id:
        record.feedback = "false_alarm"
        db.commit()
        return {"ok": True, "found": True}
    return {"ok": True, "found": False}


# --- heartbeat --------------------------------------------------------------------
class HeartbeatIn(BaseModel):
    source: str = Field(default="extension", max_length=40)
    ts: float | None = None


@router.post("/status")
def heartbeat(body: HeartbeatIn, ext: ExtensionTokenRecord = Depends(paired_extension), db: Session = Depends(get_db)) -> dict:
    db.get(AccountExtension, ext.token_id).last_seen = _now()
    db.commit()
    return {"ok": True}
