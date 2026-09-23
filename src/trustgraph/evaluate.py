"""Calibrate the risk bands on held-out normal traffic, then report
false-positive rate on a separate held-out set and detection on the named
scam scenarios and the random anomalies. Re-run whenever a real signal
replaces a stub: the fused score distribution changes, so the cut points must too."""
import json

import numpy as np
import pandas as pd

from trustgraph.anomaly.features import RAW_FEATURES
from trustgraph.fusion import BANDS_PATH, risk_band
from trustgraph.pipeline import score_interaction

# Caution is a soft warning, so it gets the looser budget: 10% of this
# calibration set came out at ~4.5% of independently generated legit traffic
# while lifting fraud caught from ~98.5% to ~99%. High stays strict.
CAUTION_FPR = 0.10
HIGH_FPR = 0.01


def _interactions(df: pd.DataFrame) -> list[dict]:
    return df[RAW_FEATURES].to_dict(orient="records")


def _fused_scores(df: pd.DataFrame) -> np.ndarray:
    return np.array([score_interaction(i)[1].score for i in _interactions(df)])


def main():
    calibration = pd.read_csv("data/anomaly/normal_calibration.csv")
    test = pd.read_csv("data/anomaly/normal_test.csv")
    scenarios = pd.read_csv("data/anomaly/scenarios.csv")
    anomalous = pd.read_csv("data/anomaly/anomalous.csv")

    calib_scores = _fused_scores(calibration)
    bands = {
        "caution": float(np.quantile(calib_scores, 1 - CAUTION_FPR)),
        "high": float(np.quantile(calib_scores, 1 - HIGH_FPR)),
    }
    with open(BANDS_PATH, "w") as f:
        json.dump(bands, f, indent=2)
    print(f"Calibrated on {len(calibration)} held-out normal rows -> {BANDS_PATH}")
    print(f"  Caution >= {bands['caution']:.3f}   High >= {bands['high']:.3f}")

    test_scores = _fused_scores(test)
    print()
    print(f"False-positive rate on {len(test)} separate held-out normal rows:")
    print(f"  Caution or above: {np.mean(test_scores >= bands['caution']):.1%}")
    print(f"  High:             {np.mean(test_scores >= bands['high']):.1%}")

    print()
    print("Named scam scenarios:")
    scenario_bands = []
    for name, interaction in zip(scenarios["scenario"], _interactions(scenarios)):
        signals, fused = score_interaction(interaction)
        anomaly = next(s for s in signals if s.signal_name == "anomaly")
        band = risk_band(fused.score, bands)
        scenario_bands.append(band)
        print(f"  {name:<24s} {fused.score:.2f}  {band:<7s}  {anomaly.explanation}")
    flagged = sum(b != "Low" for b in scenario_bands)
    high = sum(b == "High" for b in scenario_bands)
    print(f"  -> {flagged}/{len(scenarios)} at Caution or above, {high}/{len(scenarios)} High")

    anomalous_scores = _fused_scores(anomalous)
    print()
    print(f"Random single/double-feature anomalies ({len(anomalous)} rows):")
    print(f"  Caution or above: {np.sum(anomalous_scores >= bands['caution'])}/{len(anomalous)}")
    print(f"  High:             {np.sum(anomalous_scores >= bands['high'])}/{len(anomalous)}")


if __name__ == "__main__":
    main()
