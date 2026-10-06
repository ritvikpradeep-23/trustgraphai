"""PostgreSQL account tables and opaque cookie-session security."""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, Session, mapped_column
from app.core.database import Base, get_db


class Account(Base):
    __tablename__ = "tg_accounts"
    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AccountSession(Base):
    __tablename__ = "tg_account_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("tg_accounts.user_id"), index=True)
    csrf_token: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class AuthAttempt(Base):
    __tablename__ = "tg_auth_attempts"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    bucket: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempts: Mapped[int] = mapped_column(Integer)


class AccountPairing(Base):
    __tablename__ = "tg_account_pairing"
    code: Mapped[str] = mapped_column(ForeignKey("extension_pairing_codes.code"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("tg_accounts.user_id"), index=True)


class AccountExtension(Base):
    __tablename__ = "tg_account_extensions"
    token_id: Mapped[str] = mapped_column(ForeignKey("extension_tokens.token_id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("tg_accounts.user_id"), index=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AccountCheck(Base):
    """Projected verdict only: no analyzed message."""
    __tablename__ = "tg_account_checks"
    detection_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("tg_accounts.user_id"), index=True)
    view: Mapped[dict] = mapped_column(JSON)


COOKIE = "tg_session"
ITERATIONS = 600_000


def now():
    return datetime.now(timezone.utc)


def aware(value):
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_password(password):
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS).hex()
    return "$".join(("pbkdf2_sha256", str(ITERATIONS), salt, derived))


def verify_password(password, encoded):
    try:
        algorithm, iterations, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256" or int(iterations) != ITERATIONS:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


DUMMY_HASH = hash_password(secrets.token_urlsafe(32))


def rate_limit(db, request, action, email=None):
    """Atomic PostgreSQL counters, shared by all serverless instances."""
    bucket = int(now().timestamp()) // 900
    client = request.client.host if request.client else "unknown"
    keys = [(f"{action}:ip:{client}", 60 if action == "session" else 20)]
    if email:
        keys.append((f"{action}:email:{email}", 8))
    for identity, limit in keys:
        statement = insert(AuthAttempt).values(key=digest(identity), bucket=bucket, attempts=1)
        statement = statement.on_conflict_do_update(
            index_elements=["key", "bucket"], set_={"attempts": AuthAttempt.attempts + 1}
        ).returning(AuthAttempt.attempts)
        if db.execute(statement).scalar_one() > limit:
            db.commit()
            raise HTTPException(429, "Too many attempts. Try again in 15 minutes.", headers={"Retry-After": "900"})
    db.execute(delete(AuthAttempt).where(AuthAttempt.bucket < bucket - 1))
    db.commit()


def session_record(request, db):
    token = request.cookies.get(COOKIE)
    record = db.get(AccountSession, digest(token)) if token and len(token) <= 128 else None
    return record if record and aware(record.expires_at) > now() else None


def new_session(request, response, db, user_id=None, remember=False):
    db.execute(delete(AccountSession).where(AccountSession.expires_at <= now()))
    old = session_record(request, db)
    if old:
        db.delete(old)
    token = secrets.token_urlsafe(32)
    duration = timedelta(days=30) if remember else timedelta(hours=8) if user_id else timedelta(minutes=30)
    record = AccountSession(token_hash=digest(token), user_id=user_id,
                            csrf_token=secrets.token_urlsafe(32), expires_at=now() + duration)
    db.add(record)
    secure = bool(os.getenv("VERCEL")) or os.getenv("AUTH_COOKIE_SECURE") == "true" or request.url.scheme == "https"
    response.set_cookie(COOKIE, token, httponly=True, secure=secure, samesite="lax", path="/",
                        max_age=int(duration.total_seconds()) if remember else None)
    response.headers["Cache-Control"] = "no-store"
    return record


def require_csrf(request: Request, db: Session = Depends(get_db)):
    record = session_record(request, db)
    supplied = request.headers.get("x-csrf-token", "")
    if not record or not hmac.compare_digest(supplied.encode(), record.csrf_token.encode()):
        raise HTTPException(403, "Refresh this page and try again.")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Cross-site requests are not allowed.")
    return record


def current_user(request: Request, db: Session = Depends(get_db)):
    record = session_record(request, db)
    user = db.get(Account, record.user_id) if record and record.user_id else None
    if not user:
        raise HTTPException(401, "Sign in to your TrustGraph account.")
    return user


def user_view(user):
    return {"id": user.user_id, "name": user.name, "email": user.email,
            "joinedAt": aware(user.created_at).isoformat()}
