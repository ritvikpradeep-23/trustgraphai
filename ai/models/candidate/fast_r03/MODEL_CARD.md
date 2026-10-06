# Model card: fast_r03

> **All training and test data for this model is synthetic** (written by the generator in `eval/`). The numbers below show how it behaves on that data, not real-world accuracy.

## What it is
The similarity examples after round 03: the previous best (demo-safe) plus 35 missed scams and 0 false-alarm honest messages from round 03.

## How it was tested
Dev rounds 01-02, at this bundle's own ~10% / ~1% dev false-alarm cut-offs: scams caught 48.3% (was 48.3%), honest flagged at High 0.0%. Real UK SMS honest texts flagged 1.1% (demo-safe 4.4%).

## Limits
Synthetic data from one generator; the added examples come from the same generator as later rounds.

## Promote
`python scripts/promote_model.py models/candidate/fast_r03` (dry run), then add `--yes`. `--rollback` undoes it.

