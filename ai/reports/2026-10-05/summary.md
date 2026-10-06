# TrustGraph evaluation summary

> **All numbers come from synthetic, AI-written messages.** They show how the engine behaves on this generated data, not its real-world accuracy. Fake placeholders only; no real people, numbers or links.

- Frozen test set: `eval/data/test.jsonl`, sha256 `6fc6fd2858a5bb33…` (verified at start of run), generator seed 0, 1 message(s) removed by the leakage filter (>0.9 similarity).
- Test set: 894 scams across 29 types (13 the engine has reference examples for, 16 it has never seen) and 1400 honest messages across 13 types.
- Thresholds are calibrated on **dev** honest messages only (Caution flags ~10%, High ~1%) and written to `thresholds.json` here, never to `models/`. Nothing was tuned on the test set.

## Headline (text only, as a text-only client would send)

| | Caution or above | High |
|---|---|---|
| Scams caught, all types | 70.5% [67.4%, 73.7%] | 22.7% [19.8%, 25.5%] |
| Scams caught, types with reference examples | 92.8% [90.2%, 95.1%] | 40.6% [35.7%, 45.0%] |
| Scams caught, never-seen types | 53.5% [48.9%, 57.8%] | 9.1% [6.7%, 11.6%] |
| Honest messages flagged (false alarms) | 10.5% [8.9%, 12.1%] | 1.0% [0.5%, 1.6%] |
| Precision | 81.1% | 93.5% |

ROC-AUC 0.867 [0.851, 0.883], PR-AUC 0.829 [0.807, 0.850]. Precision depends on this set's 894:1400 scam-to-honest ratio; real traffic has far fewer scams.

### Scams caught per type (Caution or above, 95% CI)

| Type | Seen? | n | Caution | High |
|---|---|---|---|---|
| bank safe-account scam | seen | 45 | 100.0% [100.0%, 100.0%] | 88.9% |
| blackmail or sextortion | seen | 19 | 100.0% [100.0%, 100.0%] | 21.1% |
| gift-card request from a boss or colleague | seen | 25 | 100.0% [100.0%, 100.0%] | 52.0% |
| job or advance-fee scam | seen | 23 | 100.0% [100.0%, 100.0%] | 52.2% |
| parcel or delivery fee | seen | 25 | 100.0% [100.0%, 100.0%] | 20.0% |
| prize or lottery fee | seen | 38 | 100.0% [100.0%, 100.0%] | 68.4% |
| family emergency or new-number scam | seen | 44 | 97.7% [93.2%, 100.0%] | 9.1% |
| tech support remote-access scam | seen | 23 | 95.7% [87.0%, 100.0%] | 0.0% |
| investment or crypto scam | seen | 25 | 88.0% [76.0%, 100.0%] | 20.0% |
| romance scam money request | seen | 23 | 82.6% [65.2%, 95.7%] | 13.0% |
| tax or government threat | seen | 34 | 82.4% [70.6%, 94.1%] | 50.0% |
| one-time code or password request | seen | 39 | 79.5% [66.7%, 92.3%] | 59.0% |
| invoice or bank-details change | seen | 24 | 79.2% [62.5%, 95.8%] | 20.8% |
| deepfake CEO video call | unseen | 18 | 77.8% [55.6%, 94.4%] | 0.0% |
| student scholarship or exam scam | unseen | 40 | 70.0% [55.0%, 85.0%] | 15.0% |
| task or like-and-earn scam | unseen | 25 | 68.0% [48.0%, 84.1%] | 0.0% |
| crypto airdrop or wallet drainer | unseen | 35 | 65.7% [48.6%, 80.0%] | 0.0% |
| instant-loan app harassment | unseen | 40 | 62.5% [47.5%, 77.5%] | 22.5% |
| social-media verify or copyright strike | unseen | 24 | 62.5% [41.7%, 79.2%] | 37.5% |
| KYC or ID update expiry | unseen | 40 | 60.0% [45.0%, 75.0%] | 0.0% |
| digital arrest | unseen | 39 | 59.0% [43.6%, 74.4%] | 28.2% |
| FASTag or toll balance | unseen | 38 | 57.9% [42.1%, 73.7%] | 0.0% |
| electricity disconnection | unseen | 22 | 50.0% [27.3%, 72.7%] | 18.2% |
| rental or booking deposit | unseen | 25 | 48.0% [28.0%, 68.0%] | 0.0% |
| e-challan or traffic fine | unseen | 40 | 47.5% [32.5%, 62.5%] | 10.0% |
| fake customer-care helpline | unseen | 24 | 45.8% [29.2%, 66.7%] | 12.5% |
| fake CAPTCHA or paste-command | unseen | 34 | 38.2% [23.5%, 55.9%] | 0.0% |
| QR code scam | unseen | 39 | 30.8% [15.4%, 46.2%] | 0.0% |
| UPI collect or accidental refund | unseen | 24 | 8.3% [0.0%, 20.8%] | 0.0% |

