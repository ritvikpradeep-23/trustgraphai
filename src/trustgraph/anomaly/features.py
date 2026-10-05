import numpy as np
import pandas as pd

# What callers put in the interaction dict.
RAW_FEATURES = [
    "duration_sec",
    "hour_of_day",
    "amount_ratio",
    "contact_freq_24h",
    "urgency_score",
    "new_channel_flag",
]

# What the model sees: hour_of_day is split into sin/cos so 23:00 and 00:00
# are neighbours instead of opposite ends of a 0-23 line.
MODEL_FEATURES = [
    "duration_sec",
    "hour_sin",
    "hour_cos",
    "amount_ratio",
    "contact_freq_24h",
    "urgency_score",
    "new_channel_flag",
]


def to_model_frame(raw: pd.DataFrame) -> pd.DataFrame:
    angle = 2 * np.pi * raw["hour_of_day"] / 24
    out = raw[RAW_FEATURES].copy()
    out["hour_sin"] = np.sin(angle)
    out["hour_cos"] = np.cos(angle)
    return out[MODEL_FEATURES]


def circular_hour_distance(hour, center):
    d = np.abs(np.asarray(hour) - center) % 24
    return np.minimum(d, 24 - d)
