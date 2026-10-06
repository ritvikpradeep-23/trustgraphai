# Model card: classifier_v1

> **All training and test data for this model is synthetic** (written by the generator in `eval/`). The numbers below show how it behaves on that data, not real-world accuracy.

## What it is
A logistic-regression text classifier (TF-IDF word 1-2 grams + character 3-5 grams, balanced class weights,
C=10.0, Platt-scaled on out-of-fold scores) trained on the 1413 corpus-split messages. Text is normalized first
(disguise tricks undone; links, phones, amounts, numbers replaced by markers). It is a fifth signal named
"classifier", appended after the other four only when TRUSTGRAPH_CLASSIFIER=1, with fusion weight 0.3
(chosen on dev from 0.3 / 0.5 / 1.0). Built on top of Track B examples (similarity_v2).

## How it was tested (dev, each at its own ~10% / ~1% dev false-alarm cut-offs)

| | Scams caught at Caution | Honest flagged at High | ROC-AUC |
|---|---|---|---|
| Engine without classifier | 91.2% | 1.0% | 0.963 |
| Engine with classifier | 93.1% [90.7%, 95.4%] | 1.0% | 0.975 |
| Classifier alone | 75.4% | 1.1% | 0.925 |
| Baseline: length + has link | 50.2% | 1.4% | 0.835 |

Classifier alone, three ways: random CV 100.0%,
group CV 82.3%, dev 75.4%,
leave-one-type-out 66.5%.
Engine leave-one-type-out mean: 75.2% without, 82.8% with.
Trained without the 16 types the engine had no examples for, scored on them: classifier alone
68.8%; engine 90.3% without,
91.9% with.

Shortcut audit: 5 watch-list words among the 50 strongest terms each way (details, zzamount, zzlink, zznum, zzphone);
retrained without them, classifier alone catches
69.9% (was 75.4%).

Verdict: **reject**.

## Limits
- Trained and tested on messages from one generator: it can learn that generator's style. The leave-one-type-out
  and 13-types-only numbers are the honest ones.
- Cut-offs in risk_bands.json assume the classifier is ON and similarity_v2 is promoted.
- The website shows it as a fifth row; teammates' tools that expect exactly four signals must be checked first.

## Promote / roll back
Set TRUSTGRAPH_CLASSIFIER=1, run `python scripts/promote_model.py models/candidate/classifier_v1 --yes`,
restart the server. `python scripts/promote_model.py --rollback` undoes it.

