# TrustGraph fast routine: final summary

> **All numbers are on synthetic data** (AI-written messages, fake placeholders), except the real UK SMS false-alarm check. They show how the engine behaves on this data, **not real-world accuracy**.

Frozen final test: rounds 13-14 (120 scams across 25 types, 240 honest messages), verified against the SHA-256 manifest and scored **once** on 2026-10-05 14:57. Never used for fixes or tuning. Each engine uses its own cut-offs, set on dev rounds 01-02 to flag ~10% (Caution) and ~1% (High) of honest messages.

## Before-fix recall on each new round (synthetic data)

Each improvement round was scored **before** the engine learned from it, so this is the curve that shows learning. The bar is scams caught at Caution or above.

```
round 03  #################                         41.7%  accepted (engine: demo-safe)
round 04  #################                         41.7%  accepted (engine: fast_r03)
round 05  ###############################           76.7%  reverted (engine: fast_r04)
round 06  ##############################            75.0%  reverted (engine: fast_r04)
round 07  ######################                    55.0%  accepted (engine: fast_r04)
round 08  ###########################               66.7%  accepted (engine: fast_r07)
round 09  ###########################               68.3%  reverted (engine: fast_r08)
round 10  #############################             73.3%  reverted (engine: fast_r08)
round 11  #######################                   58.3%  accepted (engine: fast_r08)
round 12  ##############################            75.0%  accepted (engine: fast_r11)
```

Rounds 03-04 averaged **41.7%**; rounds 05-12 averaged **68.5%** (synthetic data). The curve is **not smooth**: each round leans on a different window of scam types, so a round heavy in types the engine hasn't learned yet (round 07, 11) dips. After round 05 it stopped rising steadily; the gain came mostly from the first two rounds of learning. 6 of 10 rounds' fixes passed the gate; the rest were refused (real-SMS false alarms or a drop on dev).

## Final test, rounds 13-14 (synthetic data)

| | Demo-safe engine | Best candidate (fast_r12) |
|---|---|---|
| Scams caught at Caution or above | 51.7% [42.5%, 60.9%] | **65.0% [56.7%, 72.5%]** |
| Scams caught at High | 18.3% [11.7%, 25.0%] | 21.7% [15.0%, 29.2%] |
| Honest messages flagged at Caution | 2.1% [0.4%, 4.2%] | 0.0% [0.0%, 0.0%] |
| Honest messages flagged at High | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] |
| ROC-AUC | 0.882 | 0.955 |
| Real UK SMS honest texts flagged (real data) | 4.4% | 3.6% |

Honest messages flagged on this test are well below the ~10% the cut-offs were set for on dev rounds 01-02: this test's honest messages were easier than dev's, so the 0.0% says more about the batch than about the engine.

### Per scam type (caught at Caution, synthetic data)

| Scam type | Engine had examples before? | Demo-safe | Best candidate |
|---|---|---|---|
| instant-loan harassment | no | 3/6 | 0/6 |
| fake e-challan | no | 0/4 | 0/4 |
| AI voice-clone family emergency | partly (family emergency or new-number scam) | 3/3 | 1/3 |
| deepfake CEO video call | no | 5/6 | 3/6 |
| task or like-and-earn | partly (job or advance-fee scam) | 1/4 | 2/4 |
| electricity disconnection | no | 0/4 | 2/4 |
| KYC or Aadhaar/PAN expiry | no | 0/6 | 3/6 |
| fake customer-care number | no | 2/4 | 2/4 |
| rental or booking deposit | no | 0/7 | 4/7 |
| fake CAPTCHA paste-command | no | 0/7 | 4/7 |
| courier or customs parcel held | yes (parcel or delivery fee) | 4/5 | 3/5 |
| digital arrest | partly (tax or government threat) | 4/5 | 3/5 |
| wrong-number crypto investment | partly (investment or crypto scam) | 0/5 | 3/5 |
| UPI collect-request or refund | no | 2/5 | 3/5 |
| fake scholarship or exam results | no | 3/3 | 2/3 |
| QR-code scam | no | 1/3 | 2/3 |
| fake job offer with upfront fee | yes (job or advance-fee scam) | 0/4 | 3/4 |
| AI trading-bot group | partly (investment or crypto scam) | 3/5 | 4/5 |
| remote-access support | yes (tech support remote-access scam) | 7/7 | 7/7 |
| prize or lottery | yes (prize or lottery fee) | 5/5 | 5/5 |
| social-media verify-your-account DM | no | 4/5 | 5/5 |
| romance | yes (romance scam money request) | 4/4 | 4/4 |
| FASTag or toll balance | no | 4/5 | 5/5 |
| boss gift-card request | yes (gift-card request from a boss or colleague) | 4/4 | 4/4 |
| crypto airdrop or wallet drainer | partly (investment or crypto scam) | 3/4 | 4/4 |

By language (best candidate, synthetic data): English 53/86, Hinglish 17/23, Manglish 8/11.

### 10 worst remaining misses (best candidate, with the engine's own explanation)

