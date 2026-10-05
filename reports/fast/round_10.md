# Round 10 (synthetic data)

Round file verified against the manifest (sha256 `f8d5dd5186604f3d…`). Candidate before the fix: **fast_r08**. Cut-offs set on dev rounds 01-02: Caution 0.437, High 0.615.

## Test before fix

- Scams caught at Caution or above: **73.3%** [61.7%, 85.0%] of 60 (synthetic data); at High: 1.7%.
- Honest messages flagged at Caution: 0.8% of 120 (synthetic data).

| Scam type | Already in examples? | n | Caught (Caution) | Caught (High) |
|---|---|---|---|---|
| instant-loan harassment | no | 6 | 1/6 | 0/6 |
| FASTag or toll balance | no | 5 | 1/5 | 0/5 |
| KYC or Aadhaar/PAN expiry | no | 4 | 2/4 | 0/4 |
| courier or customs parcel held | yes (parcel or delivery fee) | 7 | 4/7 | 0/7 |
| crypto airdrop or wallet drainer | partly (investment or crypto scam) | 5 | 3/5 | 0/5 |
| task or like-and-earn | partly (job or advance-fee scam) | 10 | 10/10 | 0/10 |
| fake customer-care number | no | 6 | 6/6 | 1/6 |
| social-media verify-your-account DM | no | 5 | 5/5 | 0/5 |
| prize or lottery | yes (prize or lottery fee) | 6 | 6/6 | 0/6 |
| fake CAPTCHA paste-command | no | 6 | 6/6 | 0/6 |

### Missed scams (16)

- [FASTag or toll balance, English, none] "Hi, A reminder that your toll tag account needs a quick re-verification sometime this week. It only takes a minute: [LINK]" → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [FASTag or toll balance, English, none] "Hi, A reminder that your toll tag account needs a quick re-verification sometime this week. It only takes a minute: [LINK] Regards." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [instant-loan harassment, English, none] "Hey, EasyCredit: Pre-approved loan, no documents. Install the app and allow SMS and contacts to receive $2,500." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [crypto airdrop or wallet drainer, English, spacing] "Subject: Dear customer, Congrats, you were  Dear customer, Congrats, you were selected for a t o k e n g i v e a w a y. Just connect your wa" → Combined score 0.14; driven by 'similarity' (score 0.11): Message doesn't resemble known scam scripts
- [FASTag or toll balance, English, none] "Dear customer, A reminder that your toll tag account needs a quick re-verification sometime this week. It only takes a minute: http://secure" → Combined score 0.18; driven by 'similarity' (score 0.14): Message doesn't resemble known scam scripts
- [instant-loan harassment, English, none] "RupeeFast: Get money in 5 minutes. Install the app and allow SMS and contacts to receive $750." → Combined score 0.20; driven by 'similarity' (score 0.17): Message doesn't resemble known scam scripts
- [courier or customs parcel held, English, emoji_padding] "Hey, ParcelHub customs desk: a package in your name needs clearance. Call [PHONE] within 12 hours. ❤️ Sent from my phone" → Combined score 0.20; driven by 'similarity' (score 0.17): Message doesn't resemble known scam scripts
- [KYC or Aadhaar/PAN expiry, English, emoji_padding] "Hi, Last day to link PAN with your account. 🙏 Failure will freeze your savings. ✅ Update here. 👍 Cheers." → Combined score 0.24; driven by 'similarity' (score 0.21): Message doesn't resemble known scam scripts
- [KYC or Aadhaar/PAN expiry, English, leetspeak] "Last day to link PAN w1th your account. Failure w1ll fr33z3 your savings. Update here. Cheers." → Combined score 0.26; driven by 'similarity' (score 0.23): Message doesn't resemble known scam scripts
- [instant-loan harassment, English, spacing] "Hey, Q u i c k C a s h: Pre-approved loan, no documents. Install the app and allow gallery and c o n t a c t s to receive Rs 2,500." → Combined score 0.30; driven by 'similarity' (score 0.27): Message doesn't resemble known scam scripts
- [instant-loan harassment, English, spacing] "R u p e e F a s t: Pre-approved loan, no documents. Install the app and a l l o w SMS and contacts to receive Rs. 99." → Combined score 0.31; driven by 'similarity' (score 0.28): Message doesn't resemble known scam scripts
- [FASTag or toll balance, English, none] "Hello, A reminder that your toll tag account needs a quick re-verification sometime this week. It only takes a minute: http://secure90.test/" → Combined score 0.35; driven by 'similarity' (score 0.33): Message doesn't resemble known scam scripts
- [courier or customs parcel held, English, spacing] "Hi, Expressly customs desk: a package in your name n e e d s c l e a r a n c e. Call [PHONE] today. Thanks." → Combined score 0.39; driven by 'similarity' (score 0.36): Message doesn't resemble known scam scripts
- [courier or customs parcel held, English, emoji_padding] "Hello, Expressly customs desk: a package in your name needs clearance. 💰 Call [PHONE] before it is returned. 😊 Regards." → Combined score 0.39; driven by 'similarity' (score 0.36): Message doesn't resemble known scam scripts
- [crypto airdrop or wallet drainer, English, emoji_padding] "Hey, Congrats, you were selected for a token giveaway. 🎉 Just connect your wallet and approve to receive them. Sent from my phone" → Combined score 0.41; driven by 'similarity' (score 0.39): Message doesn't resemble known scam scripts
- [instant-loan harassment, English, none] "Dear customer, RupeeFast: Pre-approved loan, no documents. Install the app and allow contacts access to receive Rs. 2,500. Regards." → Combined score 0.42; driven by 'similarity' (score 0.39): Message doesn't resemble known scam scripts

### False alarms (1)

- [bank transaction alert, English] "Lotus Bank alert: card ending 7734 used for $2,500. View details in the app. Sent from my phone" → Combined score 0.45; driven by 'similarity' (score 0.43): Message doesn't resemble known scam scripts

## Fix

Added 16 missed scams to the scam examples and 1 false-alarm honest messages to the honest examples → bundle `models\candidate\fast_r10`.

## Gate

| Check | Result |
|---|---|
| all tests pass | pass |
| all 24 named scenarios keep their result | pass |
| dev recall at Caution not lower | pass |
| dev High false alarms not higher | pass |
| real-SMS false alarms at most +2 points over demo-safe | **fail** |

Tests: 109 passed in 2.86s. Scenario failures: none.
Dev recall at Caution 64.2% → 70.8%; dev High false alarms 0.0% → 0.0%; real-SMS false alarms 6.4% (demo-safe 4.4%).

**Result: reverted.** Best candidate is now **fast_r08**.
