# TrustGraph evaluation summary

> **All numbers come from synthetic, AI-written messages.** They show how the engine behaves on this generated data, not its real-world accuracy. Fake placeholders only; no real people, numbers or links.

- Frozen test set: `eval/data/test.jsonl`, sha256 `6fc6fd2858a5bb33…` (verified at start of run), generator seed 0, 1 message(s) removed by the leakage filter (>0.9 similarity).
- Test set: 894 scams across 29 types (13 the engine has reference examples for, 16 it has never seen) and 1400 honest messages across 13 types.
- Thresholds are calibrated on **dev** honest messages only (Caution flags ~10%, High ~1%) and written to `thresholds.json` here, never to `models/`. Nothing was tuned on the test set.

## Headline (text only, as a text-only client would send)

| | Caution or above | High |
|---|---|---|
| Scams caught, all types | 74.0% [71.4%, 77.0%] | 49.1% [45.6%, 52.3%] |
| Scams caught, types with reference examples | 92.8% [90.2%, 95.3%] | 79.8% [75.7%, 83.7%] |
| Scams caught, never-seen types | 59.8% [55.4%, 63.9%] | 25.6% [21.7%, 29.2%] |
| Honest messages flagged (false alarms) | 8.6% [7.4%, 10.1%] | 1.0% [0.5%, 1.6%] |
| Precision | 84.5% | 96.9% |

ROC-AUC 0.901 [0.887, 0.916], PR-AUC 0.884 [0.866, 0.900]. Precision depends on this set's 894:1400 scam-to-honest ratio; real traffic has far fewer scams.

### Scams caught per type (Caution or above, 95% CI)

| Type | Seen? | n | Caution | High |
|---|---|---|---|---|
| bank safe-account scam | seen | 45 | 100.0% [100.0%, 100.0%] | 100.0% |
| blackmail or sextortion | seen | 19 | 100.0% [100.0%, 100.0%] | 100.0% |
| family emergency or new-number scam | seen | 44 | 100.0% [100.0%, 100.0%] | 84.1% |
| job or advance-fee scam | seen | 23 | 100.0% [100.0%, 100.0%] | 56.5% |
| parcel or delivery fee | seen | 25 | 100.0% [100.0%, 100.0%] | 60.0% |
| prize or lottery fee | seen | 38 | 100.0% [100.0%, 100.0%] | 89.5% |
| romance scam money request | seen | 23 | 100.0% [100.0%, 100.0%] | 95.7% |
| gift-card request from a boss or colleague | seen | 25 | 96.0% [88.0%, 100.0%] | 96.0% |
| tech support remote-access scam | seen | 23 | 87.0% [69.6%, 100.0%] | 60.9% |
| one-time code or password request | seen | 39 | 84.6% [71.8%, 94.9%] | 82.1% |
| tax or government threat | seen | 34 | 82.4% [67.6%, 94.1%] | 67.6% |
| invoice or bank-details change | seen | 24 | 79.2% [62.5%, 95.8%] | 70.8% |
| investment or crypto scam | seen | 25 | 72.0% [52.0%, 88.0%] | 56.0% |
| student scholarship or exam scam | unseen | 40 | 82.5% [70.0%, 92.5%] | 42.5% |
| deepfake CEO video call | unseen | 18 | 77.8% [55.6%, 94.4%] | 27.8% |
| instant-loan app harassment | unseen | 40 | 77.5% [65.0%, 90.0%] | 60.0% |
| rental or booking deposit | unseen | 25 | 76.0% [60.0%, 92.0%] | 16.0% |
| task or like-and-earn scam | unseen | 25 | 72.0% [52.0%, 88.0%] | 16.0% |
| crypto airdrop or wallet drainer | unseen | 35 | 71.4% [54.3%, 85.7%] | 28.6% |
| KYC or ID update expiry | unseen | 40 | 67.5% [52.5%, 82.5%] | 20.0% |
| digital arrest | unseen | 39 | 59.0% [43.6%, 74.4%] | 33.3% |
| social-media verify or copyright strike | unseen | 24 | 58.3% [37.5%, 75.0%] | 45.8% |
| electricity disconnection | unseen | 22 | 54.5% [31.8%, 77.3%] | 22.7% |
| FASTag or toll balance | unseen | 38 | 50.0% [34.2%, 65.8%] | 23.7% |
| e-challan or traffic fine | unseen | 40 | 50.0% [35.0%, 65.0%] | 22.5% |
| fake customer-care helpline | unseen | 24 | 50.0% [29.2%, 70.8%] | 25.0% |
| QR code scam | unseen | 39 | 41.0% [25.6%, 56.4%] | 0.0% |
| fake CAPTCHA or paste-command | unseen | 34 | 38.2% [23.5%, 55.9%] | 14.7% |
| UPI collect or accidental refund | unseen | 24 | 29.2% [12.5%, 50.0%] | 0.0% |

### By language and evasion trick (scams caught at Caution)

en 73.7% (n=771), hinglish 84.6% (n=65), manglish 67.2% (n=58).

emoji_padding 68.5% (n=73), leetspeak 73.2% (n=56), none 75.4% (n=613), obfuscated_link 70.5% (n=44), spacing 71.2% (n=52), split_phrasing 73.2% (n=56).

## Real-world false-alarm check

4827 genuine non-scam texts from the public UCI SMS Spam Collection (UK, 2000s): **9.6% [8.7%, 10.4%] flagged at Caution**, 1.3% [1.0%, 1.7%] at High. Its spam is mostly marketing, not scams; 25.3% of it is flagged.

## Limits

- Synthetic data written by the same AI that built the engine: shared phrasing habits can flatter results.
- Hinglish and Manglish were written by a non-native writer and may read unnaturally.
- A few honest code messages contain an invoice-style number where the code should be (a generator slip); left in place because the test set is frozen.
- Text only: continuity and precedent have nothing to work with unless account, number or history data are supplied.
- The negation and Hinglish/Manglish fixes (after the first report, reports/2026-10-05/) were found by reading that report's test-set errors and real-SMS false alarms, so later numbers on those two sets are slightly optimistic. A fresh batch from a never-used seed is the cleaner before/after comparison.

## Re-run

```
PYTHONPATH=src python -m eval.run                    # all sections
PYTHONPATH=src python -m eval.run --batch-seed 7     # plus a fresh batch
```
