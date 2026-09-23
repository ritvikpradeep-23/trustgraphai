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

FEATURES = [
    "duration_sec",
    "hour_of_day",
    "amount_ratio",
    "contact_freq_24h",
    "urgency_score",
    "new_channel_flag",
]

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


def main():
    normal = generate_normal_rows(300, seed=0)
    anomalous = generate_anomalous_rows(15, seed=1)

    normal.to_csv("data/anomaly/normal.csv", index=False)
    anomalous.to_csv("data/anomaly/anomalous.csv", index=False)

    print(f"Wrote {len(normal)} normal rows -> data/anomaly/normal.csv")
    print(normal.describe().to_string())
    print()
    print(f"Wrote {len(anomalous)} anomalous rows -> data/anomaly/anomalous.csv")
    print(anomalous.to_string(index=False))


if __name__ == "__main__":
    main()
