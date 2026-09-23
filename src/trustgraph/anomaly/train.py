"""Stage 3: train an IsolationForest on normal rows only and validate it
against the planted anomalous rows."""
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from trustgraph.anomaly.data_gen import FEATURES

MODEL_PATH = "models/anomaly_isolation_forest.joblib"


def load_data():
    normal = pd.read_csv("data/anomaly/normal.csv")
    anomalous = pd.read_csv("data/anomaly/anomalous.csv")
    return normal, anomalous


def train(normal: pd.DataFrame) -> IsolationForest:
    model = IsolationForest(contamination=0.05, random_state=0)
    model.fit(normal[FEATURES])
    return model


def save_model(model: IsolationForest, normal: pd.DataFrame, path: str = MODEL_PATH):
    """Bundle the model with everything anomaly_score() needs to turn a raw
    decision_function value into a 0-1 score and a per-feature explanation,
    without having to reload the training CSV at inference time."""
    decision = model.decision_function(normal[FEATURES])
    sigma = float(np.std(decision))

    bundle = {
        "model": model,
        "features": FEATURES,
        "sigma": sigma,
        "feature_mean": normal[FEATURES].mean().to_dict(),
        "feature_std": normal[FEATURES].std().replace(0, 1.0).to_dict(),
    }
    joblib.dump(bundle, path)
    return bundle


def main():
    normal, anomalous = load_data()
    model = train(normal)
    save_model(model, normal)
    print(f"Saved trained model -> {MODEL_PATH}")
    print()

    # Higher score == more anomalous.
    normal_scores = -model.score_samples(normal[FEATURES])
    anomalous_scores = -model.score_samples(anomalous[FEATURES])

    threshold = np.percentile(normal_scores, 90)

    report = anomalous.copy()
    report["anomaly_score"] = anomalous_scores
    report["flagged"] = anomalous_scores > threshold

    cols = ["pushed_features", "anomaly_score", "flagged"]
    print(f"90th-percentile normal-set score (threshold): {threshold:.4f}")
    print()
    print(report[cols].to_string())

    flagged_count = report["flagged"].sum()
    total = len(report)
    print()
    print(f"Flagged {flagged_count}/{total} anomalous rows "
          f"({flagged_count / total:.0%}).")


if __name__ == "__main__":
    main()
