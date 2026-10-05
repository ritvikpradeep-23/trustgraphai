"""Track A: retrain the anomaly model on a larger, more realistic normal set.

    PYTHONPATH=src python -m training.track_a

The current model learned "normal" from 300 tidy rows. Here it learns from
20,000 normal interactions that include honest odd cases: late-night
messages, a large one-off payment, a burst of messages from family, a new
phone, a long call. It is still trained on NORMAL rows only: feeding it scams
would teach it that scams are normal.

Anomalies to detect come from a separate function (injected_anomalies) that
never shares code with the normal generator. Both models are compared at
matched false-alarm rates (cut-offs set on a separate normal calibration set,
~10% and ~1% flagged), then on the old held-out normal rows and the named
scenarios. This only matters once something sends call details (hour,
frequency, new sender): with text only, the anomaly signal sees just the
urgency-word count. Writes reports/<date>-training/track_a* and
models/candidate/anomaly_v2/.
"""
import argparse
import json
import tempfile
import time
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from eval import metrics
from training.bundle import live_bands, write_bundle
from training.track_b import write_csv
from trustgraph.anomaly import detector
from trustgraph.anomaly.data_gen import _HOUR_WEIGHTS
from trustgraph.anomaly.features import RAW_FEATURES
from trustgraph.anomaly.train import MODEL_PATH, save_model, train

SEED = 0
N_NORMAL = 20_000
# Share of each honest odd case in the normal data.
ODD = {"late_night": 0.06, "large_one_off": 0.04, "family_burst": 0.05, "new_phone": 0.05, "long_call": 0.03}


