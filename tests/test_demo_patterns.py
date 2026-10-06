import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, SubmissionRecord
from app.services.pattern_detection import verdict
from app.services.previous_report_matcher import MATCH_THRESHOLD, find_previous_report_matches, similarity_tier
from scripts.calibrate_demo_threshold import calibrate
from scripts.seed_demo_patterns import seed
from scripts.scam_catalog import load_catalog, seed_metadata, validate_catalog

PATTERNS = load_catalog()


class FakeDB:
    def __init__(self, patterns=None):
        self.records = {}
        self.commits = 0
        self.patterns = PATTERNS if patterns is None else patterns
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
        return [(SimpleNamespace(report_id="report_" + p["id"], report_type=seed_metadata(p)[2], status=seed_metadata(p)[1]),
                 SimpleNamespace(submission_id=p["id"], text=p["text"], caption=None, url=None)) for p in self.patterns]
    def scalars(self, statement):
        model = statement.column_descriptions[0]["entity"]
        return SimpleNamespace(all=lambda: [record for (record_model, _), record in self.records.items() if record_model == model])


class PatternTests(unittest.TestCase):
    def test_unique_patterns_preserve_scamshield_provenance(self):
        self.assertEqual(validate_catalog(PATTERNS), 1038)
        sourced = [p for p in PATTERNS if p.get("source_dataset")]
        self.assertEqual(len(sourced), 302)
        self.assertEqual({p["language"] for p in sourced}, {"Hindi", "Hinglish"})
        self.assertTrue(all(p["license"] == "MIT" and p["redacted"] and p["source_kind"] == "Synthetic_Tier_C" for p in sourced))
        self.assertTrue(all("[phone redacted]" in p["text"] or not any(len(word) >= 8 and word.isdecimal() for word in p["text"].split()) for p in sourced))
        app.dependency_overrides[get_db] = lambda: FakeDB()
        try:
            result = TestClient(app).post("/api/detect", json={"channel": "other", "text": sourced[0]["text"]}).json()
            self.assertEqual(result["previous_report_matches"][0]["status"], "synthetic_dataset")
            self.assertTrue(result["previous_report_matches"][0]["report_type"].startswith("ScamShield: "))
            self.assertTrue(any("synthetic" in reason for reason in result["reasons"]))
        finally:
            app.dependency_overrides.clear()
    def test_threshold_and_hierarchy_boundaries(self):
        for score, expected in ((1, "Exact"), (.999, "Very strong"), (.9, "Very strong"),
                                (.899, "Strong"), (.8, "Strong"), (.799, "Partial"),
                                (.712, "Partial"), (.711, "Below threshold")):
            with self.subTest(score=score):
                self.assertEqual(similarity_tier(score), expected)
        with patch("app.services.previous_report_matcher._similarity_score", return_value=.712):
            self.assertEqual(len(find_previous_report_matches(FakeDB(), text=PATTERNS[0]["text"], url=None, submission_id=None)), len(PATTERNS))
        with patch("app.services.previous_report_matcher._similarity_score", return_value=.711):
            self.assertEqual(find_previous_report_matches(FakeDB(), text=PATTERNS[0]["text"], url=None, submission_id=None), [])

    def test_all_patterns_ranked_but_only_threshold_hits_are_matches(self):
        app.dependency_overrides[get_db] = lambda: FakeDB()
        try:
            result = TestClient(app).post("/api/detect", json={"channel": "other", "text": PATTERNS[0]["text"]}).json()
            ranked = result["pattern_comparisons"]
            self.assertEqual(len(ranked), len(PATTERNS))
            self.assertEqual(result["comparison_count"], len(PATTERNS))
            self.assertEqual(ranked[0]["tier"], "Exact")
            self.assertEqual([p["rank"] for p in ranked], list(range(1, len(PATTERNS) + 1)))
            self.assertEqual([p["similarity_score"] for p in ranked], sorted((p["similarity_score"] for p in ranked), reverse=True))
            self.assertTrue(any(p["tier"] == "Below threshold" for p in ranked))
            self.assertTrue(all(p["similarity_score"] >= MATCH_THRESHOLD for p in result["previous_report_matches"]))
            self.assertTrue(all("text" not in p for p in ranked))
            short = TestClient(app).post("/api/detect", json={"channel": "other", "text": "hh"}).json()
            self.assertEqual(short["pattern_comparisons"], [])
        finally:
            app.dependency_overrides.clear()

    def test_all_demo_messages_and_normalized_variants_match(self):
        for p in PATTERNS:
            for text in (p["text"], p["text"].upper().replace(".", "!!!")):
                with self.subTest(pattern=p["title"]):
                    matches = find_previous_report_matches(FakeDB([p]), text=text, url=None, submission_id=None)
                    score, level, reasons = verdict(matches)
                    self.assertEqual(level, "HIGH")
                    self.assertEqual(score, 1)
                    self.assertTrue(any(m.report_id == "report_" + p["id"] for m in matches))
                    self.assertTrue(any("synthetic" in reason for reason in reasons))

    def test_representative_families_match_against_the_full_catalog(self):
        by_family = {p["title"]: p for p in PATTERNS}
        for p in by_family.values():
            matches = find_previous_report_matches(FakeDB(), text=p["text"], url=None, submission_id=None)
            self.assertEqual(matches[0].similarity_score, 1)
            self.assertTrue(any(m.submission_id == p["id"] for m in matches))

    def test_authored_variants_are_reproducible_and_not_relabeled_scamshield(self):
        from scripts.build_authored_scam_catalog import build, provenance
        authored = [p for p in PATTERNS if p.get("source_kind") == "TrustGraph_authored_synthetic"]
        self.assertEqual(authored, build())
        self.assertEqual(len(authored), 700)
        self.assertEqual(len({p["family"] for p in authored}), 25)
        self.assertTrue(all("source_dataset" not in p for p in authored))
        metadata = json.loads((Path(__file__).resolve().parents[1] / "data/authored_scam_provenance.json").read_text())
        self.assertEqual(metadata, provenance(authored))

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
        self.assertEqual(seed(db, PATTERNS), len(PATTERNS))
        self.assertEqual(seed(db, PATTERNS), 0)
        self.assertEqual(len(db.records), 2 * len(PATTERNS))
        original = db.get(SubmissionRecord, PATTERNS[0]["id"])
        original.text = "Existing user record"
        with self.assertRaises(ValueError):
            seed(db, PATTERNS)
        self.assertEqual(original.text, "Existing user record")

    def test_paraphrases_have_natural_nonidentical_scores(self):
        queries = json.loads((Path(__file__).resolve().parents[1] / "data/demo_judge_queries.json").read_text())
        scores = []
        for query in queries:
            matches = find_previous_report_matches(FakeDB(), text=query["text"], url=None, submission_id=None)
            score, level, _ = verdict(matches)
            self.assertEqual(level, "HIGH", query["title"])
            self.assertLess(score, 1, query["title"])
            scores.append(round(score * 100))
        self.assertGreater(len(set(scores)), 3)
        self.assertTrue(any(MATCH_THRESHOLD <= s.similarity_score < .80 for s in matches))

    def test_calibration_is_reproducible_and_rejects_similar_benign_warnings(self):
        result = calibrate()
        self.assertEqual(result["threshold"], MATCH_THRESHOLD)
        self.assertEqual(result["true_positives"], 13)
        self.assertEqual(result["false_positives"], 0)
        controls = json.loads((Path(__file__).resolve().parents[1] / "data/demo_benign_controls.json").read_text())
        for text in controls:
            self.assertEqual(find_previous_report_matches(FakeDB(), text=text, url=None, submission_id=None), [])

    def test_extension_adapter_and_unknown_fallback(self):
        app.dependency_overrides[get_db] = lambda: FakeDB()
        try:
            client = TestClient(app)
            response = client.post("/api/score", json={"message_text": PATTERNS[0]["text"]})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["band"], "High")
            self.assertIsInstance(response.json()["signals"], list)
            self.assertEqual(client.post("/api/score", json={"message_text": "hello"}).status_code, 503)
        finally:
            app.dependency_overrides.clear()

    def test_endpoint_returns_pattern_evidence_without_calling_ai(self):
        db = FakeDB()
        app.dependency_overrides[get_db] = lambda: db
        try:
            with patch("app.api.detect.scam_analyze", side_effect=AssertionError("AI must not be called")):
                response = TestClient(app).post("/api/detect", json={"channel": "other", "text": PATTERNS[0]["text"]})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["risk_level"], "HIGH")
            self.assertEqual(response.json()["previous_report_matches"][0]["status"], "synthetic_demo")
            self.assertEqual(db.commits, 0)
        finally:
            app.dependency_overrides.clear()