### By language and evasion trick (scams caught at Caution)

en 72.4% (n=771), hinglish 72.3% (n=65), manglish 43.1% (n=58).

emoji_padding 67.1% (n=73), leetspeak 64.3% (n=56), none 71.6% (n=613), obfuscated_link 68.2% (n=44), spacing 73.1% (n=52), split_phrasing 67.9% (n=56).

## Unseen scam types: leave-one-category-out

For each of the 13 types with reference examples, the examples were removed, thresholds recalibrated on dev, and that type measured. Mean caught: **92.7% with its examples → 61.5% without** (wording match alone: 40.0%). The 16 never-seen types average **53.3%**. The red-flag rules can't be left out this way and were written by someone who knew many scam types, so treat the full-engine number as an upper bound.

| Type | With examples | Left out | Left out, wording only |
|---|---|---|---|
| bank safe-account scam | 100.0% | 88.9% | 26.7% |
| blackmail or sextortion | 100.0% | 84.2% | 57.9% |
| family emergency or new-number scam | 97.7% | 22.7% | 13.6% |
| gift-card request from a boss or colleague | 100.0% | 72.0% | 24.0% |
| investment or crypto scam | 88.0% | 32.0% | 32.0% |
| invoice or bank-details change | 79.2% | 33.3% | 20.8% |
| job or advance-fee scam | 100.0% | 78.3% | 69.6% |
| one-time code or password request | 79.5% | 64.1% | 10.3% |
| parcel or delivery fee | 100.0% | 56.0% | 44.0% |
| prize or lottery fee | 100.0% | 94.7% | 68.4% |
| romance scam money request | 82.6% | 47.8% | 52.2% |
| tax or government threat | 82.4% | 73.5% | 44.1% |
| tech support remote-access scam | 95.7% | 52.2% | 56.5% |

## Which signal does the work (each at its own matched ~10% false-alarm rate)

| Score | Caught (Caution) | Never-seen types | False alarms (test) | ROC-AUC |
|---|---|---|---|---|
| similarity signal (wording match + red flags) | 70.1% | 53.3% | 10.6% | 0.863 |
| red-flag rules only | 23.2% | 8.3% | 1.0% | 0.610 |
| wording match only | 68.3% | 53.6% | 9.9% | 0.856 |
| anomaly only | 22.1% | 17.6% | 2.8% | 0.597 |
| all four signals fused | 70.5% | 53.5% | 10.5% | 0.867 |

### With call details

| Setting | Caught (Caution) | False alarms | ROC-AUC |
|---|---|---|---|
| text only | 70.5% | 10.5% | 0.867 |
| text + call details, same for scam and honest | 54.4% | 11.6% | 0.829 |
| text + call details where scams look unusual (**assumption**) | 94.6% | 11.1% | 0.979 |

Call details that carry no information make honest scores noisier and lower detection; they only help if scams really do arrive at odd hours, in bursts, from new senders.

## Errors on the frozen test set (text only)

264 scams missed, 147 honest messages flagged. Full lists with the engine's explanations: `false_negatives_worst.csv`, `false_positives_worst.csv`, `error_groups.csv`.

Highest error rates by group:

- **missed scam**: category=UPI collect or accidental refund 22/24 (92%); category=QR code scam 27/39 (69%); category=fake CAPTCHA or paste-command 21/34 (62%); language=manglish 33/58 (57%); category=fake customer-care helpline 13/24 (54%); category=e-challan or traffic fine 21/40 (52%)
- **false alarm**: category=refund confirmation 26/67 (39%); language=hinglish 20/61 (33%); category=real promotion 15/56 (27%); category=bank transaction alert 18/69 (26%); category=delivery update 50/209 (24%); language=manglish 15/64 (23%)

