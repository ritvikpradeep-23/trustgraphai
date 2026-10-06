"""Read-only checks against the running API; examples are not an accuracy benchmark."""
import json
import sys
from pathlib import Path
import httpx

patterns = json.loads((Path(__file__).resolve().parents[1] / "data/demo_scam_patterns.json").read_text())
base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"
with httpx.Client(base_url=base, timeout=30, trust_env=False) as client:
    for p in patterns:
        response = client.post("/api/detect", json={"channel": "other", "text": p["text"]})
        response.raise_for_status()
        result = response.json()
        assert result["method"] == "database-pattern-matching"
        assert result["risk_level"] == "HIGH"
        assert any(m["report_id"] == "report_" + p["id"] for m in result["previous_report_matches"])
    for text in ("hh", "Lunch at the canteen at one? Please bring your exam notes.",
                 "Never share your OTP or UPI PIN with anyone. Contact your bank using its official number."):
        response = client.post("/api/detect", json={"channel": "other", "text": text})
        response.raise_for_status()
        assert response.json()["risk_level"] == "UNKNOWN"
        assert response.json()["risk_score"] is None
print(f"{len(patterns)}/{len(patterns)} authored demo examples matched through the API; 3 benign controls had no match. Not a real-world accuracy benchmark.")
