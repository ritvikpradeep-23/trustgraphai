"""Calibrate the risk bands on held-out legit traffic, then report
false-positive rate on a separate held-out set and detection on the named
scenarios and the random anomalies. Re-run whenever a real signal replaces a
stub: the fused score distribution changes, so the cut points must too."""
import json

import numpy as np
import pandas as pd

from trustgraph.anomaly.features import RAW_FEATURES
from trustgraph.fusion import BANDS_PATH, risk_band
from trustgraph.pipeline import score_interaction
from trustgraph.scenarios import SCENARIOS

# Caution is a soft warning, so it gets the looser budget: 10% of this
# calibration set came out at ~4.5% of independently generated legit traffic
# while lifting fraud caught from ~98.5% to ~99%. High stays strict.
CAUTION_FPR = 0.10
HIGH_FPR = 0.01


def _legit(split: str) -> list[dict]:
    """Legit call features paired row-for-row with legit identity histories
    and message text, each drawn independently."""
    features = pd.read_csv(f"data/anomaly/normal_{split}.csv")[RAW_FEATURES].to_dict(orient="records")
    with open(f"data/continuity/legit_{split}.json") as f:
        identities = json.load(f)
    with open(f"data/similarity/legit_{split}.json") as f:
        texts = json.load(f)
    return [{**feat, **ident, "message_text": text}
            for feat, ident, text in zip(features, identities, texts, strict=True)]


def _fused_scores(interactions: list[dict]) -> np.ndarray:
    return np.array([score_interaction(i)[1].score for i in interactions])


def main():
    calibration = _legit("calibration")
    test = _legit("test")
    anomalous = pd.read_csv("data/anomaly/anomalous.csv")[RAW_FEATURES].to_dict(orient="records")

    calib_scores = _fused_scores(calibration)
    bands = {
        "caution": float(np.quantile(calib_scores, 1 - CAUTION_FPR)),
        "high": float(np.quantile(calib_scores, 1 - HIGH_FPR)),
    }
    with open(BANDS_PATH, "w") as f:
        json.dump(bands, f, indent=2)
    print(f"Calibrated on {len(calibration)} held-out legit interactions -> {BANDS_PATH}")
    print(f"  Caution >= {bands['caution']:.3f}   High >= {bands['high']:.3f}")

    test_scores = _fused_scores(test)
    print()
    print(f"False-positive rate on {len(test)} separate held-out legit interactions:")
    print(f"  Caution or above: {np.mean(test_scores >= bands['caution']):.1%}")
    print(f"  High:             {np.mean(test_scores >= bands['high']):.1%}")

    print()
    print("Named scenarios (anomaly / continuity / similarity / precedent -> fused):")
    results = {"scam": [], "legit": []}
    for name, kind, interaction in SCENARIOS:
        signals, fused = score_interaction(interaction)
        by_name = {s.signal_name: s for s in signals}
        band = risk_band(fused.score, bands)
        results[kind].append(band)
        ok = (band != "Low") == (kind == "scam")
        print(f"  {'ok ' if ok else 'MISS'} [{kind:<5s}] {name:<37s} "
              f"{by_name['anomaly'].score:.2f} / {by_name['continuity'].score:.2f} / {by_name['similarity'].score:.2f} / {by_name['precedent'].score:.2f}"
              f" -> {fused.score:.2f} {band:<7s}")
        print(f"         {fused.explanation}")
    scams, legit = results["scam"], results["legit"]
    print(f"  -> scams: {sum(b != 'Low' for b in scams)}/{len(scams)} at Caution or above, "
          f"{sum(b == 'High' for b in scams)}/{len(scams)} High; "
          f"legit controls kept Low: {sum(b == 'Low' for b in legit)}/{len(legit)}")

    anomalous_scores = _fused_scores(anomalous)
    print()
    print(f"Random single/double-feature anomalies ({len(anomalous)} rows):")
    print(f"  Caution or above: {np.sum(anomalous_scores >= bands['caution'])}/{len(anomalous)}")
    print(f"  High:             {np.sum(anomalous_scores >= bands['high'])}/{len(anomalous)}")


if __name__ == "__main__":
    main()
