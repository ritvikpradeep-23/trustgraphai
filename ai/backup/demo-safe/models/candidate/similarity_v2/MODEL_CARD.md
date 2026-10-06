# Model card: similarity_v2

> **All training and test data for this model is synthetic** (written by the generator in `eval/`). The numbers below show how it behaves on that data, not real-world accuracy.

## What it is
The similarity signal's reference examples, grown from 91 scam and
78 honest hand-written examples by 433 scam and 416 honest
messages from the corpus split (564 near-copies and 0
messages close to a dev/test message removed). Comparison after text normalization: no.
Same detector code, red flags, negation handling and wording-only cap.

## How it was tested
Dev split (452 scams, 1,498 honest; template families never shared with the corpus split), at this model's
own cut-offs flagging about 10% (Caution) and 1% (High) of dev honest messages.

| | Current examples | This bundle |
|---|---|---|
| Dev scams caught at Caution | 70.6% | 91.4% [88.7%, 94.0%] |
| Dev honest flagged at High | 1.0% | 1.0% |
| Mean leave-one-type-out recall | 56.8% | 79.1% |
| 16 types built without, scored on | 55.1% | 75.7% |
| Real UK SMS honest texts flagged | 19.3% | 34.3% |

Verdict: **reject**.

## Limits
- Every added example comes from the same generator as the dev and test messages, so dev recall flatters it;
  leave-one-type-out is the honest novelty number.
- Cut-offs in risk_bands.json are set on synthetic honest messages (src/trustgraph/evaluate.py's calibration set).

## Promote / roll back
`python scripts/promote_model.py models/candidate/similarity_v2 --yes`, then restart the server.
`python scripts/promote_model.py --rollback` undoes it.