def normal_interactions(n: int, seed: int) -> pd.DataFrame:
    """Everyday interactions plus honest odd cases, labelled by kind."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "duration_sec": rng.uniform(20, 180, n),
        "hour_of_day": rng.choice(24, n, p=_HOUR_WEIGHTS),
        "amount_ratio": np.clip(rng.normal(1.0, 0.15, n), 0.1, None),
        "contact_freq_24h": rng.poisson(0.8, n),
        "urgency_score": rng.poisson(0.4, n),
        "new_channel_flag": (rng.random(n) < 0.05).astype(int),
    })
    kind = rng.choice(["everyday", *ODD], n, p=[1 - sum(ODD.values()), *ODD.values()])
    m = kind == "late_night"
    df.loc[m, "hour_of_day"] = rng.choice([22, 23, 0, 1, 5], m.sum())
    m = kind == "large_one_off"
    df.loc[m, "amount_ratio"] = rng.uniform(1.5, 4.0, m.sum())
    m = kind == "family_burst"
    df.loc[m, "contact_freq_24h"] = rng.integers(3, 9, m.sum())
    df.loc[m, "urgency_score"] = rng.poisson(1.0, m.sum())
    m = kind == "new_phone"
    df.loc[m, "new_channel_flag"] = 1
    m = kind == "long_call"
    df.loc[m, "duration_sec"] = rng.uniform(300, 1200, m.sum())
    df["kind"] = kind
    return df


def injected_anomalies(n: int, seed: int) -> pd.DataFrame:
    """Separate from normal_interactions on purpose. Each row starts from its
    own plain baseline; 40% get one feature pushed to an extreme, 60% get 2-3
    features pushed in the directions scams take (very short call, small
    hours, a large amount, many contacts, urgent words, a new channel)."""
    rng = np.random.default_rng(seed)
    rows = []
    push = {
        "duration_sec": lambda: float(rng.choice([rng.uniform(0, 8), rng.uniform(900, 2400)])),
        "hour_of_day": lambda: int(rng.choice([1, 2, 3, 4])),
        "amount_ratio": lambda: float(rng.uniform(4.0, 12.0)),
        "contact_freq_24h": lambda: int(rng.integers(10, 30)),
        "urgency_score": lambda: int(rng.integers(4, 10)),
        "new_channel_flag": lambda: 1,
    }
    for _ in range(n):
        row = {"duration_sec": float(rng.uniform(30, 150)), "hour_of_day": int(rng.integers(9, 18)),
               "amount_ratio": float(rng.uniform(0.8, 1.2)), "contact_freq_24h": int(rng.integers(0, 2)),
               "urgency_score": int(rng.integers(0, 2)), "new_channel_flag": 0}
        k = 1 if rng.random() < 0.4 else int(rng.choice([2, 3]))
        chosen = rng.choice(RAW_FEATURES, k, replace=False)
        for f in chosen:
            row[f] = push[f]()
        row["pushed"] = "+".join(sorted(chosen))
        rows.append(row)
    return pd.DataFrame(rows)


def anomaly_scores(bundle: dict, df: pd.DataFrame) -> np.ndarray:
    saved = detector._bundle
    detector._bundle = bundle
    try:
        return np.array([detector.anomaly_score(r).score for r in df[RAW_FEATURES].to_dict(orient="records")])
    finally:
        detector._bundle = saved


def scenario_check(bundle: dict, bands: dict) -> dict:
    from trustgraph.fusion import risk_band
    from trustgraph.pipeline import score_interaction
    from trustgraph.scenarios import SCENARIOS
    saved = detector._bundle
    detector._bundle = bundle
    try:
        res = {"scam": [], "legit": []}
        for _, kind, inter in SCENARIOS:
            res[kind].append(risk_band(score_interaction(inter)[1].score, bands))
    finally:
        detector._bundle = saved
    return {"scams_caught": sum(b != "Low" for b in res["scam"]), "scams": len(res["scam"]),
            "honest_kept_low": sum(b == "Low" for b in res["legit"]), "honest": len(res["legit"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=f"reports/{date.today().isoformat()}-training")
    args = ap.parse_args()
    out = Path(args.out)
    t0 = time.time()

    train_normal = normal_interactions(N_NORMAL, seed=SEED)
    calib_normal = normal_interactions(5_000, seed=SEED + 1)
    test_normal = normal_interactions(5_000, seed=SEED + 2)
    anomalies = injected_anomalies(2_000, seed=SEED + 3)
    old_test = pd.read_csv("data/anomaly/normal_test.csv")
    old_anomalous = pd.read_csv("data/anomaly/anomalous.csv")

    current = joblib.load(MODEL_PATH)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "anomaly_isolation_forest.joblib"
        candidate = save_model(train(train_normal[RAW_FEATURES]), train_normal[RAW_FEATURES], str(path))

        table, scored = [], {}
        rng = np.random.default_rng(SEED)
        for name, bundle in (("current (300 tidy normal rows)", current), ("candidate (20,000 rows incl. odd cases)", candidate)):
            cal = anomaly_scores(bundle, calib_normal)
            bands = metrics.calibrate(cal)
            s_test, s_anom = anomaly_scores(bundle, test_normal), anomaly_scores(bundle, anomalies)
            s_old, s_old_anom = anomaly_scores(bundle, old_test), anomaly_scores(bundle, old_anomalous)
            row = {"model": name, "caution_cutoff": bands["caution"], "high_cutoff": bands["high"]}
            for band in ("caution", "high"):
                det = metrics.rate(metrics.hits(s_anom, bands[band]), rng)
                row[f"anomalies_caught_{band}"], row[f"lo_{band}"], row[f"hi_{band}"] = det["value"], det["lo"], det["hi"]
                row[f"new_normal_flagged_{band}"] = float(metrics.hits(s_test, bands[band]).mean())
                row[f"old_normal_flagged_{band}"] = float(metrics.hits(s_old, bands[band]).mean())
            row["old_15_anomalies_caught_caution"] = int(metrics.hits(s_old_anom, bands["caution"]).sum())
            odd = {}
            for kind in ODD:
                m = (test_normal["kind"] == kind).to_numpy()
                odd[kind] = float(metrics.hits(s_test[m], bands["caution"]).mean())
            row.update({f"odd_{k}_flagged": v for k, v in odd.items()})
            scored[name] = (bundle, s_anom)
            table.append(row)
            print(f"[{name}] anomalies caught {row['anomalies_caught_caution']:.1%} (High {row['anomalies_caught_high']:.1%}); "
                  f"old normal flagged {row['old_normal_flagged_caution']:.1%}; odd cases flagged {odd}")

        by_kind = []
        for name, (_, s) in scored.items():
            bands = {"caution": next(t for t in table if t["model"] == name)["caution_cutoff"]}
            for pushed in sorted(anomalies["pushed"].unique(), key=lambda p: (p.count("+"), p)):
                m = (anomalies["pushed"] == pushed).to_numpy()
                if m.sum() >= 20:
                    by_kind.append({"model": name, "pushed": pushed, "n": int(m.sum()),
                                    "caught_caution": float(metrics.hits(s[m], bands["caution"]).mean())})

        cur, new = table
        detection_up = new["anomalies_caught_caution"] - cur["anomalies_caught_caution"]
        old_fa_change = new["old_normal_flagged_caution"] - cur["old_normal_flagged_caution"]
        saved = detector._bundle
        detector._bundle = candidate
        try:
            bands_live = live_bands()
        finally:
            detector._bundle = saved
        scen_cur = scenario_check(current, json.loads(Path("models/risk_bands.json").read_text()))
        scen_new = scenario_check(candidate, bands_live)
        # Track A rule: adopt only if detection rises or false alarms fall, without the other getting worse.
        better = detection_up > 0.01 or old_fa_change < -0.01
        worse = detection_up < -0.01 or old_fa_change > 0.01 or scen_new["scams_caught"] < scen_cur["scams_caught"] \
            or scen_new["honest_kept_low"] < scen_cur["honest_kept_low"]
        verdict = "adopt" if better and not worse else "reject"
        dev_m = {"anomalies_caught_caution": new["anomalies_caught_caution"],
                 "fpr_caution": new["new_normal_flagged_caution"], "fpr_high": new["new_normal_flagged_high"],
                 "current_engine": {"anomalies_caught_caution": cur["anomalies_caught_caution"],
                                    "fpr_caution": cur["new_normal_flagged_caution"],
                                    "fpr_high": cur["new_normal_flagged_high"]},
                 "verdict": verdict}
        card = card_text(table, scen_cur, scen_new, verdict)
        bundle = write_bundle("anomaly_v2", {"anomaly_isolation_forest.joblib": path},
                              {"anomaly_isolation_forest.joblib": MODEL_PATH}, bands_live,
                              data_hash=str(pd.util.hash_pandas_object(train_normal).sum()), n_train=N_NORMAL,
                              seeds={"normal": SEED, "calibration": SEED + 1, "test": SEED + 2, "anomalies": SEED + 3,
                                     "isolation_forest": 0},
                              dev_metrics=dev_m, card=card)

    res = {"table": table, "scenarios": {"current": scen_cur, "candidate": scen_new}, "verdict": verdict,
           "bundle": str(bundle), "live_bands": bands_live}
    (out / "track_a.json").write_text(json.dumps(res, indent=1, default=float))
    write_csv(out / "track_a.csv", table)
    write_csv(out / "track_a_by_pushed_feature.csv", by_kind)
    with open(out / "runlog.md", "a", encoding="utf-8") as f:
        f.write(f"- {time.strftime('%H:%M:%S')} `PYTHONPATH=src python -m training.track_a` (seeds {SEED}-{SEED + 3}, "
                f"{time.time() - t0:.0f}s): verdict {verdict}\n")
    print(json.dumps(res, indent=1, default=float))


def card_text(table, scen_cur, scen_new, verdict) -> str:
    cur, new = table
    return f"""## What it is