- [KYC or Aadhaar/PAN expiry, English] "hi, routine reminder: our records show your kyc is due for renewal. you can do it from home in two minutes." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day u
- [task or like-and-earn, English] "Hi, I'm a recruiter for a digital marketing team. Simple online tasks, paid daily. Interested? No fees mentioned until y" → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day u
- [electricity disconnection, Hinglish] "Hi, Aapki bijli aaj raat 9 baje kaat di j a y e g i. P i c h l a bill update nahi hua. Turant [PHONE] pe call karein. Th" → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day u
- [courier or customs parcel held, English] "Subject: Hello, your parcel is held  Hello, your parcel is held at customs. pay the import duty of £4,999 at update-acco" → Combined score 0.06; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day u
- [wrong-number crypto investment, English] "Hey, Hello, are we still meeting for golf on Sunday? 🙏 Oh, wrong number. ❤️ Nice to meet you anyway, I'm in finance. ❤️" → Combined score 0.08; driven by 'similarity' (score 0.05): Message doesn't resemble known scam scripts
- [wrong-number crypto investment, English] "Hi, Hello, are we still meeting for golf on Sunday? 👍 Oh, wrong number. 📦 Nice to meet you anyway, I'm in finance. 👍 Tha" → Combined score 0.09; driven by 'similarity' (score 0.06): Message doesn't resemble known scam scripts
- [electricity disconnection, Hinglish] "Hello, Aapki bijli aaj raat 9 baje kaat di jayegi. Pichla bill update nahi hua. Turant [PHONE] pe call karein. Cheers." → Combined score 0.11; driven by 'similarity' (score 0.07): Message doesn't resemble known scam scripts
- [KYC or Aadhaar/PAN expiry, English] "Dear customer, Hi, routine reminder: our records show your KYC is due for renewal. You can do it from home in two minute" → Combined score 0.13; driven by 'similarity' (score 0.10): Message doesn't resemble known scam scripts
- [fake job offer with upfront fee, English] "Your interview is cleared. Please deposit the refundable laptop security amount before joining on Monday. Regards." → Combined score 0.15; driven by 'similarity' (score 0.12): Message doesn't resemble known scam scripts
- [AI trading-bot group, English] "Dear customer, Join our st0ck tips group led by a famous market professor. Free today, limited seats: pay-secure.1nv4l1d" → Combined score 0.15; driven by 'similarity' (score 0.11): Message doesn't resemble known scam scripts

## What improved

- Learning the missed scams from 6 accepted rounds raised scams caught on the untouched final test from 51.7% to 65.0% (+13.3%, synthetic data), with honest false alarms 2.1% → 0.0%.
- Real-UK-SMS false alarms stayed within 2 points of the demo-safe engine at every accepted round (gate).
- All 24 named demo scenarios kept their result and all tests passed at every accepted round.

## What still fails

- 42 of 120 final-test scams are still missed (synthetic data); the weakest types are at the top of the per-type table.
- Soft scams with no ask at all (a friendly "wrong number", "are you free?") read like honest messages: wording can't catch them; sender history (continuity, precedent) has to.
- **Six scam types got worse** even though the total improved: instant-loan harassment 3/6 → 0/6, AI voice-clone family emergency 3/3 → 1/3, deepfake CEO call 5/6 → 3/6, courier/customs 4/5 → 3/5, digital arrest 4/5 → 3/5, fake scholarship 3/3 → 2/3 (synthetic data). Learning other types' messages moved the cut-offs and the closest matches; with 3-7 messages per type these are small numbers, but the direction is consistent.
- On this final test Hinglish (17/23) and Manglish (8/11) did *not* trail English (53/86) (synthetic data), but they trailed in several improvement rounds, the samples here are small, and the red-flag rules are English wording.
- Eight proposed red-flag rules (`proposed_rules.md`) were not applied, so this test measures the engine without them.

## Five honest bullets for the judges

1. We ran 10 improvement rounds, each on a fresh batch of 180 messages the engine had never seen, scoring each one **before** fixing anything; before-fix catches went from about 42% to about 69% (synthetic data).
2. Every fix had to pass a safety gate: all tests, all 24 demo scenarios, no drop on a fixed development set, and no more than +2 points of false alarms on 4,827 real UK text messages. Four rounds' fixes were refused.
3. On a locked final test (rounds 13-14, used once), the improved engine caught 65.0% of scams vs 51.7% for the starting engine, at 0.0% false alarms on honest messages (synthetic data).
4. All test messages are synthetic, written by the same AI that built the detector, so these numbers flatter it; they are not real-world accuracy. The only real data is the UK SMS false-alarm check.
5. What it can't do yet: catch scams that make no request at all, and learning some scam types made a few others slightly worse (e.g. instant-loan harassment). Real reported scams and real honest messages are the next step.

*Two statements in the generated text were corrected by hand after the run (language comparison; types that got worse). No number was changed.*

## Commands (run these yourself)

```
python -m pytest tests/                                          # all tests
$env:PYTHONPATH="src;."                                          # Windows PowerShell
python scripts/promote_model.py models/candidate/fast_r12       # dry run: shows the comparison
python scripts/promote_model.py models/candidate/fast_r12 --yes # promote (backs up models/ first)
python scripts/promote_model.py --rollback                       # undo a promotion
python run_website.py                                            # start the demo website
```

To run the website on the demo-safe engine instead: `git checkout demo-safe` (the tag; on your computer), start the server, then `git checkout claude/new-session-ftqy5g` to come back. To try the best candidate without promoting it: `$env:TRUSTGRAPH_MODEL_DIR="models/candidate/fast_r12"` and then start the server.
