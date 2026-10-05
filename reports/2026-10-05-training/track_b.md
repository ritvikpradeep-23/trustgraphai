# Track B: grow the similarity examples (first attempt rejected; retry: adopt with caveats)

> Synthetic data except the real-SMS row. Not real-world accuracy.

Added 433 scam and 416 honest corpus-split messages to the reference examples (564 near-copies dropped, none close
to a dev/test message). Compared on dev at each candidate's own cut-offs (about 10% / 1% of dev honest messages flagged).

| | Current examples | Grown | Grown + normalized text |
|---|---|---|---|
| Dev scams caught at Caution | 70.6% [66.1, 74.8] | **91.4%** [88.7, 94.0] | 86.9% |
| Types the engine had no examples for | 55.1% | 91.5% | 85.0% |
| Dev honest flagged at High | 1.0% | 1.0% | 1.0% |
| ROC-AUC | 0.880 | 0.964 | 0.960 |
| **Real UK SMS honest texts flagged** | 19.3% | **34.3%** | 33.2% |

Novelty (the honest numbers):
- **Leave-one-type-out** (examples rebuilt without each type, mean over 29): 56.8% to **79.1%**.
- **Built without the 16 types, scored on them:** 55.1% to **75.7%**.

Adoption rules for "grown" (chosen over "normalized" on dev recall):
1. Recall up at least 3 points: **yes**.
2. Leave-one-type-out not lower: **yes**.
3. High false alarms not higher: **yes**.
4. Tests: pass.
5. Real-SMS false alarms up at most 2 points: **no, up 15 points**.

The verdict is **reject**. The bundle `models/candidate/similarity_v2/` is kept for reference.

Why real texts get worse (diagnostic, not used to choose anything): two effects.
- **The cut-off falls (0.244 to 0.18).** The added honest examples sit right next to dev's honest messages from the
  same generator, so dev honest messages score lower and the 10% line drops.
- **Real texts score higher even at the old cut-off** (19.3% to 26.8% flagged). Short casual texts land closer to
  the many generator-style scam examples.

## What this means
1. More examples made the wording match much better at recognising scam *types*, including ones held out from its examples.
2. But every new example came from my own generator, and real people's casual texts started looking scam-like.
3. The real-text rule caught a problem the made-up data alone would have hidden.
4. The fix is real honest messages (and ideally real scams) in the examples and in the cut-off calibration, not more generated text.
5. So this is not promoted. The bigger example list stays in `models/candidate/` as evidence.

---

## Retry (after "try again")

Variants were fixed **before** running:
- **Cap:** each scam type and honest message type keeps at most its K most varied corpus messages (K = 5 or 10), so
  generator-style text doesn't swamp the list.
- **Casual texts:** optionally add 40 short casual everyday texts on the honest side (English, Hinglish, Manglish),
  hand-written in `training/track_b.py`. The generated honest messages contain no casual chat at all.

Same rules. Among the passing variants, the one with the highest dev recall wins.

| Variant | Dev scams caught | Real SMS honest flagged | Leave-one-type-out | Verdict |
|---|---|---|---|---|
| Current | 70.6% | 19.3% | 56.8% | |
| 5 per type | 89.2% | 28.4% | 76.6% | reject (rule 5) |
| 5 per type + casual | 89.8% | 16.2% | 76.3% | adopt |
| 10 per type | 90.7% | 29.7% | 74.0% | reject (rule 5) |
| **10 per type + casual** | **91.2%** | 16.7% | 75.2% | **adopt with caveats** (dev is 16 points above leave-one-type-out) |

- **Chosen:** `models/candidate/similarity_v3/` (250 scam + 111 honest corpus messages + 40 casual texts).
- **Novelty check** (built without the 16 types, scored on them): 55.1% to **75.3%**.

### The control that changes the reading

Adding **only the 40 casual texts** to the current examples gives dev recall 71.7% and real-SMS false alarms
**9.6%**. So the real-text improvement comes from the casual texts, not from the extra generated examples. Against
"current + casual" as the baseline, the bigger example list still gains about 19 points of dev recall, but costs
about 7 points of real-SMS false alarms. By the pre-agreed rules (baseline = the current engine) the verdict is
"adopt with caveats". By the fairer baseline it would fail rule 5.

**Honesty notes:**
- The real-SMS result motivated this retry and gated the choice, so its real-SMS numbers are optimistic.
- The casual texts were written after looking at real-SMS false alarms, though none were copied.

## What this means (retry)
1. Capping how many generated examples go in, and adding everyday casual chat as "honest", fixed the real-text problem.
2. Most of the real-text gain comes from the casual chat alone, a cheap change worth making on its own.
3. The bigger example list still catches far more scam types it wasn't built from (leave-one-type-out 57% to 75%).
4. But it flags more real casual texts than "current + casual chat" does, so it's a trade-off, not a free win.
5. Both are packaged. Choosing between them is your call, ideally after testing on some real honest messages.
