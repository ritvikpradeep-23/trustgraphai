# Round 05 (synthetic data)

Round file verified against the manifest (sha256 `b5b2161992ffa93f…`). Candidate before the fix: **fast_r04**. Cut-offs set on dev rounds 01-02: Caution 0.327, High 0.615.

## Test before fix

- Scams caught at Caution or above: **76.7%** [66.6%, 86.7%] of 60 (synthetic data); at High: 26.7%.
- Honest messages flagged at Caution: 4.2% of 120 (synthetic data).

| Scam type | Already in examples? | n | Caught (Caution) | Caught (High) |
|---|---|---|---|---|
| electricity disconnection | no | 6 | 2/6 | 0/6 |
| rental or booking deposit | no | 3 | 1/3 | 0/3 |
| fake scholarship or exam results | no | 7 | 3/7 | 0/7 |
| AI trading-bot group | partly (investment or crypto scam) | 4 | 2/4 | 0/4 |
| remote-access support | yes (tech support remote-access scam) | 3 | 2/3 | 0/3 |
| fake job offer with upfront fee | yes (job or advance-fee scam) | 5 | 4/5 | 2/5 |
| boss gift-card request | yes (gift-card request from a boss or colleague) | 6 | 6/6 | 5/6 |
| QR-code scam | no | 3 | 3/3 | 0/3 |
| romance | yes (romance scam money request) | 4 | 4/4 | 0/4 |
| deepfake CEO video call | no | 1 | 1/1 | 0/1 |
| digital arrest | partly (tax or government threat) | 6 | 6/6 | 6/6 |
| fake e-challan | no | 2 | 2/2 | 2/2 |
| UPI collect-request or refund | no | 4 | 4/4 | 0/4 |
| AI voice-clone family emergency | partly (family emergency or new-number scam) | 4 | 4/4 | 1/4 |
| wrong-number crypto investment | partly (investment or crypto scam) | 2 | 2/2 | 0/2 |

### Missed scams (14)

- [fake scholarship or exam results, English, none] "Hi, Your exam results are ready. Download the official result app and pay Rs. 2,500 to unlock your scorecard." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [fake scholarship or exam results, English, split_phrasing] "Hey, your exam results are ready. Download the official result app and pay £500 to unlock your scorecard." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [fake scholarship or exam results, English, leetspeak] "Your exam results are r34dy. Download the official result app and pay Rs 2,500 to unl0ck your sc0r3c4rd. Regards." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [electricity disconnection, Manglish, none] "Ningalude current innu raathri 9 manikku cut cheyyum. Bill update aayilla. Udane [PHONE] il vilikkuka. Regards." → Combined score 0.11; driven by 'similarity' (score 0.07): Message doesn't resemble known scam scripts
- [electricity disconnection, Manglish, none] "Ningalude current innu raathri 9 manikku cut cheyyum. Bill update aayilla. Udane [PHONE] il vilikkuka. Cheers." → Combined score 0.11; driven by 'similarity' (score 0.08): Message doesn't resemble known scam scripts
- [fake scholarship or exam results, English, emoji_padding] "Your exam results are ready. Download the official result app and pay £15,000 to unlock your scorecard. Regards." → Combined score 0.14; driven by 'similarity' (score 0.10): Message doesn't resemble known scam scripts
- [electricity disconnection, Manglish, emoji_padding] "Dear customer, Ningalude current innu raathri 9 manikku cut cheyyum. Bill update aayilla. Udane [PHONE] il vilikkuka. ❤️ Regards." → Combined score 0.15; driven by 'similarity' (score 0.11): Message doesn't resemble known scam scripts
- [fake job offer with upfront fee, English, spacing] "Hello, overseas job opening in a h o t e l. Visa p r o c e s s i n g fee of £750 is required before we book your interview. Thanks." → Combined score 0.15; driven by 'similarity' (score 0.12): Message doesn't resemble known scam scripts
- [electricity disconnection, English, emoji_padding] "Hello, City energy department: your power will be suspended within 2 hours because last month's bill is not updated. 📦 Call [PHONE] or pay a" → Combined score 0.17; driven by 'similarity' (score 0.14): Message doesn't resemble known scam scripts
- [AI trading-bot group, English, none] "Dear customer, Welcome to the AI Quant Signals group! Our trading bot made 300% this quarter. Deposit £99 to get the VIP signals." → Combined score 0.18; driven by 'similarity' (score 0.15): Message doesn't resemble known scam scripts
- [AI trading-bot group, English, none] "Hi, RoboTrade Circle update: the bot closed another winning week. Members in VIP signals earned 40% this month. Message the admin to join. S" → Combined score 0.21; driven by 'similarity' (score 0.18): Message doesn't resemble known scam scripts
- [remote-access support, English, none] "Hello, Your account shows unusual logins. Our engineer will connect to your phone to secure it, accept the screen-share request. Sent from m" → Combined score 0.23; driven by 'similarity' (score 0.20): Message doesn't resemble known scam scripts
- [rental or booking deposit, English, emoji_padding] "To confirm your cab/hotel booking, pay the refundable deposit to this account; you'll get a confirmation code. Sent from my phone" → Combined score 0.28; driven by 'similarity' (score 0.25): Message doesn't resemble known scam scripts
- [rental or booking deposit, English, none] "To confirm your cab/hotel booking, pay the refundable deposit to this account; you'll get a confirmation code." → Combined score 0.31; driven by 'similarity' (score 0.28): Message doesn't resemble known scam scripts

### False alarms (5)

- [real promotion, English] "Dear customer, Thanks for shopping with Streamly. Rate your experience and get 5% off next time. Sent from my phone" → Combined score 0.49; driven by 'similarity' (score 0.47): Message: reads like a known task or like-and-earn script (similarity 0.33)
- [real promotion, English] "Thanks for shopping with Bluefin. Rate your experience and get 5% off next time. Sent from my phone" → Combined score 0.47; driven by 'similarity' (score 0.45): Message doesn't resemble known scam scripts
- [real promotion, English] "Thanks for shopping with Streamly. Rate your experience and get 5% off next time. Sent from my phone" → Combined score 0.44; driven by 'similarity' (score 0.42): Message doesn't resemble known scam scripts
- [appointment reminder, English] "car service confirmed for Friday, 2pm. Call us to reschedule. Regards." → Combined score 0.43; driven by 'similarity' (score 0.40): Message doesn't resemble known scam scripts
- [recruiter outreach, English] "Hey, Hi Asha, we'd like to discuss a design opportunity at Oakridge Partners. No fees are ever charged. Regards." → Combined score 0.36; driven by 'similarity' (score 0.33): Message doesn't resemble known scam scripts

## Fix

Added 14 missed scams to the scam examples and 5 false-alarm honest messages to the honest examples → bundle `models\candidate\fast_r05`.

## Gate

| Check | Result |
|---|---|
| all tests pass | pass |
| all 24 named scenarios keep their result | pass |
| dev recall at Caution not lower | pass |
| dev High false alarms not higher | pass |
| real-SMS false alarms at most +2 points over demo-safe | **fail** |

Tests: 109 passed in 4.81s. Scenario failures: none.
Dev recall at Caution 57.5% → 65.0%; dev High false alarms 0.0% → 0.0%; real-SMS false alarms 10.5% (demo-safe 4.4%).

**Result: reverted.** Best candidate is now **fast_r04**.
