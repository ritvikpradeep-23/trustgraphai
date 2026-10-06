import re
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.accounts import (
    Account, AccountSession, AccountCheck, AccountExtension, AccountPairing,
    COOKIE, DUMMY_HASH, current_user, hash_password, new_session, now,
    rate_limit, require_csrf, session_record, user_view, verify_password,
)
from app.core.database import get_db, ExtensionTokenRecord, ExtensionResultRecord, PairingCodeRecord

router = APIRouter(prefix="/auth", tags=["Accounts"])


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)
    remember: bool = False

    @field_validator("email")
    @classmethod
    def email_valid(cls, value):
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address.")
        return value


class RegisterIn(LoginIn):
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=15, max_length=128)

    @field_validator("password")
    @classmethod
    def password_valid(cls, value):
        if not value.strip():
            raise ValueError("Choose a non-blank passphrase.")
        return value

    @field_validator("name")
    @classmethod
    def name_valid(cls, value):
        if not value.strip():
            raise ValueError("Enter your name.")
        return value.strip()


@router.get("/session")
def session(request: Request, response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    record = session_record(request, db)
    if not record:
        rate_limit(db, request, "session")
        record = new_session(request, response, db)
        db.commit()
    user = db.get(Account, record.user_id) if record.user_id else None
    return {"user": user_view(user) if user else None, "csrfToken": record.csrf_token}


@router.post("/login", dependencies=[Depends(require_csrf)])
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    rate_limit(db, request, "login", body.email)
    user = db.scalar(select(Account).where(Account.email == body.email))
    valid = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "Email or password is incorrect.")
    record = new_session(request, response, db, user.user_id, body.remember)
    db.commit()
    return {"user": user_view(user), "csrfToken": record.csrf_token}


@router.post("/register", status_code=201, dependencies=[Depends(require_csrf)])
def register(body: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)):
    rate_limit(db, request, "register", body.email)
    user = Account(user_id="usr_" + secrets.token_hex(16), name=body.name, email=body.email,
                   password_hash=hash_password(body.password), created_at=now())
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Unable to create this account. Try signing in or use another email.")
    record = new_session(request, response, db, user.user_id, body.remember)
    db.commit()
    return {"user": user_view(user), "csrfToken": record.csrf_token}


@router.post("/logout", dependencies=[Depends(require_csrf)])
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    record = session_record(request, db)
    if record:
        db.delete(record)
        db.commit()
    response.delete_cookie(COOKIE, path="/")
    response.headers["Cache-Control"] = "no-store"
    return {"ok": True}


@router.get("/me")
def me(response: Response, user: Account = Depends(current_user)):
    response.headers["Cache-Control"] = "no-store"
    return user_view(user)


class ProfileIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def valid_name(cls, value):
        if not value.strip():
            raise ValueError("Enter your name.")
        return value.strip()


class PasswordChangeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=15, max_length=128)

    @field_validator("new_password")
    @classmethod
    def valid_password(cls, value):
        if not value.strip():
            raise ValueError("Choose a non-blank passphrase.")
        return value


class DeleteAccountIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=1, max_length=128)
    confirmation: str = Field(pattern=r"^DELETE$")


@router.patch("/profile", dependencies=[Depends(require_csrf)])
def update_profile(body: ProfileIn, user: Account = Depends(current_user), db: Session = Depends(get_db)):
    user.name = body.name
    db.commit()
    return user_view(user)


@router.post("/password", dependencies=[Depends(require_csrf)])
def change_password(body: PasswordChangeIn, request: Request, response: Response,
                    user: Account = Depends(current_user), db: Session = Depends(get_db)):
    rate_limit(db, request, "password-change", user.user_id)
    locked = db.scalar(select(Account).where(Account.user_id == user.user_id).with_for_update().execution_options(populate_existing=True))
    if not locked or not verify_password(body.current_password, locked.password_hash):
        raise HTTPException(401, "Current password is incorrect.")
    if body.current_password == body.new_password:
        raise HTTPException(400, "Choose a different new passphrase.")
    locked.password_hash = hash_password(body.new_password)
    # Revoke old website sessions, including this one, and issue a fresh cookie/CSRF.
    db.execute(delete(AccountSession).where(AccountSession.user_id == locked.user_id))
    record = new_session(request, response, db, locked.user_id)
    db.commit()
    return {"user": user_view(locked), "csrfToken": record.csrf_token}


@router.delete("/account", dependencies=[Depends(require_csrf)])
def delete_account(body: DeleteAccountIn, request: Request, response: Response,
                   user: Account = Depends(current_user), db: Session = Depends(get_db)):
    rate_limit(db, request, "account-delete", user.user_id)
    locked = db.scalar(select(Account).where(Account.user_id == user.user_id).with_for_update().execution_options(populate_existing=True))
    if not locked or not verify_password(body.password, locked.password_hash):
        raise HTTPException(401, "Current password is incorrect.")
    # Explicit dependent-first deletion: no cascade or broad legacy-data deletion.
    token_ids = list(db.scalars(select(AccountExtension.token_id).where(AccountExtension.user_id == locked.user_id)))
    codes = list(db.scalars(select(AccountPairing.code).where(AccountPairing.user_id == locked.user_id)))
    db.execute(delete(ExtensionResultRecord).where(ExtensionResultRecord.token_id.in_(token_ids)))
    db.execute(delete(AccountCheck).where(AccountCheck.user_id == locked.user_id))
    db.execute(delete(AccountExtension).where(AccountExtension.user_id == locked.user_id))
    db.execute(delete(ExtensionTokenRecord).where(ExtensionTokenRecord.token_id.in_(token_ids)))
    db.execute(delete(AccountPairing).where(AccountPairing.user_id == locked.user_id))
    db.execute(delete(PairingCodeRecord).where(PairingCodeRecord.code.in_(codes)))
    db.execute(delete(AccountSession).where(AccountSession.user_id == locked.user_id))
    db.delete(locked)
    db.commit()
    response.delete_cookie(COOKIE, path="/")
    response.headers["Cache-Control"] = "no-store"
    return {"ok": True}
