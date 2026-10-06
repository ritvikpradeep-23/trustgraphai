import unittest

from fastapi.testclient import TestClient

from app.main import app


class URLAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_parses_and_normalizes_url_with_deterministic_signals(self):
        response = self.client.post(
            "/api/url/analyze",
            json={"url": "HTTP://user:pass@a.b.c.d.example.co.uk:8080/login?next=%2F"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["scheme"], "http")
        self.assertEqual(payload["hostname"], "a.b.c.d.example.co.uk")
        self.assertEqual(payload["registrable_domain"], "example.co.uk")
        self.assertEqual(payload["port"], 8080)
        self.assertEqual(payload["path"], "/login")
        self.assertEqual(payload["query"], "next=%2F")
        self.assertTrue(payload["signals"]["http"])
        self.assertTrue(payload["signals"]["unusual_port"])
        self.assertTrue(payload["signals"]["excessive_subdomains"])
        self.assertTrue(payload["signals"]["suspicious_encoding_or_pattern"])
        self.assertTrue(payload["signals"]["embedded_userinfo"])
        self.assertNotIn("user", payload["normalized_url"])

    def test_accepts_bare_domain_and_detects_ip_hostname(self):
        response = self.client.post("/api/url/analyze", json={"url": "127.0.0.1/path"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["normalized_url"], "https://127.0.0.1/path")
        self.assertTrue(response.json()["signals"]["ip_hostname"])

    def test_rejects_unsupported_and_malformed_urls(self):
        for value in ("javascript:alert(1)", "https:///missing-host", "http://example.com:bad"):
            with self.subTest(value=value):
                response = self.client.post("/api/url/analyze", json={"url": value})
                self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
