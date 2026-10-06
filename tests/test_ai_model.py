import unittest

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

        self.assertIsNone(RecordingAI().predict("web_app", None, "sample", None).risk_score)
        self.assertEqual(calls[0][0], "scam")
        self.assertEqual(calls[0][1]["channel"], "web_app")

if __name__ == "__main__":
    unittest.main()
