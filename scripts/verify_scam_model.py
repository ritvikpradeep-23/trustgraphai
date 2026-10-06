"""Offline self-test of the committed scam model; no database or provider calls.

The eight fixtures are integration/demo cases, not an accuracy benchmark. Extra
challenge cases deliberately report misses without adjusting model thresholds.
Run: python scripts/verify_scam_model.py [--json]
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.ai.scam_engine import analyze, engine

CHALLENGES = [
    {"title": "Short lottery fee (known limitation)", "kind": "scam",
     "text": "Congratulations! You won a lottery prize. Pay a registration fee to claim it."},
    {"title": "Unfamiliar investment pitch", "kind": "scam",
     "text": "Our private trading circle guarantees your stake will triple by Friday. Wire the joining contribution to me to reserve your place."},
    {"title": "Security warning with risky vocabulary", "kind": "benign",
     "text": "Our IT team warns against remote access requests. Never give callers your password or verification code."},
    {"title": "Ordinary payment reminder", "kind": "benign",
     "text": "Your library membership renewal is due next month. Please use the official library website or pay at the service desk."},
]


def verify():
    assert engine() is not None, "Original scam engine could not load"
    from sklearn.ensemble import IsolationForest
    from trustgraph.anomaly.detector import _load_bundle
    bundle = _load_bundle()
    assert isinstance(bundle["model"], IsolationForest), "Wrong model artifact"
    assert len(bundle["model"].estimators_) > 0, "Isolation Forest has no fitted trees"
    queries = json.loads((ROOT / "data/demo_scam_model_queries.json").read_text(encoding="utf-8"))
    results = []
    for index, query in enumerate([*queries, *CHALLENGES]):
        answer = analyze(query["text"])
        assert answer is not None, f"Inference unavailable: {query['title']}"
        assert set(answer["signals"]) == {"anomaly", "continuity", "similarity", "precedent"}
        kind = query.get("kind", "scam" if index < 6 else "benign")
        flagged = answer["level"] in {"CAUTION", "HIGH"}
        agrees = flagged == (kind == "scam")
        if index < len(queries):
            assert agrees, f"Demo regression: {query['title']}"
        results.append({"title": query["title"], "text": query["text"], "intended_label": kind,
            "review_score": round(answer["score"] * 100, 2), "risk_level": answer["level"],
            "signals": answer["signals"], "agrees_with_label": agrees,
            "fixture": "demo" if index < len(queries) else "challenge"})
    assert len({row["review_score"] for row in results[:len(queries)]}) > 1
    return {"model": "original-scam-engine", "learned_component": "IsolationForest",
        "demo_checks_passed": len(queries), "challenge_cases": len(CHALLENGES),
        "note": "Synthetic functional examples, not an independent accuracy benchmark. Review scores are not fraud probabilities. Challenges expose limitations; thresholds are unchanged.",
        "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = verify()
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"Original trained Isolation Forest verified: {report['demo_checks_passed']} demo checks passed.")
            for row in report["results"]:
                note = "" if row["agrees_with_label"] else " [LIMITATION: label mismatch]"
                print(f"{row['title']}: {row['review_score']:.2f}/100 {row['risk_level']}{note}")
            print(report["note"])
    except Exception as error:
        print(f"Scam model verification failed ({type(error).__name__}); install backend/requirements.txt and check the baseline artifacts.", file=sys.stderr)
        sys.exit(1)
