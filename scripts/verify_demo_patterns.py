"""Read-only checks against the running API; examples are not an accuracy benchmark."""
import json
import sys
from pathlib import Path
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.scam_catalog import load_catalog, validate_catalog
patterns = load_catalog()
validate_catalog(patterns)
queries = json.loads((Path(__file__).resolve().parents[1] / "data/demo_judge_queries.json").read_text())
controls = json.loads((Path(__file__).resolve().parents[1] / "data/demo_benign_controls.json").read_text())
base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"
with httpx.Client(base_url=base, timeout=30, trust_env=False) as client:
    for index, p in enumerate(patterns, 1):
        response = client.post("/api/detect", json={"channel": "other", "text": p["text"]})
        response.raise_for_status()
        result = response.json()
        assert result["method"] == "database-pattern-matching"
        assert result["decision_source"] == "records" and not result["model_used"]
        assert result["risk_level"] == "HIGH"
        assert any(m["report_id"] == "report_" + p["id"] for m in result["previous_report_matches"])
        assert result["comparison_count"] >= len(patterns)
        ranked = result["pattern_comparisons"]
        assert ranked[0]["report_id"] == "report_" + p["id"]
        assert [m["similarity_score"] for m in ranked] == sorted((m["similarity_score"] for m in ranked), reverse=True)
        assert [m["rank"] for m in ranked] == list(range(1, len(ranked) + 1))
        if index % 50 == 0:
            print(f"Exact-copy API checks: {index}/{len(patterns)} passed", flush=True)
    scores = []
    for query in queries:
        response = client.post("/api/detect", json={"channel": "other", "text": query["text"]})
        response.raise_for_status()
        result = response.json()
        assert result["risk_level"] == "HIGH"
        similarity = result["pattern_comparisons"][0]["similarity_score"]
        assert result["match_threshold"] <= similarity < 1
        score = round(similarity * 100)
        scores.append(score)
        print(f"{query['title']}: {similarity:.1%} text similarity; {result['pattern_comparisons'][0]['tier']}; closest: {result['pattern_comparisons'][0]['report_type']}")
    assert len(set(scores)) > 3
    response = client.post("/api/score", json={"message_text": queries[0]["text"], "channel": "other"})
    response.raise_for_status()
    assert response.json()["band"] == "High"
    for text in ["hh", *controls]:
        response = client.post("/api/detect", json={"channel": "other", "text": text})
        response.raise_for_status()
        result = response.json()
        assert not result["previous_report_matches"]
        if result.get("model_available"):
            assert 0 <= result["risk_score"] <= 1
        else:
            assert result["risk_level"] == "UNKNOWN" and result["risk_score"] is None
print(f"{len(patterns)}/{len(patterns)} synthetic catalog examples matched through the API; {len(controls)} benign controls and short input had no match. Not a real-world accuracy benchmark.")
print(f"{len(queries)} unseeded paraphrases matched with scores from {min(scores)}% to {max(scores)}%; extension adapter passed.")
