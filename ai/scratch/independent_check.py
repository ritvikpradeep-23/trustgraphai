"""Independent check of the anomaly signal + extreme-value floor.

Data here is generated from scratch with its own assumptions (lognormal
durations/amounts, unclipped Poisson counts, an evening-heavy hour mix), not
from trustgraph.anomaly.data_gen, so the model sees traffic it wasn't built
around. Every check runs with the floor ON and OFF to isolate what it does.

Targets: >=99% of fraud flagged at Caution or above, while <=5% of fresh
legit calls are. Pass a seed to draw a new sample (the rule was tuned on
2026; report on a seed it has never seen).

Run: PYTHONPATH=src python3 scratch/independent_check.py [seed]
"""
import json
import sys
from contextlib import contextmanager

import numpy as np

from trustgraph.anomaly import detector
from trustgraph.fusion import BANDS_PATH, risk_band
from trustgraph.pipeline import score_interaction

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
rng = np.random.default_rng(SEED)
print(f"seed {SEED}")
BANDS = json.load(open(BANDS_PATH))
FEATURES = ["duration_sec", "hour_of_day", "amount_ratio", "contact_freq_24h", "urgency_score", "new_channel_flag"]
results = []


@contextmanager
def floor(enabled: bool):
    original = detector._evidence_floor
    if not enabled:
        detector._evidence_floor = lambda strengths: 0.0
    try:
        yield
    finally:
        detector._evidence_floor = original


def fused(interaction: dict) -> float:
    return score_interaction(interaction)[1].score


def check(name: str, passed: bool, detail: str):
    results.append(passed)
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")


def fresh_normal(n: int) -> list[dict]:
    """Legit traffic, deliberately not the project's generator."""
    business = rng.normal(13, 2.5, n)
    evening = rng.normal(19.5, 1.5, n)
    hours = np.where(rng.random(n) < 0.8, business, evening).round().astype(int) % 24
    return [
        {
            "duration_sec": float(np.clip(rng.lognormal(np.log(90), 0.45), 20, 180)),
            "hour_of_day": int(h),
            "amount_ratio": float(rng.lognormal(0, 0.12)),
            "contact_freq_24h": int(rng.poisson(0.7)),
            "urgency_score": int(rng.poisson(0.3)),
            "new_channel_flag": int(rng.random() < 0.04),
        }
        for h in hours
    ]


def fresh_fraud(n: int, severity: str) -> list[dict]:
    """1-3 features pushed by a severity-dependent amount on top of fresh normal rows."""
    push = {
        "mild": {"amount_ratio": (1.4, 1.7), "contact_freq_24h": (3, 4), "urgency_score": (2, 3), "duration_sec": (240, 360)},
        "moderate": {"amount_ratio": (1.8, 3.0), "contact_freq_24h": (5, 9), "urgency_score": (3, 5), "duration_sec": (400, 900)},
        "severe": {"amount_ratio": (4.0, 15.0), "contact_freq_24h": (12, 40), "urgency_score": (6, 10), "duration_sec": (1200, 3600)},
    }[severity]
    rows = fresh_normal(n)
    for row in rows:
        feats = rng.choice(list(push), size=rng.integers(1, 4), replace=False)
        for feat in feats:
            lo, hi = push[feat]
            value = rng.uniform(lo, hi)
            row[feat] = int(round(value)) if feat in ("contact_freq_24h", "urgency_score") else float(value)
        if rng.random() < 0.3:
            row["hour_of_day"] = int(rng.choice([0, 1, 2, 3, 4, 23]))
        if rng.random() < 0.4:
            row["new_channel_flag"] = 1
    return rows


def flag_rate(rows: list[dict], cut: float) -> float:
    return float(np.mean([fused(r) >= cut for r in rows]))


print("1. False positives on 2000 fresh legit interactions (different generator)")
normal_rows = fresh_normal(2000)
for enabled in (False, True):
    with floor(enabled):
        caution = flag_rate(normal_rows, BANDS["caution"])
        high = flag_rate(normal_rows, BANDS["high"])
    print(f"     floor {'ON ' if enabled else 'OFF'}: Caution+ {caution:.1%}   High {high:.1%}")
with floor(True):
    on_caution = flag_rate(normal_rows, BANDS["caution"])
with floor(False):
    off_caution = flag_rate(normal_rows, BANDS["caution"])
print(f"     floor adds +{on_caution - off_caution:.1%} Caution+ (budget below is what counts)")
check("legit calls flagged Caution+ stay within the 5% budget", on_caution <= 0.05, f"{on_caution:.1%}")

print()
print("2. Fresh fraud at three severities (500 rows each), Caution+ detection")
caught = []
for severity in ("mild", "moderate", "severe"):
    rows = fresh_fraud(500, severity)
    with floor(False):
        off = flag_rate(rows, BANDS["caution"])
    with floor(True):
        on = flag_rate(rows, BANDS["caution"])
        on_high = flag_rate(rows, BANDS["high"])
        caught.append(on)
    print(f"     {severity:<9s} floor OFF {off:.1%} -> ON {on:.1%} (High {on_high:.1%})")
    check(f"floor never lowers {severity} detection", on >= off, f"{off:.0%} -> {on:.0%}")
    if severity == "severe":
        check("severe fraud is almost always caught", on >= 0.99, f"{on:.1%}")
