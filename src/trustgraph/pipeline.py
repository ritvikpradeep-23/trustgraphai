"""Run interactions through all 4 signals and fusion end to end."""
import pandas as pd

from trustgraph.anomaly.detector import anomaly_score
from trustgraph.anomaly.features import RAW_FEATURES
from trustgraph.fusion import fuse, risk_band
from trustgraph.stubs import continuity_score, precedent_score, similarity_score

SIGNAL_FUNCS = [continuity_score, similarity_score, precedent_score, anomaly_score]


def score_interaction(interaction: dict):
    signals = [fn(interaction) for fn in SIGNAL_FUNCS]
    return signals, fuse(signals)


def main():
    sample_interaction = {
        "duration_sec": 30, "hour_of_day": 3, "amount_ratio": 8.5,
        "contact_freq_24h": 25, "urgency_score": 7, "new_channel_flag": 1,
    }
    print("=== Single interaction through all 4 signals + fusion ===")
    signals, fused = score_interaction(sample_interaction)
    for s in signals:
        print(f"  {s.signal_name:12s} score={s.score:.2f}  {s.explanation}")
    print(f"  {fused.signal_name:12s} score={fused.score:.2f}  [{risk_band(fused.score)}]  {fused.explanation}")

    print()
    print("=== Stage 2 anomalous rows end to end (all 4 signals + fusion) ===")
    anomalous = pd.read_csv("data/anomaly/anomalous.csv")
    for i, row in anomalous.iterrows():
        _, fused = score_interaction(row[RAW_FEATURES].to_dict())
        print(f"  row {i:2d} pushed={row['pushed_features']:<30s} "
              f"{fused.score:.2f} [{risk_band(fused.score):<7s}] {fused.explanation}")


if __name__ == "__main__":
    main()
