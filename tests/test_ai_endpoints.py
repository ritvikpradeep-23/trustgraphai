import unittest
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.detect import get_db as detect_get_db
from app.api.submission import get_db as submission_get_db
from app.main import app


class FakeSession:
    def __init__(self):
        self.added = []
        self.committed = False

    def add(self, record):
        self.added.append(record)

    def commit(self):
        self.committed = True


class AIDetectorEndpointTests(unittest.TestCase):
    def setUp(self):
        self.fake_session = FakeSession()

        def override_db():
            yield self.fake_session

        app.dependency_overrides[detect_get_db] = override_db
        app.dependency_overrides[submission_get_db] = override_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_ai_written_endpoint_reports_unavailable_without_a_score(self):
        response = self.client.post("/api/text/ai-check", json={"text": "ordinary text"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "ai_written_score": None,
                "available": False,
                "model": "AI integration pending",
                "reasons": ["AI-content analysis is pending AI integration; no score was produced."],
            },
        )

    def test_video_endpoint_reports_unavailable_without_a_score(self):
        response = self.client.post(
            "/api/video/analyze",
            files={"file": ("sample.mp4", BytesIO(b"not analyzed"), "video/mp4")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "fake_score": None,
                "available": False,
                "model": "AI integration pending",
                "reasons": ["Video analysis is pending AI integration; no score was produced."],
            },
        )

    def test_detect_keeps_legacy_fields_and_separates_ai_written_status(self):
        with patch("app.api.detect.find_previous_report_matches", return_value=[]):
            response = self.client.post(
                "/api/detect",
                json={"channel": "web_app", "text": "scam compatibility check"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["risk_level"], "UNKNOWN")
        self.assertIsNone(payload["risk_score"])
        self.assertIn("No stored scam pattern", payload["reasons"][0])
        self.assertEqual(payload["method"], "database-pattern-matching")
        self.assertEqual(payload["previous_report_matches"], [])
        self.assertEqual(set(payload["signals"]), {"anomaly", "continuity", "similarity", "precedent"})
        self.assertTrue(all(value is None for value in payload["signals"].values()))
        self.assertIsNone(payload["ai_written"])

    def test_existing_routes_remain_registered(self):
        paths = app.openapi()["paths"]
        for path in (
            "/health",
            "/api/detect",
            "/api/submit",
            "/api/detections",
            "/api/reports",
            "/api/text/ai-check",
            "/api/video/analyze",
        ):
            self.assertIn(path, paths)

    def test_submit_still_accepts_existing_universal_submission(self):
        response = self.client.post(
            "/api/submit",
            json={
                "source": "web_app",
                "content_type": "video",
                "media_reference": "local-upload-ref",
                "user_consent": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.fake_session.committed)
        self.assertEqual(self.fake_session.added[0].content_type, "video")


if __name__ == "__main__":
    unittest.main()
