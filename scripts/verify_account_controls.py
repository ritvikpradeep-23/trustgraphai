"""Verify account mutations in a temporary PostgreSQL schema, then roll back.

Never deletes existing user data. Checks owner isolation, CSRF, password rotation,
history deletion and authenticated account deletion with paired-token revocation.
"""
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.core.accounts import Account, AccountCheck, AccountExtension, AccountPairing, AccountSession, digest
from app.core.database import Base, ExtensionTokenRecord, PairingCodeRecord, engine, get_db
from app.main import app


def run():
    schema = "tg_controls_verify_" + secrets.token_hex(8)
    with engine.connect() as connection:
        transaction = connection.begin()
        db = None
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            Base.metadata.create_all(connection)
            db = Session(bind=connection, join_transaction_mode="create_savepoint")
            app.dependency_overrides[get_db] = lambda: db
            a, b, old_a = TestClient(app), TestClient(app), TestClient(app)
            password = secrets.token_urlsafe(24)
            new_password = secrets.token_urlsafe(24)

            def register(client, name):
                csrf = client.get("/api/auth/session").json()["csrfToken"]
                response = client.post("/api/auth/register", json={"name": name,
                    "email": name + "@example.invalid", "password": password}, headers={"X-CSRF-Token": csrf})
                assert response.status_code == 201, "Register test account"
                return response.json()["user"]["id"], {"X-CSRF-Token": response.json()["csrfToken"]}

            a_id, headers = register(a, "controls-a")
            b_id, b_headers = register(b, "controls-b")
            assert a.patch("/api/auth/profile", json={"name": "Changed"}).status_code == 403
            assert a.patch("/api/auth/profile", json={"name": " "}, headers=headers).status_code == 422
            response = a.patch("/api/auth/profile", json={"name": " Updated Name "}, headers=headers)
            assert response.status_code == 200 and a.get("/api/auth/me").json()["name"] == "Updated Name"
            assert b.get("/api/auth/me").json()["name"] == "controls-b"

            def pair(client, auth_headers):
                response = client.post("/api/extension/pairing-code", headers=auth_headers)
                assert response.status_code == 200
                code = response.json()["code"]
                response = client.post("/api/extension/pair", json={"code": code})
                assert response.status_code == 200
                return code, {"Authorization": "Bearer " + response.json()["token"]}

            a_code, ext_a = pair(a, headers)
            b_code, ext_b = pair(b, b_headers)
            def add_checks(client, csrf, extension_headers, suffix):
                response = client.post("/api/workspace/checks", json={"channel": "other",
                    "text": "The volunteer meeting has moved to Wednesday afternoon."}, headers=csrf)
                assert response.status_code == 200
                response = client.post("/api/results", json={"id": "controls-result-" + suffix,
                    "timestamp": 1791288000000, "riskLevel": "caution", "score": 75,
                    "signalIds": ["urgency"], "channel": "other", "domain": "example.invalid"}, headers=extension_headers)
                assert response.status_code in {200, 201}

            add_checks(a, headers, ext_a, "a")
            add_checks(b, b_headers, ext_b, "b")
            assert len(a.get("/api/workspace/detections").json()) == 2
            assert len(b.get("/api/workspace/detections").json()) == 2
            own = next(item for item in a.get("/api/workspace/detections").json() if item["engineVersion"] != "browser-extension")
            own_path = "/api/workspace/detections/" + own["id"]
            assert a.patch(own_path, json={"status": "reviewed"}).status_code == 403
            assert b.patch(own_path, json={"status": "reviewed"}, headers=b_headers).status_code == 404
            assert a.patch(own_path, json={"riskScore": 0}, headers=headers).status_code == 422
            reviewed = a.patch(own_path, json={"status": "reviewed", "feedback": "false_alarm"}, headers=headers)
            assert reviewed.status_code == 200 and reviewed.json()["riskScore"] == own["riskScore"]
            saved_review = a.get(own_path).json()
            assert saved_review["status"] == "reviewed" and saved_review["feedback"] == "false_alarm"
            old_csrf = old_a.get("/api/auth/session").json()["csrfToken"]
            response = old_a.post("/api/auth/login", json={"email": "controls-a@example.invalid", "password": password}, headers={"X-CSRF-Token": old_csrf})
            assert response.status_code == 200
            old_cookie = old_a.cookies.get("tg_session")
            response = a.post("/api/auth/password", json={"current_password": "incorrect", "new_password": new_password}, headers=headers)
            assert response.status_code == 401
            assert old_a.get("/api/auth/me").status_code == 200
            response = a.post("/api/auth/password", json={"current_password": password, "new_password": new_password}, headers=headers)
            assert response.status_code == 200 and new_password not in response.text
            rotated = {"X-CSRF-Token": response.json()["csrfToken"]}
            assert rotated != headers and old_a.get("/api/auth/me").status_code == 401
            assert db.get(AccountSession, digest(old_cookie)) is None
            assert a.delete("/api/workspace/detections", headers=headers).status_code == 403
            assert a.delete("/api/workspace/detections").status_code == 403
            response = a.delete("/api/workspace/detections", headers=rotated)
            assert response.status_code == 200 and response.json()["deleted"] == 2
            assert a.get("/api/workspace/detections").json() == []
            assert len(b.get("/api/workspace/detections").json()) == 2
            assert a.get("/api/results", headers=ext_a).status_code == 200, "History deletion must not revoke pairing"
            add_checks(a, rotated, ext_a, "a-new")
            response = a.request("DELETE", "/api/auth/account", json={"password": "incorrect", "confirmation": "DELETE"}, headers=rotated)
            assert response.status_code == 401 and db.get(Account, a_id) is not None
            response = a.request("DELETE", "/api/auth/account", json={"password": new_password, "confirmation": "not-confirmed"}, headers=rotated)
            assert response.status_code == 422 and new_password not in response.text
            response = a.request("DELETE", "/api/auth/account", json={"password": new_password, "confirmation": "DELETE"}, headers=rotated)
            assert response.status_code == 200 and response.json()["ok"]
            assert a.get("/api/auth/me").status_code == 401
            assert a.get("/api/results", headers=ext_a).status_code == 401
            assert db.get(Account, a_id) is None and db.get(Account, b_id) is not None
            assert not list(db.scalars(select(AccountCheck).where(AccountCheck.user_id == a_id)))
            assert not list(db.scalars(select(AccountSession).where(AccountSession.user_id == a_id)))
            assert not list(db.scalars(select(AccountExtension).where(AccountExtension.user_id == a_id)))
            assert not list(db.scalars(select(AccountPairing).where(AccountPairing.user_id == a_id)))
            assert db.get(PairingCodeRecord, a_code) is None and db.get(PairingCodeRecord, b_code) is not None
            assert len(list(db.scalars(select(ExtensionTokenRecord)))) == 1
            assert b.get("/api/auth/me").status_code == 200
            assert b.get("/api/results", headers=ext_b).status_code == 200
            assert len(b.get("/api/workspace/detections").json()) == 2
            print("Account controls passed: profile persistence, owner-only review/feedback without score edits, password reauthentication/session rotation, CSRF, history deletion, dependent account deletion and extension-token revocation; second account untouched.")
        finally:
            if db is not None:
                db.close()
            app.dependency_overrides.clear()
            transaction.rollback()
            print("Temporary schema and all test rows rolled back; existing user data untouched.")


if __name__ == "__main__":
    try:
        run()
    except Exception as error:
        # Exceptions from DB drivers may contain a DSN; never print them verbatim.
        print(f"Account verification failed ({type(error).__name__}); no credentials displayed.", file=sys.stderr)
        sys.exit(1)
