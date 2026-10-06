# Model card: fast_r07

> **All training and test data for this model is synthetic** (written by the generator in `eval/`). The numbers below show how it behaves on that data, not real-world accuracy.

## What it is
The similarity examples after round 07: the previous best (fast_r04) plus 27 missed scams and 0 false-alarm honest messages from round 07.

## How it was tested
Dev rounds 01-02, at this bundle's own ~10% / ~1% dev false-alarm cut-offs: scams caught 63.3% (was 57.5%), honest flagged at High 0.0%. Real UK SMS honest texts flagged 5.6% (demo-safe 4.4%).

## Limits
Synthetic data from one generator; the added examples come from the same generator as later rounds.

## Promote
`python scripts/promote_model.py models/candidate/fast_r07` (dry run), then add `--yes`. `--rollback` undoes it.

