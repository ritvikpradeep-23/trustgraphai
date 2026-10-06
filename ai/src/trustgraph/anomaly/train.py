"""Train the IsolationForest on normal rows only and save everything
anomaly_score() needs at inference time. Validation lives in evaluate.py."""
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from trustgraph.anomaly.features import RAW_FEATURES, circular_hour_distance, to_model_frame

MODEL_PATH = "models/anomaly_isolation_forest.joblib"


def train(normal: pd.DataFrame) -> IsolationForest:
    model = IsolationForest(contamination=0.05, random_state=0)
    model.fit(to_model_frame(normal))
    return model


def save_model(model: IsolationForest, normal: pd.DataFrame, path: str = MODEL_PATH):
    decision = model.decision_function(to_model_frame(normal))

    angle = 2 * np.pi * normal["hour_of_day"] / 24
    hour_center = float(np.arctan2(np.sin(angle).mean(), np.cos(angle).mean()) * 24 / (2 * np.pi)) % 24
    hour_dist = circular_hour_distance(normal["hour_of_day"], hour_center)

    bundle = {
        "model": model,
        "sigma": float(np.std(decision)),
        "feature_median": normal[RAW_FEATURES].median().to_dict(),
        "feature_mean": normal[RAW_FEATURES].mean().to_dict(),
        "feature_std": normal[RAW_FEATURES].std().replace(0, 1.0).to_dict(),
        # z for hour is circular distance from the typical hour, over its RMS.
        "hour_center": hour_center,
        "hour_rms": float(np.sqrt(np.mean(hour_dist ** 2))),
    }
    joblib.dump(bundle, path)
    return bundle


def main():
    normal = pd.read_csv("data/anomaly/normal.csv")
    bundle = save_model(train(normal), normal)
    print(f"Saved trained model -> {MODEL_PATH}")
    print(f"  typical hour {bundle['hour_center']:.1f}, hour RMS distance {bundle['hour_rms']:.2f}h")


if __name__ == "__main__":
    main()
