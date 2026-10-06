# Casual honest texts + two red-flag gaps (after the training report)

> Synthetic data except the real-SMS row. Not real-world accuracy.

## Changes
1. **40 short casual everyday texts** added to the built-in honest examples (`similarity/corpus.py`), in English,
   Hinglish and Manglish. They are the same texts as the Track B control in `reports/2026-10-05-training/`.
2. **"storage fee"** added to the upfront-fee red flag.
3. **Asking for "the code"** is now a red flag, e.g. "open the app and share the code with us". It covers
   read/send/tell/give/forward/share + (me/us) + the/that/this/your + code. Exceptions:
   - "share your referral code" (another word sits between)
   - "...with your friends/family"
   - offers like "I'll send the code"

Live cut-offs recalibrated as for every engine change (`models/risk_bands.json`: Caution 0.676, High 0.911,
almost unchanged).

## Before and after (text only, cut-offs calibrated on dev)

| | Before | After |
|---|---|---|
| Frozen test: scams caught at Caution | 76.1% [73.3, 79.0] | 74.0% [71.4, 77.0] |
| Frozen test: honest messages flagged | 8.6% | 8.6% |
| ROC-AUC | 0.896 | 0.901 |
| **Real UK SMS honest texts flagged** | 19.3% | **9.6%** |
| Demo scenarios | 18/18 scams, 6/6 honest Low | 18/18, 6/6 |

**The trade-off:** about 2 points fewer synthetic test scams caught (within the confidence ranges), for half the
false alarms on real people's texts. The real-SMS result motivated the casual texts, so that number is
somewhat optimistic.
