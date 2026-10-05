from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_health_says_ok():
    client = TestClient(create_app(Settings()))
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_cors_allows_configured_origins_only():
    client = TestClient(create_app(Settings(cors_origins="http://site.test,chrome-extension://abc123")))
    ok = client.get("/health", headers={"Origin": "chrome-extension://abc123"})
    assert ok.headers.get("access-control-allow-origin") == "chrome-extension://abc123"
    other = client.get("/health", headers={"Origin": "http://evil.test"})
    assert "access-control-allow-origin" not in other.headers


def test_settings_come_from_environment(monkeypatch):
    monkeypatch.setenv("SCAM_HIGH_THRESHOLD", "0.9")
    monkeypatch.setenv("VIDEO_MAX_FRAMES", "12")
    s = Settings()
    assert s.scam_high_threshold == 0.9 and s.video_max_frames == 12
