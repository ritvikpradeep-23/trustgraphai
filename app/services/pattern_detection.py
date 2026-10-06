"""Deterministic report matching, not AI or a calibrated fraud probability."""
from app.services.previous_report_matcher import MATCH_THRESHOLD


def verdict(matches):
    if not matches:
        return None, "UNKNOWN", [
            "No stored scam pattern met the similarity threshold.",
            "No match does not prove a message is safe. New scams and paraphrases can be missed.",
        ]
    similarity = max(match.similarity_score for match in matches)
    demo = any(match.status == "synthetic_demo" for match in matches)
    return similarity, "HIGH", [
        f"Matched {len(matches)} stored scam pattern(s); best text similarity {similarity:.0%} (threshold {MATCH_THRESHOLD:.0%}).",
        "Deterministic word overlap and sequence matching; the score is similarity, not a fraud probability.",
        *(["Matched examples include synthetic judge-demo patterns, not verified real-world reports."] if demo else []),
    ]
