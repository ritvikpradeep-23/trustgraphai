# Track A: retrain the anomaly model (verdict: reject)

> All rows are generated. Not real-world accuracy.

The Isolation Forest was retrained on **20,000** normal interactions instead of 300, using the same features,
settings and evidence floor. The normal data includes honest odd cases: late-night messages 6%, a large one-off
payment 4%, a family burst 5%, a new phone 5%, a long call 3%. The 2,000 anomalies to catch come from a separate
function: one feature pushed to an extreme, or 2-3 pushed the way scams go. Cut-offs are set on 5,000 separate
normal rows (~10% / ~1% flagged).

| | Current (300 tidy rows) | Candidate (20,000 incl. odd cases) |
|---|---|---|
| Injected anomalies caught at Caution | 78.1% [76.5, 79.8] | 79.8% [78.0, 81.5] |
| Injected anomalies caught at High | 55.7% | **72.6%** |
| New normal rows flagged (Caution / High) | 10.6% / 1.1% | 10.6% / 1.0% |
| Old held-out normal rows flagged at Caution | 0.5% | 1.3% |
| Honest large one-off payments flagged | 94% | **73%** |
| Honest long calls flagged | 96% | **77%** |
| Honest late-night messages flagged | 3% | 10% |
| Honest new-phone messages flagged | 1% | 7% |
| Named demo scenarios: scams caught / honest kept Low (live-style cut-offs) | 18/18, 6/6 | **17/18, 5/6** |

Rule: adopt only if detection rises or false alarms fall without the other getting worse. Detection rose (High
band clearly, Caution slightly), but one demo scam is now missed and one honest control is no longer Low.

**Verdict: reject.** The bundle `models/candidate/anomaly_v2/` is kept for reference.

## What this means
1. Teaching the model about honest odd cases made it far less jumpy about big one-off payments and long calls.
2. It also got sharper at the strict High level for clear anomalies (56% to 73%).
3. But it now shrugs at a few things the current one flags (late-night, new phone), and it slipped on the demo cases.
4. None of this matters until something sends call details (time, frequency, new sender): with text only, the
   anomaly check sees just the urgent-word count.
5. The mix of "odd but honest" cases is my guess. Real call logs would settle it.
