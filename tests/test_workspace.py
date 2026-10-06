import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.api.workspace import detection_view
from app.core.accounts import current_user
from app.core.database import DetectionRecord, get_db
from app.main import app


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.record = SimpleNamespace(
            detection_id="det_test", risk_level="MEDIUM", risk_score=.5,
            created_at=datetime(2026, 10, 6, tzinfo=timezone.utc),
            signals={"anomaly": .4, "continuity": None}, reasons=["Backend reason"],
            submission=SimpleNamespace(source="gmail", url="https://example.com/private?token=secret", text="PRIVATE MESSAGE", caption="PRIVATE CAPTION", sender="PRIVATE SENDER"),
        )
        records = [self.record]
        class FakeSession:
            # Detection queries get the fake records; the extension tables
            # (synced verdicts, pairing, heartbeats) are empty.
            def _detections(self, statement):
                return any(d.get("entity") is DetectionRecord for d in statement.column_descriptions)
            def scalars(self, statement):
                return SimpleNamespace(all=lambda: records if self._detections(statement) else [])
            def scalar(self, statement):
                return (records[0] if records else None) if self._detections(statement) else None
            def get(self, _model, _key):
                return None
        def override():
            yield FakeSession()
        self.records = records
        app.dependency_overrides[get_db] = override
        app.dependency_overrides[current_user] = lambda: SimpleNamespace(user_id="test-account")
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_workspace_projection_does_not_expose_raw_submission(self):
        # Legacy records have no account owner; they are never exposed in
        # authenticated history. The compatibility projection is tested directly.
        self.assertEqual(self.client.get("/api/workspace/detections").json(), [])
        payload = [detection_view(self.record)]
        self.assertEqual(payload[0]["riskLevel"], "CAUTION")
        self.assertEqual(payload[0]["site"], "example.com")
        self.assertFalse(payload[0]["editable"])
        for private in ("PRIVATE MESSAGE", "PRIVATE CAPTION", "PRIVATE SENDER", "secret", "/private"):
            self.assertNotIn(private, str(payload))
        self.assertNotIn("submission", payload[0])

    def test_pending_does_not_become_a_zero_or_low_risk_score(self):
        self.record.risk_level = "PENDING"
        self.record.risk_score = None
        payload = detection_view(self.record)
        self.assertEqual(payload["riskLevel"], "PENDING")
        self.assertIsNone(payload["riskScore"])
        self.assertIsNone(payload["signals"][1]["score"])

    def test_invalid_scores_are_unavailable_and_valid_zero_is_preserved(self):
        for invalid in (True, float("nan"), float("inf"), -1, 2, "0.5"):
            self.record.risk_score = invalid
            self.assertEqual(detection_view(self.record)["riskLevel"], "PENDING")
        self.record.risk_score = 0
        self.assertEqual(detection_view(self.record)["riskScore"], 0)
        self.assertEqual(detection_view(self.record)["riskLevel"], "CAUTION")

    def test_detail_not_found_and_existing_api_paths(self):
        self.assertEqual(self.client.get("/api/workspace/detections/det_test").status_code, 404)
        self.records.clear()
        self.assertEqual(self.client.get("/api/workspace/detections/missing").status_code, 404)
        for path in ("/api/detections", "/api/detect", "/api/submit", "/api/url/analyze"):
            self.assertIn(path, app.openapi()["paths"])

    def test_status_is_not_an_authenticated_or_paired_session(self):
        payload = self.client.get("/api/workspace/status").json()
        self.assertTrue(payload["authentication"])
        self.assertFalse(payload["extensionPairing"])
        self.assertIsInstance(payload["aiAvailable"], bool)

    def test_static_spa_does_not_swallow_api_404_or_missing_assets(self):
        with TemporaryDirectory() as directory:
            Path(directory, "index.html").write_text("<html>Workspace</html>", encoding="utf-8")
            with patch("app.main.FRONTEND_DIST", Path(directory)):
                self.assertEqual(self.client.get("/app/analytics").status_code, 200)
                self.assertEqual(self.client.get("/api/unknown").status_code, 404)
                self.assertEqual(self.client.get("/assets/missing.js").status_code, 404)
                self.assertEqual(self.client.get("/.env").status_code, 404)

    def test_missing_frontend_build_is_explicit(self):
        with TemporaryDirectory() as directory:
            with patch("app.main.FRONTEND_DIST", Path(directory)):
                self.assertEqual(self.client.get("/").status_code, 503)

    def test_cors_is_limited_to_configured_local_origins(self):
        allowed = self.client.options("/api/detect", headers={"Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "POST"})
        self.assertEqual(allowed.headers["access-control-allow-origin"], "http://127.0.0.1:5173")
        denied = self.client.options("/api/detect", headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST"})
        self.assertNotIn("access-control-allow-origin", denied.headers)
