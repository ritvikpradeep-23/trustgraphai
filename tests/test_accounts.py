from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.core.accounts import hash_password, verify_password, require_csrf, session_record, now
from app.api.auth import LoginIn, RegisterIn, ProfileIn, PasswordChangeIn, DeleteAccountIn
from app.core.database import get_db
from app.main import app


def test_password_hashes_are_salted_and_not_reversible_plaintext():
    password = "a deliberately long passphrase"
    a, b = hash_password(password), hash_password(password)
    assert a != b and password not in a
    assert verify_password(password, a)
    assert not verify_password("wrong password", a)
    assert not verify_password(password, "corrupt")


def test_account_validation():
    assert LoginIn(email=" USER@EXAMPLE.INVALID ", password="x").email == "user@example.invalid"
    with pytest.raises(ValueError):
        LoginIn(email="invalid", password="x")
    with pytest.raises(ValueError):
        RegisterIn(name="User", email="user@example.invalid", password="too short")
    with pytest.raises(ValueError):
        RegisterIn(name=" ", email="user@example.invalid", password="a secure long passphrase")
    with pytest.raises(ValueError):
        RegisterIn(name="User", email="user@example.invalid", password=" " * 20)


def test_account_controls_validate_required_parameters():
    assert ProfileIn(name="  Updated  ").name == "Updated"
    with pytest.raises(ValueError):
        ProfileIn(name=" ")
    with pytest.raises(ValueError):
        ProfileIn(name="Updated", user_id="another-account")
    for password in ["short", " " * 20, "x" * 129]:
        with pytest.raises(ValueError):
            PasswordChangeIn(current_password="current", new_password=password)
    with pytest.raises(ValueError):
        DeleteAccountIn(password="valid", confirmation="no")


def test_account_controls_require_signin_csrf_and_never_echo_passwords():
    db = Mock()
    db.get.return_value = None
    app.dependency_overrides[get_db] = lambda: db
    try:
        client = TestClient(app)
        assert client.patch("/api/auth/profile", json={"name": "Changed"}).status_code == 403
        assert client.post("/api/auth/password", json={"current_password": "old", "new_password": "secure long passphrase"}).status_code == 403
        assert client.delete("/api/workspace/detections").status_code == 403
        assert client.patch("/api/workspace/detections/example", json={"status": "reviewed"}).status_code == 403
        assert client.request("DELETE", "/api/auth/account", json={"password": "old", "confirmation": "DELETE"}).status_code == 403
        app.dependency_overrides[require_csrf] = lambda: None
        for path in ["/api/auth/profile", "/api/auth/password", "/api/auth/account"]:
            method = {"/api/auth/profile": "PATCH", "/api/auth/password": "POST", "/api/auth/account": "DELETE"}[path]
            assert client.request(method, path, json={}).status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_expired_sessions_and_csrf_cannot_authenticate():
    db = Mock()
    request = SimpleNamespace(cookies={"tg_session": "random-cookie"}, headers={})
    db.get.return_value = SimpleNamespace(expires_at=now() - timedelta(seconds=1), csrf_token="expected")
    assert session_record(request, db) is None
    with pytest.raises(HTTPException) as denied:
        require_csrf(request, db)
    assert denied.value.status_code == 403
    db.get.return_value.expires_at = now() + timedelta(minutes=1)
    request.headers = {"x-csrf-token": "非ASCII"}
    with pytest.raises(HTTPException) as denied:
        require_csrf(request, db)
    assert denied.value.status_code == 403
    request.headers = {"x-csrf-token": "expected", "sec-fetch-site": "cross-site"}
    with pytest.raises(HTTPException):
        require_csrf(request, db)


def test_workspace_and_pairing_are_not_accessible_without_signin():
    db = Mock()
    db.get.return_value = None
    app.dependency_overrides[get_db] = lambda: db
    try:
        client = TestClient(app)
        for path in ["/api/workspace/detections", "/api/workspace/status", "/api/auth/me"]:
            assert client.get(path).status_code == 401
        assert client.post("/api/extension/pairing-code").status_code in (401, 403)
    finally:
        app.dependency_overrides.clear()


def test_hosted_legacy_data_is_not_public_and_validation_never_echoes_passwords():
    from app.core.accounts import require_csrf
    app.dependency_overrides[get_db] = lambda: Mock()
    app.dependency_overrides[require_csrf] = lambda: None
    try:
        client = TestClient(app, base_url="https://testserver")
        for path in ["/api/detections", "/api/reports", "/api/relationships"]:
            assert client.get(path).status_code == 403
        assert client.post("/api/detect", json={"text": "Test", "channel": "other", "submission_id": "legacy"}).status_code == 403
        secret = "should-never-be-echoed" * 10
        response = client.post("/api/auth/login", json={"email": "user@example.invalid", "password": secret})
        assert response.status_code == 422
        assert secret not in response.text and '"input"' not in response.text
    finally:
        app.dependency_overrides.clear()
