# Model card: similarity_v3

> **All training and test data for this model is synthetic** (written by the generator in `eval/`). The numbers below show how it behaves on that data, not real-world accuracy.

## What it is
Second Track B attempt (capped_10_casual). The similarity signal's built-in examples plus, for each scam type and each
honest message type in the corpus split, at most its 10 most varied messages
(250 scam, 111 honest), plus 40 short casual everyday texts written by hand.
Same detector code, red flags, negation handling and wording-only cap.

## How it was tested
Dev split at this model's own ~10% / ~1% dev false-alarm cut-offs; real UK SMS honest texts as a false-alarm check.

| | Current examples | This bundle |
|---|---|---|
| Dev scams caught at Caution | 70.6% | 91.2% [88.5%, 93.8%] |
| Dev honest flagged at High | 1.0% | 1.0% |
| Mean leave-one-type-out recall | 56.8% | 75.2% |
| 16 types built without, scored on | 55.1% | 75.3% |
| Real UK SMS honest texts flagged | 19.3% | 16.7% |

Verdict: **adopt with caveats**.

## Limits
- This retry was designed after the first attempt failed the real-SMS check, and that check gated the choice,
  so the real-SMS number above is slightly optimistic.
- Added examples come from the same generator as dev and test; leave-one-type-out is the honest novelty number.

## Promote / roll back
`python scripts/promote_model.py models/candidate/similarity_v3 --yes`, then restart the server.
`python scripts/promote_model.py --rollback` undoes it.

