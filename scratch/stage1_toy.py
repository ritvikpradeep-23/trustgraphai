"""Stage 1: sanity-check IsolationForest mechanics on throwaway data."""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

rng = np.random.default_rng(42)

# 18 normal rows clustered in 10-20, plus 2 deliberate outliers far outside.
normal = pd.DataFrame({
    "value_a": rng.uniform(10, 20, size=18),
    "value_b": rng.uniform(10, 20, size=18),
})
outliers = pd.DataFrame({
    "value_a": [90, 95],
    "value_b": [95, 90],
})
df = pd.concat([normal, outliers], ignore_index=True)

model = IsolationForest(random_state=42)
model.fit(df[["value_a", "value_b"]])

# Lower score_samples() == more anomalous, so flip sign for an intuitive
# "higher = more anomalous" ranking.
df["anomaly_score"] = -model.score_samples(df[["value_a", "value_b"]])
df_sorted = df.sort_values("anomaly_score", ascending=False)

print(df_sorted.to_string(index_names=False))

top2_idx = set(df_sorted.head(2).index)
outlier_idx = {18, 19}
print()
if top2_idx == outlier_idx:
    print("PASS: the 2 planted outliers are the top 2 most anomalous rows.")
else:
    print("FAIL: outliers did not land on top. Investigate before Stage 2.")
