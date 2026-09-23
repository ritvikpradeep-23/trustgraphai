"""Stage 3: train an IsolationForest on normal rows only and validate it
against the planted anomalous rows."""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from trustgraph.anomaly.data_gen import FEATURES


def load_data():
    normal = pd.read_csv("data/anomaly/normal.csv")
    anomalous = pd.read_csv("data/anomaly/anomalous.csv")
    return normal, anomalous


def train(normal: pd.DataFrame) -> IsolationForest:
    model = IsolationForest(contamination=0.05, random_state=0)
    model.fit(normal[FEATURES])
    return model


def main():
    normal, anomalous = load_data()
    model = train(normal)

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
