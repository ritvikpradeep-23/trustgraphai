"""Real PostgreSQL/API checks in a temporary schema, wholly rolled back.

Never sets TEST_DATABASE_URL to the existing database; does not touch public
tables or leave demonstration users, sessions, tokens or results behind.
"""
import secrets
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.core.accounts import Account, AccountCheck, AccountSession, digest
from app.core.database import Base, engine, get_db
from app.main import app


def run():
    schema = "tg_verify_" + secrets.token_hex(8)
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            Base.metadata.create_all(connection)
            db = Session(bind=connection, join_transaction_mode="create_savepoint")
            app.dependency_overrides[get_db] = lambda: db
            a, b = TestClient(app), TestClient(app)
            password = secrets.token_urlsafe(24)
            def signup(client, name):
                bootstrap = client.get("/api/auth/session")
                assert bootstrap.status_code == 200
                assert "HttpOnly" in bootstrap.headers["set-cookie"]
                csrf = bootstrap.json()["csrfToken"]
                response = client.post("/api/auth/register", json={
                    "name": name, "email": name + "@example.invalid", "password": password,
                }, headers={"X-CSRF-Token": csrf})
                assert response.status_code == 201, response.status_code
                return response.json()
            account_a, account_b = signup(a, "verify-a"), signup(b, "verify-b")
            csrf_a = {"X-CSRF-Token": account_a["csrfToken"]}
            csrf_b = {"X-CSRF-Token": account_b["csrfToken"]}
            assert a.get("/api/auth/me").json()["id"] == account_a["user"]["id"]
            stored = db.get(Account, account_a["user"]["id"])
            assert stored.password_hash != password and "pbkdf2_sha256" in stored.password_hash
            original_cookie = a.cookies.get("tg_session")
            assert db.get(AccountSession, digest(original_cookie)) is not None
            assert a.post("/api/extension/pairing-code").status_code == 403
            assert a.post("/api/extension/pairing-code", headers={"X-CSRF-Token": "incorrect"}).status_code == 403
            code = a.post("/api/extension/pairing-code", headers=csrf_a).json()["code"]
            paired = a.post("/api/extension/pair", json={"code": code})
            assert paired.status_code == 200
            assert a.post("/api/extension/pair", json={"code": code}).status_code == 400
            extension = {"Authorization": "Bearer " + paired.json()["token"]}
            assert a.post("/api/status", json={"source": "whatsapp"}).status_code == 401
            assert a.post("/api/status", json={"source": "whatsapp"}, headers=extension).status_code == 200
            assert a.get("/api/workspace/status").json()["state"] == "CONNECTED"
            assert b.get("/api/workspace/status").json()["state"] == "NOT CONNECTED"
            result = {"id": "verify-result-12345678", "timestamp": time.time() * 1000,
                      "riskLevel": "high", "score": 86, "signalIds": ["impersonation"],
                      "channel": "whatsapp", "domain": "web.whatsapp.com"}
            assert a.post("/api/results", json={**result, "text": "DO NOT STORE"}, headers=extension).status_code == 422
            assert a.post("/api/results", json=result, headers=extension).status_code == 201
            assert a.get("/api/workspace/detections").json()[0]["id"] == result["id"]
            assert b.get("/api/workspace/detections").json() == []
            assert b.get("/api/workspace/detections/" + result["id"]).status_code == 404
            # Check metadata persistence without retaining the supplied text.
            private = "A harmless test sentence about meeting tomorrow for a walk."
            check = a.post("/api/workspace/checks", json={"text": private, "channel": "other"}, headers=csrf_a)
            assert check.status_code == 200
            saved = db.get(AccountCheck, check.json()["detection_id"])
            assert private not in str(saved.view)
            assert len(a.get("/api/workspace/detections").json()) == 2
            assert b.get("/api/workspace/detections").json() == []
            assert a.post("/api/auth/logout", headers=csrf_a).status_code == 200
            assert a.get("/api/workspace/detections").status_code == 401
            a.cookies.set("tg_session", original_cookie)
            assert a.get("/api/auth/me").status_code == 401
            a.cookies.clear()
            csrf = a.get("/api/auth/session").json()["csrfToken"]
            login = a.post("/api/auth/login", json={"email": "VERIFY-A@example.invalid",
                           "password": password, "remember": True}, headers={"X-CSRF-Token": csrf})
            assert login.status_code == 200
            assert "Max-Age=2592000" in login.headers["set-cookie"]
            assert original_cookie != a.cookies.get("tg_session")
            csrf = login.json()["csrfToken"]
            failed = a.post("/api/auth/login", json={"email": "verify-a@example.invalid", "password": "wrong"},
                            headers={"X-CSRF-Token": csrf})
            assert failed.status_code == 401 and failed.json()["detail"] == "Email or password is incorrect."
            for _ in range(6):
                assert a.post("/api/auth/login", json={"email": "verify-a@example.invalid", "password": "wrong"},
                              headers={"X-CSRF-Token": csrf}).status_code == 401
            assert a.post("/api/auth/login", json={"email": "verify-a@example.invalid", "password": "wrong"},
                          headers={"X-CSRF-Token": csrf}).status_code == 429
            print("Real PostgreSQL/API checks passed: accounts, cookies, CSRF, rotation/revocation, pairing, heartbeat, sync, per-account history and metadata privacy.")
            db.close()
        finally:
            app.dependency_overrides.clear()
            transaction.rollback()
            print("Temporary verification schema and every test row rolled back. Public tables untouched.")


if __name__ == "__main__":
    run()
