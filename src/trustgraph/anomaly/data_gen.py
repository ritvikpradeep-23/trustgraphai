"""Stage 2: synthetic data generator for the anomaly detector's 6 features.

Columns:
    duration_sec       call/interaction length, in seconds
    hour_of_day         0-23
    amount_ratio        requested amount / that contact's typical amount
    contact_freq_24h    how many times this contact reached out today
    urgency_score        count of urgency keywords in the content text
    new_channel_flag    0 or 1 - has this device/channel been seen before
"""
import numpy as np
import pandas as pd

from trustgraph.anomaly.features import RAW_FEATURES as FEATURES

# Business-hours weighting for hour_of_day: 9-18 gets most of the mass,
# the rest of the day gets a thin tail so "normal" isn't ONLY 9-to-5.
_HOUR_WEIGHTS = np.array(
    [0.5, 0.3, 0.2, 0.2, 0.3, 0.5, 1.0, 2.0,
     4.0, 6.0, 7.0, 7.0, 6.0, 7.0, 7.0, 6.0,
     6.0, 5.0, 3.0, 1.5, 1.0, 0.8, 0.6, 0.5]
)
_HOUR_WEIGHTS = _HOUR_WEIGHTS / _HOUR_WEIGHTS.sum()


def generate_normal_rows(n: int = 300, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    duration_sec = rng.uniform(20, 180, size=n)
    hour_of_day = rng.choice(np.arange(24), size=n, p=_HOUR_WEIGHTS)
    amount_ratio = np.clip(rng.normal(1.0, 0.15, size=n), 0.1, None)
    contact_freq_24h = rng.poisson(0.8, size=n)
    contact_freq_24h = np.clip(contact_freq_24h, 0, 2)
    urgency_score = rng.poisson(0.4, size=n)
    urgency_score = np.clip(urgency_score, 0, 1)
    new_channel_flag = rng.choice([0, 1], size=n, p=[0.95, 0.05])

    return pd.DataFrame({
        "duration_sec": duration_sec,
        "hour_of_day": hour_of_day,
        "amount_ratio": amount_ratio,
        "contact_freq_24h": contact_freq_24h,
        "urgency_score": urgency_score,
        "new_channel_flag": new_channel_flag,
    })


def generate_anomalous_rows(n: int = 15, seed: int = 1) -> pd.DataFrame:
    """Each row has 1-2 features pushed to an extreme; the rest stay
    within normal ranges, so a real detector actually has to work for it."""
    rng = np.random.default_rng(seed)

    # Draw a normal-looking baseline for every row, then override 1-2
    # features per row with an extreme value.
    base = generate_normal_rows(n=n, seed=seed + 1000)

    extreme_generators = {
        "duration_sec": lambda: rng.choice([rng.uniform(0, 5), rng.uniform(600, 1800)]),
        "hour_of_day": lambda: int(rng.choice([1, 2, 3, 4])),
        "amount_ratio": lambda: rng.uniform(4.0, 10.0),
        "contact_freq_24h": lambda: int(rng.integers(15, 30)),
        "urgency_score": lambda: int(rng.integers(5, 9)),
        "new_channel_flag": lambda: 1,
    }

    pushed_features = []
    for i in range(n):
        num_extreme = rng.choice([1, 2], p=[0.6, 0.4])
        chosen = rng.choice(FEATURES, size=num_extreme, replace=False)
        for feat in chosen:
            base.loc[i, feat] = extreme_generators[feat]()
        pushed_features.append("+".join(sorted(chosen)))

    base["pushed_features"] = pushed_features
    return base


# Hand-written scam patterns, independent of the random anomaly generator, so
# detection on these isn't guaranteed by construction. NaN = feature unknown.
# subtle_invoice_bump is deliberately mild: it's expected to be missed and
# shows where this signal needs help from the others.
SCENARIOS = [
    {"scenario": "grandparent_emergency", "duration_sec": 150, "hour_of_day": 2,
     "amount_ratio": 6.0, "contact_freq_24h": 3, "urgency_score": 5, "new_channel_flag": 1},
    {"scenario": "ceo_wire_fraud", "duration_sec": 60, "hour_of_day": 11,
     "amount_ratio": 9.0, "contact_freq_24h": 2, "urgency_score": 4, "new_channel_flag": 0},
    {"scenario": "sim_swap_takeover", "duration_sec": 45, "hour_of_day": 14,
     "amount_ratio": 3.5, "contact_freq_24h": 1, "urgency_score": 1, "new_channel_flag": 1},
    {"scenario": "harassment_burst", "duration_sec": 15, "hour_of_day": 22,
     "amount_ratio": 1.0, "contact_freq_24h": 20, "urgency_score": 2, "new_channel_flag": 0},
    {"scenario": "romance_scam_escalation", "duration_sec": 900, "hour_of_day": 23,
     "amount_ratio": 4.0, "contact_freq_24h": 4, "urgency_score": 1, "new_channel_flag": 0},
    {"scenario": "tech_support_popup", "duration_sec": 1200, "hour_of_day": 16,
     "amount_ratio": 2.5, "contact_freq_24h": 1, "urgency_score": 3, "new_channel_flag": 1},
    {"scenario": "one_ring_callback_bait", "duration_sec": 1, "hour_of_day": 3,
     "amount_ratio": np.nan, "contact_freq_24h": 5, "urgency_score": 0, "new_channel_flag": 1},
    {"scenario": "subtle_invoice_bump", "duration_sec": 90, "hour_of_day": 10,
     "amount_ratio": 1.6, "contact_freq_24h": 1, "urgency_score": 1, "new_channel_flag": 0},
]


def main():
    outputs = {
        "normal": generate_normal_rows(300, seed=0),
        # Never trained on. Calibration sets the risk-band cut points; test
        # reports the false-positive rate at those cut points.
        "normal_calibration": generate_normal_rows(1000, seed=2),
        "normal_test": generate_normal_rows(1000, seed=3),
        "anomalous": generate_anomalous_rows(15, seed=1),
        "scenarios": pd.DataFrame(SCENARIOS),
    }
    for name, df in outputs.items():
        path = f"data/anomaly/{name}.csv"
        df.to_csv(path, index=False)
        print(f"Wrote {len(df)} rows -> {path}")

    print()
    print(outputs["normal"].describe().to_string())
    print()
    print(outputs["anomalous"].to_string(index=False))
    print()
    print(outputs["scenarios"].to_string(index=False))


if __name__ == "__main__":
    main()
