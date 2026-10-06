import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, SubmissionRecord
from app.services.pattern_detection import verdict
from app.services.previous_report_matcher import find_previous_report_matches
from scripts.seed_demo_patterns import seed

PATTERNS = json.loads((Path(__file__).resolve().parents[1] / "data/demo_scam_patterns.json").read_text())


class FakeDB:
    def __init__(self):
        self.records = {}
        self.commits = 0
    def get(self, model, key):
        return self.records.get((model, key))
    def add(self, record):
        key = record.submission_id if isinstance(record, SubmissionRecord) else record.report_id
        self.records[(type(record), key)] = record
    def flush(self):
        pass
    def commit(self):
        self.commits += 1
    def execute(self, statement):
        return [(SimpleNamespace(report_id="report_" + p["id"], report_type="Demo: " + p["title"], status="synthetic_demo"),
                 SimpleNamespace(submission_id=p["id"], text=p["text"], caption=None, url=None)) for p in PATTERNS]


class PatternTests(unittest.TestCase):
    def test_all_demo_messages_and_normalized_variants_match(self):
        for p in PATTERNS:
            for text in (p["text"], p["text"].upper().replace(".", "!!!")):
                with self.subTest(pattern=p["title"]):
                    matches = find_previous_report_matches(FakeDB(), text=text, url=None, submission_id=None)
                    score, level, reasons = verdict(matches)
                    self.assertEqual(level, "HIGH")
                    self.assertEqual(score, 1)
                    self.assertTrue(any(m.report_id == "report_" + p["id"] for m in matches))
                    self.assertTrue(any("synthetic" in reason for reason in reasons))

    def test_benign_controls_and_short_input_do_not_become_safe_verdicts(self):
        for text in ("hh", "Lunch at the canteen at one? Please bring your exam notes.",
                     "Never share your OTP or UPI PIN with anyone. Contact your bank using its official number."):
            matches = find_previous_report_matches(FakeDB(), text=text, url=None, submission_id=None)
            score, level, reasons = verdict(matches)
            self.assertEqual(level, "UNKNOWN")
            self.assertIsNone(score)
            self.assertIn("does not prove", reasons[1])

    def test_seed_is_idempotent_and_preserves_existing_records(self):
        db = FakeDB()
        self.assertEqual(seed(db, PATTERNS), 12)
        self.assertEqual(seed(db, PATTERNS), 0)
        self.assertEqual(len(db.records), 24)
        original = db.get(SubmissionRecord, PATTERNS[0]["id"])
        original.text = "Existing user record"
        with self.assertRaises(ValueError):
            seed(db, PATTERNS)
        self.assertEqual(original.text, "Existing user record")

    def test_endpoint_returns_pattern_evidence_without_calling_ai(self):
        db = FakeDB()
        app.dependency_overrides[get_db] = lambda: db
        try:
            with patch("app.services.ai_model.TrustGraphAI.analyze", side_effect=AssertionError("AI must not be called")):
                response = TestClient(app).post("/api/detect", json={"channel": "other", "text": PATTERNS[0]["text"]})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["risk_level"], "HIGH")
            self.assertEqual(response.json()["previous_report_matches"][0]["status"], "synthetic_demo")
            self.assertEqual(db.commits, 0)
        finally:
            app.dependency_overrides.clear()