overall = float(np.mean(caught))
# Rounded: 1485/1500 is exactly 99% but averages to 0.98999... in floating point.
check("99% of all fraud flagged Caution+", round(overall, 9) >= 0.99, f"{overall:.1%}")

print()
print("3. Dose-response: push ONE feature on a typical call, others held normal")
base = {"duration_sec": 95, "hour_of_day": 13, "amount_ratio": 1.0,
        "contact_freq_24h": 1, "urgency_score": 0, "new_channel_flag": 0}
sweeps = {
    "amount_ratio": [1.0, 1.3, 1.6, 2.0, 3.0, 5.0, 10.0, 50.0],
    "contact_freq_24h": [1, 2, 3, 4, 6, 10, 30],
    "urgency_score": [0, 1, 2, 3, 5, 10],
    "duration_sec": [95, 180, 300, 600, 1800, 7200],
}
for feat, values in sweeps.items():
    for enabled in (False, True):
        with floor(enabled):
            scores = [fused({**base, feat: v}) for v in values]
        label = "ON " if enabled else "OFF"
        print(f"     {feat:<17s} floor {label}: " + "  ".join(f"{v:g}->{s:.2f}" for v, s in zip(values, scores)))
    monotone = all(b >= a - 1e-9 for a, b in zip(scores, scores[1:]))
    check(f"{feat} score never drops as it gets more extreme (floor ON)", monotone, "monotone" if monotone else "dips")
    check(f"{feat} at its most extreme reaches High", risk_band(scores[-1], BANDS) == "High",
          f"{values[-1]:g} -> {scores[-1]:.2f}")

print()
print("4. The case the floor exists for: 9x vs 2x the usual amount")
with floor(False):
    off_2, off_9 = fused({**base, "amount_ratio": 2.0}), fused({**base, "amount_ratio": 9.0})
with floor(True):
    on_2, on_9 = fused({**base, "amount_ratio": 2.0}), fused({**base, "amount_ratio": 9.0})
print(f"     floor OFF: 2x -> {off_2:.2f}, 9x -> {off_9:.2f}")
print(f"     floor ON:  2x -> {on_2:.2f}, 9x -> {on_9:.2f}")
check("without floor, 9x is barely distinguished from 2x (the original bug)", off_9 - off_2 < 0.1,
      f"gap {off_9 - off_2:.2f}")
check("with floor, 9x reaches High", risk_band(on_9, BANDS) == "High", f"{on_9:.2f}")

print()
print("5. Things the floor must NOT do")
new_ch = fused({**base, "new_channel_flag": 1})
alone = {f: fused({**base, f: v}) for f, v in (("contact_freq_24h", 3), ("urgency_score", 2))}
check("one mildly-off count alone stays Low (legit traffic does this ~3% of the time)",
      all(risk_band(v, BANDS) == "Low" for v in alone.values()), ", ".join(f"{k} {v:.2f}" for k, v in alone.items()))
check("new channel alone is not floored to Caution", new_ch < BANDS["caution"], f"{new_ch:.2f}")
low_amt = fused({**base, "amount_ratio": 0.05})
check("a tiny amount is not treated as suspicious", low_amt < BANDS["caution"], f"0.05x -> {low_amt:.2f}")
three_am = fused({**base, "hour_of_day": 3})
check("3am alone stays below High", risk_band(three_am, BANDS) != "High", f"{three_am:.2f}")
combo = fused({**base, "amount_ratio": 1.3, "contact_freq_24h": 3, "urgency_score": 2})
check("several mild signals together reach Caution", risk_band(combo, BANDS) != "Low", f"{combo:.2f}")

print()
print("6. Garbage-in robustness")
edge_cases = {
    "all missing": ({}, "Insufficient data"),
    "all NaN": ({f: float("nan") for f in FEATURES}, "Insufficient data"),
    "absurd amount 1e9": ({**base, "amount_ratio": 1e9}, "1,000,000,000×"),
    "negative duration": ({**base, "duration_sec": -50}, "call duration invalid"),
    "hour 24": ({**base, "hour_of_day": 24}, "time of day invalid"),
    "non-numeric amount": ({**base, "amount_ratio": "lots"}, "amount invalid"),
    "extra unknown keys": ({**base, "caller_id": "+1555", "notes": "hi"}, "No unusual behavior"),
}
for name, (interaction, expected) in edge_cases.items():
    try:
        signals, result = score_interaction(interaction)
        explanation = next(s for s in signals if s.signal_name == "anomaly").explanation
        ok = 0.0 <= result.score <= 1.0 and expected in explanation
        check(name, ok, f"{result.score:.2f}  {explanation}")
    except Exception as exc:
        check(name, False, f"{type(exc).__name__}: {exc}")

print()
print(f"{sum(results)}/{len(results)} checks passed")