The anomaly signal's Isolation Forest (same features, settings and evidence floor), retrained on 20,000 normal
interactions instead of 300. The normal data includes honest odd cases: late-night messages (6%), a large one-off
payment (4%), a burst of family messages (5%), a new phone (5%), a long call (3%). Trained on normal rows only.

## How it was tested
Cut-offs set on 5,000 separate normal rows (~10% / ~1% flagged); 2,000 injected anomalies from a separate
function (1 feature pushed to an extreme, or 2-3 pushed the way scams go).

| | Current model | This bundle |
|---|---|---|
| Injected anomalies caught at Caution | {cur['anomalies_caught_caution']:.1%} | {new['anomalies_caught_caution']:.1%} [{new['lo_caution']:.1%}, {new['hi_caution']:.1%}] |
| Injected anomalies caught at High | {cur['anomalies_caught_high']:.1%} | {new['anomalies_caught_high']:.1%} |
| New normal rows flagged at Caution | {cur['new_normal_flagged_caution']:.1%} | {new['new_normal_flagged_caution']:.1%} |
| Old held-out normal rows flagged at Caution | {cur['old_normal_flagged_caution']:.1%} | {new['old_normal_flagged_caution']:.1%} |
| Late-night honest messages flagged | {cur['odd_late_night_flagged']:.1%} | {new['odd_late_night_flagged']:.1%} |
| Large one-off honest payments flagged | {cur['odd_large_one_off_flagged']:.1%} | {new['odd_large_one_off_flagged']:.1%} |
| Family bursts flagged | {cur['odd_family_burst_flagged']:.1%} | {new['odd_family_burst_flagged']:.1%} |
| Named scenarios: scams caught / honest kept Low | {scen_cur['scams_caught']}/{scen_cur['scams']}, {scen_cur['honest_kept_low']}/{scen_cur['honest']} | {scen_new['scams_caught']}/{scen_new['scams']}, {scen_new['honest_kept_low']}/{scen_new['honest']} |

Verdict: **{verdict}**.

## Limits
- All rows are generated; the normal mix and the odd-case shares are assumptions, not measurements.
- Matters only once something sends call details (hour, contact frequency, new sender). With text only, the
  anomaly signal sees just the urgency-word count.
- The joblib file is tied to scikit-learn {__import__('sklearn').__version__}.

## Promote / roll back
`python scripts/promote_model.py models/candidate/anomaly_v2 --yes`, then restart the server.
`python scripts/promote_model.py --rollback` undoes it.
"""


if __name__ == "__main__":
    main()