Worst misses:

- [romance scam money request, manglish] "Subject: Ente chakkare, njan ivide foreign

Ente chakkare, njan ivide foreign il kudungi, account freeze aanu." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call d
- [romance scam money request, manglish] "Hey, Ente chakkare, njan ivide foreign il kudungi, account freeze aanu. Kurachu paisa ayachu tharamo? Thirichu" → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call d
- [romance scam money request, manglish] "Hey, Ente chakkare, njan ivide foreign il kudungi, account freeze aanu. Kurachu paisa ayachu tharamo? Thirichu" → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call d
- [romance scam money request, manglish] "Ente chakkare, njan ivide foreign il kudungi, account freeze aanu. Kurachu paisa ayachu tharamo? Thirichu thar" → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call d
- [one-time code or password request, en] "Hi, Your 4cc0unt upd4t3 is pending. r3ply with the OTP you just received. Thanks! Thanks." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call d

Worst false alarms:

- [OTP message with do-not-share, manglish] "Dear user, 151964 aanu ningalude OTP. Ithu aarumaayi share cheyyaruthu, bank orikkalum OTP chodikkilla. Sent f" → Combined score 0.76; driven by 'similarity' (score 0.75): Message: asks for a one-time cod
- [OTP message with do-not-share, manglish] "Dear user, INV-79747 aanu ningalude OTP. Ithu aarumaayi share cheyyaruthu, bank orikkalum OTP chodikkilla. Sen" → Combined score 0.75; driven by 'similarity' (score 0.74): Message: asks for a one-time cod
- [OTP message with do-not-share, manglish] "Hello, INV-73654 aanu ningalude OTP. Ithu aarumaayi share cheyyaruthu, bank orikkalum OTP chodikkilla. Cheers." → Combined score 0.75; driven by 'similarity' (score 0.74): Message: asks for a one-time cod
- [OTP message with do-not-share, manglish] "Hello, 745390 aanu ningalude OTP. Ithu aarumaayi share cheyyaruthu, bank orikkalum OTP chodikkilla. Cheers." → Combined score 0.75; driven by 'similarity' (score 0.74): Message: asks for a one-time cod
- [OTP message with do-not-share, manglish] "Dear user, 465066 aanu ningalude OTP. Ithu aarumaayi share cheyyaruthu, bank orikkalum OTP chodikkilla. Regard" → Combined score 0.71; driven by 'similarity' (score 0.70): Message: asks for a one-time cod

## Report-once experiment

75 scams the engine missed in fresh batch A (seed 101) were added to a copy of its reference examples, thresholds were recalibrated on dev, and a different fresh batch B (seed 202, 1582 scams, excluding the reported messages' families and near-copies) was measured.

| Variant | Caught before | Caught after | Dev false alarms after |
|---|---|---|---|
| scam reports only | 75.1% | 37.7% [35.3%, 40.1%] | 1.4% |
| scam reports + 63 honest examples | 75.1% | 87.9% [86.4%, 89.5%] | 10.0% |

Scam reports alone backfire: many were Hinglish/Manglish, the honest reference examples are English, so honest messages in those languages start resembling the reports and the threshold must jump. Adding a few honest examples in the same languages turns it into a clear gain.

## Real-world false-alarm check

4827 genuine non-scam texts from the public UCI SMS Spam Collection (UK, 2000s): **16.3% [15.3%, 17.4%] flagged at Caution**, 0.1% [0.0%, 0.3%] at High. Its spam is mostly marketing, not scams; 24.0% of it is flagged.

## Fresh batch (seed 7)

Recall at Caution 67.4% [64.9%, 69.8%], false alarms 11.2% [9.9%, 12.4%] after removing 1942 near-copies. New fills of the same hand-written seeds: a stability check, not a second untouched test set.

## Limits

- Synthetic data written by the same AI that built the engine: shared phrasing habits can flatter results.
- Hinglish and Manglish were written by a non-native writer and may read unnaturally.
- A few honest code messages contain an invoice-style number where the code should be (a generator slip); left in place because the test set is frozen.
- Text only: continuity and precedent have nothing to work with unless account, number or history data are supplied.

## Re-run

```
PYTHONPATH=src python -m eval.run                    # all sections
PYTHONPATH=src python -m eval.run --batch-seed 7     # plus a fresh batch
```
