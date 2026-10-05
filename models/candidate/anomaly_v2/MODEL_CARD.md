# Model card: anomaly_v2

> **All training and test data for this model is synthetic** (written by the generator in `eval/`). The numbers below show how it behaves on that data, not real-world accuracy.

## What it is
The anomaly signal's Isolation Forest (same features, settings and evidence floor), retrained on 20,000 normal
interactions instead of 300. The normal data includes honest odd cases: late-night messages (6%), a large one-off
payment (4%), a burst of family messages (5%), a new phone (5%), a long call (3%). Trained on normal rows only.

## How it was tested
Cut-offs set on 5,000 separate normal rows (~10% / ~1% flagged); 2,000 injected anomalies from a separate
function (1 feature pushed to an extreme, or 2-3 pushed the way scams go).

| | Current model | This bundle |
|---|---|---|
| Injected anomalies caught at Caution | 78.1% | 79.8% [78.0%, 81.5%] |
| Injected anomalies caught at High | 55.7% | 72.6% |
| New normal rows flagged at Caution | 10.6% | 10.6% |
| Old held-out normal rows flagged at Caution | 0.5% | 1.3% |
| Late-night honest messages flagged | 3.0% | 10.2% |
| Large one-off honest payments flagged | 94.0% | 73.4% |
| Family bursts flagged | 66.9% | 62.4% |
| Named scenarios: scams caught / honest kept Low | 18/18, 6/6 | 17/18, 5/6 |

Verdict: **reject**.

## Limits
- All rows are generated; the normal mix and the odd-case shares are assumptions, not measurements.
- Matters only once something sends call details (hour, contact frequency, new sender). With text only, the
  anomaly signal sees just the urgency-word count.
- The joblib file is tied to scikit-learn 1.9.1.

## Promote / roll back
`python scripts/promote_model.py models/candidate/anomaly_v2 --yes`, then restart the server.
`python scripts/promote_model.py --rollback` undoes it.

