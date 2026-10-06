# What changed since reports/2026-10-05/

> All numbers come from synthetic, AI-written messages except the real-SMS row. They show how the
> engine behaves on this data, not its real-world accuracy.

## The three fixes (similarity signal)

1. **"Never asks" and "Never share your password".** The do-not-share exception only knew the base verb
   ("never ask") and needed a verb after "never". It now covers every verb form and a "never" directly before the ask.
2. **Hinglish/Manglish "don't share".** "share na karein", "mat share karo", "share cheyyaruthu" now count as
   warnings, not asks. "Share na?" (a question) and "don't tell your family, send me the OTP" (a secrecy demand) still count as asks.
3. **Reference examples in Hinglish and Manglish.** 30 honest messages and 26 scam scripts (one per language for
   each of the 13 known scam types). Adding only honest ones made every Hinglish/Manglish message look honest
   (development set: those scams caught fell from 34/80 to 6/80), so both sides were added.
   All new examples are under 0.62 similarity to every dev/test message (leakage limit 0.90).

Live risk bands (`models/risk_bands.json`) were recalibrated the same way as for the previous engine fix.
Demo scenarios: 18/18 scams caught, 6/6 honest controls kept Low.

## Before and after (text only, Caution band)

| | Before | After |
|---|---|---|
| Frozen test: scams caught | 70.5% | **76.1%** |
| Frozen test: honest messages flagged | 10.5% | **8.6%** |
| Known scam types / never-seen types | 92.8% / 53.5% | 95.6% / **61.1%** |
| Hinglish / Manglish scams caught | 72.3% / 43.1% | 84.6% / **79.3%** |
| Leave-one-type-out (known types without their examples) | 61.5% | 71.3% |
| **Fresh batch, never-used seed 11** (cleanest comparison) | 67.2% caught, 11.0% flagged | **72.8%** caught, **9.1%** flagged |
| Report-once, scam reports only | 75.1% → 38.0% | 81.2% → 75.0% (still worse) |
| Report-once, plus honest examples | 75.1% → 87.9% | 81.2% → 91.2% |
| **Real UK SMS, honest texts flagged** | 16.3% | **19.3% (worse)** |

## What got worse, and why

- **Real SMS false alarms rose (16.3% → 19.3%).** At the *same* cut-off the rate is unchanged (15.9% → 15.8%).
  The cut-off is set to flag 10% of the synthetic honest dev messages. Those got easier (no more Hinglish OTP
  false alarms), so the cut-off dropped from 0.289 to 0.244. Real UK texts are a different kind of message, so
  more of them now sit above it. **This is a calibration-data problem:** the cut-off should be set on real honest
  traffic, which is part of the training plan. Not tuned here, to avoid fitting to the real-SMS check.
- **Honest "family is hurt but fine" messages** went from 0% to 32% flagged on the test set (9 English, 9 Manglish
  of 57). They now resemble the new family-emergency scripts slightly, and the lower cut-off catches them.
  The same pattern was visible on the development set. It was left alone rather than patched with one matching example.

The fixes were found by reading the first report's test-set and real-SMS errors, so the "after" numbers on those
two sets are slightly optimistic. The fresh seed-11 batch was never looked at before this comparison.
