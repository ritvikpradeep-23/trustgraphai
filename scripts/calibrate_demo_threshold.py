"""Read-only synthetic calibration. Not a real-world validation benchmark."""
import json
from pathlib import Path
import sys

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "backend"), str(Path(__file__).resolve().parents[1])]
from app.services.previous_report_matcher import _normalize_content, _similarity_score
from scripts.scam_catalog import load_catalog

root = Path(__file__).resolve().parents[1]
patterns = load_catalog()
queries = json.loads((root / "data/demo_judge_queries.json").read_text())
benign = json.loads((root / "data/demo_benign_controls.json").read_text())

def best_score(text):
    return max(_similarity_score(_normalize_content(text), _normalize_content(p["text"])) or 0 for p in patterns)

def calibrate():
    positives = [best_score(q["text"]) for q in queries]
    negatives = [best_score(text) for text in benign]
    values = sorted(set([0., 1., *positives, *negatives]))
    candidates = [(a + b) / 2 for a, b in zip(values, values[1:])]
    def metrics(threshold):
        tp = sum(s >= threshold for s in positives)
        fp = sum(s >= threshold for s in negatives)
        # Equal class weights; ties prefer fewer false alarms, then higher cutoff.
        balanced = (tp / len(positives) + 1 - fp / len(negatives)) / 2
        return balanced, -fp, threshold
    threshold = max(candidates, key=metrics)
    return {
        "threshold": round(threshold, 4),
        "positive_queries": len(positives), "benign_controls": len(negatives),
        "true_positives": sum(s >= threshold for s in positives),
        "false_positives": sum(s >= threshold for s in negatives),
        "balanced_accuracy": round(metrics(threshold)[0], 4),
        "positive_scores": positives, "benign_scores": negatives,
        "selection": "Maximize balanced accuracy on synthetic unseeded calibration queries and benign controls; ties prefer fewer false positives. Not independent validation."
    }

if __name__ == "__main__":
    print(json.dumps(calibrate(), indent=2))
