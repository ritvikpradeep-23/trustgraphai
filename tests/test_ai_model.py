import unittest
from unittest.mock import patch

from app.services.ai_model import TrustGraphAI


class TrustGraphAITests(unittest.TestCase):
    def test_unavailable_results_never_fabricate_scores(self):
        for capability in ("scam", "ai_content", "image", "audio", "video", "multimodal"):
            with self.subTest(capability=capability):
                result = TrustGraphAI().analyze(capability, {})
                self.assertFalse(result.available)
                self.assertIsNone(result.risk_score)
                self.assertIsNone(result.anomaly)
                self.assertEqual(result.risk_level, "PENDING")
                self.assertIn("no score was produced", result.reasons[0])

    def test_legacy_predict_uses_central_interface(self):
        calls = []
        class RecordingAI(TrustGraphAI):
            def analyze(self, capability, payload):
                calls.append((capability, payload))
                return super().analyze(capability, payload)

        with patch("app.ai.scam_engine.analyze", return_value=None):
            self.assertIsNone(RecordingAI().predict("web_app", None, "sample", None).risk_score)
        self.assertEqual(calls[0][0], "scam")
        self.assertEqual(calls[0][1]["channel"], "web_app")

    def test_legacy_scam_adapter_returns_existing_model_not_pending(self):
        answer = {"score": .834, "level": "CAUTION", "signals": {
            "anomaly": .12, "continuity": 0, "similarity": .7, "precedent": 0}, "reasons": ["Model result"]}
        with patch("app.ai.scam_engine.analyze", return_value=answer) as model:
            result = TrustGraphAI().predict("other", None, "A message", None)
        model.assert_called_once_with("A message", None, None)
        self.assertTrue(result.available)
        self.assertEqual(result.model, "original-scam-engine")
        self.assertEqual(result.risk_score, .834)
        self.assertEqual(result.anomaly, .12)

    def test_missing_or_invalid_message_does_not_call_model(self):
        with patch("app.ai.scam_engine.analyze") as model:
            for text in [None, " ", "x" * 20001]:
                self.assertFalse(TrustGraphAI().analyze("scam", {"text": text}).available)
        model.assert_not_called()

if __name__ == "__main__":
    unittest.main()
