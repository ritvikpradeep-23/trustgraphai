"""Read-only checks against the running API; examples are not an accuracy benchmark."""
import json
import sys
from pathlib import Path
import httpx

patterns = json.loads((Path(__file__).resolve().parents[1] / "data/demo_scam_patterns.json").read_text())
queries = json.loads((Path(__file__).resolve().parents[1] / "data/demo_judge_queries.json").read_text())
base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"
with httpx.Client(base_url=base, timeout=30, trust_env=False) as client:
    for p in patterns:
        response = client.post("/api/detect", json={"channel": "other", "text": p["text"]})
        response.raise_for_status()
        result = response.json()
        assert result["method"] == "database-pattern-matching"
        assert result["risk_level"] == "HIGH"
        assert any(m["report_id"] == "report_" + p["id"] for m in result["previous_report_matches"])
    scores = []
    for query in queries:
        response = client.post("/api/detect", json={"channel": "other", "text": query["text"]})
        response.raise_for_status()
        result = response.json()
        assert result["risk_level"] == "HIGH"
        assert .72 <= result["risk_score"] < 1
        score = round(result["risk_score"] * 100)
        scores.append(score)
        print(f"{query['title']}: {score}% text similarity")
    assert len(set(scores)) > 3
    response = client.post("/api/score", json={"message_text": queries[0]["text"], "channel": "other"})
    response.raise_for_status()
    assert response.json()["band"] == "High"
    for text in ("hh", "Lunch at the canteen at one? Please bring your exam notes.",
                 "Never share your OTP or UPI PIN with anyone. Contact your bank using its official number."):
        response = client.post("/api/detect", json={"channel": "other", "text": text})
        response.raise_for_status()
        assert response.json()["risk_level"] == "UNKNOWN"
        assert response.json()["risk_score"] is None
print(f"{len(patterns)}/{len(patterns)} authored demo examples matched through the API; 3 benign controls had no match. Not a real-world accuracy benchmark.")
print(f"{len(queries)} unseeded paraphrases matched with scores from {min(scores)}% to {max(scores)}%; extension adapter passed.")
