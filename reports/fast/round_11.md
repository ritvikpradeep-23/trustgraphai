# Round 11 (synthetic data)

Round file verified against the manifest (sha256 `ae56ee2dfabbb3f9…`). Candidate before the fix: **fast_r08**. Cut-offs set on dev rounds 01-02: Caution 0.437, High 0.615.

## Test before fix

- Scams caught at Caution or above: **58.3%** [45.0%, 71.7%] of 60 (synthetic data); at High: 23.3%.
- Honest messages flagged at Caution: 2.5% of 120 (synthetic data).

| Scam type | Already in examples? | n | Caught (Caution) | Caught (High) |
|---|---|---|---|---|
| social-media verify-your-account DM | no | 2 | 0/2 | 0/2 |
| QR-code scam | no | 6 | 0/6 | 0/6 |
| instant-loan harassment | no | 2 | 0/2 | 0/2 |
| FASTag or toll balance | no | 2 | 0/2 | 0/2 |
| fake customer-care number | no | 3 | 1/3 | 1/3 |
| crypto airdrop or wallet drainer | partly (investment or crypto scam) | 5 | 2/5 | 1/5 |
| task or like-and-earn | partly (job or advance-fee scam) | 4 | 2/4 | 0/4 |
| KYC or Aadhaar/PAN expiry | no | 4 | 2/4 | 2/4 |
| fake e-challan | no | 6 | 4/6 | 2/6 |
| prize or lottery | yes (prize or lottery fee) | 4 | 3/4 | 2/4 |
| remote-access support | yes (tech support remote-access scam) | 7 | 6/7 | 4/7 |
| deepfake CEO video call | no | 6 | 6/6 | 0/6 |
| wrong-number crypto investment | partly (investment or crypto scam) | 3 | 3/3 | 0/3 |
| courier or customs parcel held | yes (parcel or delivery fee) | 2 | 2/2 | 2/2 |
| fake CAPTCHA paste-command | no | 4 | 4/4 | 0/4 |

### Missed scams (25)

- [task or like-and-earn, Manglish, obfuscated_link] "Veettil irunnu video like cheythu divasavum Rs 249 undaakkam. Next task nu munpu cheriya recharge venam." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [task or like-and-earn, Manglish, leetspeak] "Hey, Veettil irunnu v1d30 like ch3ythu divasavum $249 undaakkam. Next task nu munpu cheriya recharge venam. Thanks." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [crypto airdrop or wallet drainer, English, none] "Hey, Exclusive NFT drop! Connect your wallet at info-pay.invalid/xen7ux and verify your balance to receive Rs. 750." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [FASTag or toll balance, English, emoji_padding] "Your vehicle tag has expired. 👍 Renew it today, a fee of Rs 15,000 applies, otherwise you pay a cash penalty. ❤️ Regards." → Combined score 0.16; driven by 'similarity' (score 0.11): Message doesn't resemble known scam scripts
- [crypto airdrop or wallet drainer, English, none] "Hi, Claim your staking rewards now. Link your wallet at my-pay.invalid/35kcrq, the pool closes tonight. Sent from my phone" → Combined score 0.16; driven by 'similarity' (score 0.12): Message doesn't resemble known scam scripts
- [crypto airdrop or wallet drainer, English, leetspeak] "Exclusive NFT drop! Connect your wallet at cl41m-update.1nv4l1d/q88kvy and s1gn the message to receive Rs. 249. Sent from my phone" → Combined score 0.16; driven by 'similarity' (score 0.13): Message doesn't resemble known scam scripts
- [fake customer-care number, Manglish, none] "Customer care il ninnu aanu. Refund nu app download cheythu screen il varunna code parayu. Sent from my phone" → Combined score 0.18; driven by 'similarity' (score 0.15): Message doesn't resemble known scam scripts
- [KYC or Aadhaar/PAN expiry, English, leetspeak] "Hello, Your Aadhaar-l1nk3d KYC has expired. Click orders-app.invalid/a9jhw9 and enter your details and OTP to k33p your 4cc0unt active. Sent" → Combined score 0.21; driven by 'similarity' (score 0.18): Message doesn't resemble known scam scripts
- [QR-code scam, English, split_phrasing] "Dear customer, i'm interested in your dining table. I've sent you a QR code, scan it and enter your pin to receive rs. 15,000." → Combined score 0.23; driven by 'similarity' (score 0.20): Message doesn't resemble known scam scripts
- [QR-code scam, English, leetspeak] "Hi, I'm buy1ng y0ur sofa from the listing. I've sent a QR code, just scan it and enter y0ur UPI PIN to receive the payment." → Combined score 0.24; driven by 'similarity' (score 0.21): Message doesn't resemble known scam scripts
- [fake e-challan, Manglish, none] "Ningalude vandikku oru challan undu. Innu thanne http://info25.test/help il Rs 1,200 adakkuka, illenkil licence suspend aakum. Regards." → Combined score 0.24; driven by 'similarity' (score 0.21): Message doesn't resemble known scam scripts
- [fake customer-care number, Manglish, emoji_padding] "Dear customer, Customer care il ninnu aanu. 🎉 Refund nu app download cheythu screen il varunna code parayu. 📦 Cheers." → Combined score 0.26; driven by 'similarity' (score 0.23): Message doesn't resemble known scam scripts
- [instant-loan harassment, English, leetspeak] "Hi, quick l04ns for students 4v41l4bl3, no cr3d1t check. Just download the app and give the permissions it asks for." → Combined score 0.27; driven by 'similarity' (score 0.24): Message doesn't resemble known scam scripts
- [instant-loan harassment, English, leetspeak] "Hi, quick loans for stud3nts available, no credit ch3ck. Just download the app and give the permissions it 4sks for. Cheers." → Combined score 0.27; driven by 'similarity' (score 0.25): Message doesn't resemble known scam scripts
- [social-media verify-your-account DM, Hinglish, none] "Aapka account review mein hai. 24 ghante mein [LINK] pe verify karo warna permanently band ho jayega." → Combined score 0.28; driven by 'similarity' (score 0.26): Message doesn't resemble known scam scripts
- [QR-code scam, English, none] "Dear customer, Hi, I'm buying your sofa from the listing. I've sent a QR code, just scan it and enter your UPI PIN to receive the payment. S" → Combined score 0.29; driven by 'similarity' (score 0.26): Message doesn't resemble known scam scripts
- [prize or lottery, English, none] "Dear customer, global promotion result: you are a winner of a holiday package. To claim, share your account number before midnight." → Combined score 0.29; driven by 'similarity' (score 0.26): Message doesn't resemble known scam scripts
- [FASTag or toll balance, English, obfuscated_link] "Your vehicle tag has expired. Renew it today, a fee of Rs. 2,500 applies, otherwise you pay a cash penalty." → Combined score 0.32; driven by 'similarity' (score 0.29): Message doesn't resemble known scam scripts
- [fake e-challan, Manglish, none] "Ningalude vandikku oru challan undu. Innu thanne https://claim-account.example.org/6ur6y3 il ₹500 adakkuka, illenkil licence suspend aakum." → Combined score 0.34; driven by 'similarity' (score 0.31): Message doesn't resemble known scam scripts
- [remote-access support, English, none] "Hi, Security alert: your router was hacked. Call [PHONE] and install the support tool. Sent from my phone" → Combined score 0.35; driven by 'similarity' (score 0.33): Message doesn't resemble known scam scripts
- [social-media verify-your-account DM, Hinglish, none] "Aapka account review mein hai. 24 ghante mein info-orders.invalid/vqz6ef pe verify karo warna permanently band ho jayega." → Combined score 0.38; driven by 'similarity' (score 0.35): Message doesn't resemble known scam scripts
- [QR-code scam, English, emoji_padding] "Hi, I'm interested in your fridge. ❤️ I've sent you a QR code, scan it and enter your PIN to receive Rs 249. 🔔 Cheers." → Combined score 0.38; driven by 'similarity' (score 0.36): Message doesn't resemble known scam scripts
- [QR-code scam, English, none] "I'm interested in your fridge. I've sent you a QR code, scan it and enter your PIN to receive Rs 249." → Combined score 0.39; driven by 'similarity' (score 0.36): Message doesn't resemble known scam scripts
- [QR-code scam, English, leetspeak] "Hi, I'm buy1ng y0ur sofa from the listing. I've sent a QR code, just scan it and enter y0ur UPI PIN to receive the payment. Regards." → Combined score 0.42; driven by 'similarity' (score 0.39): Message doesn't resemble known scam scripts
- [KYC or Aadhaar/PAN expiry, English, emoji_padding] "Hi, Your Aadhaar-linked KYC has expired. ✅ Click [LINK] and enter your details and OTP to keep your account active. ✅ Regards." → Combined score 0.43; driven by 'similarity' (score 0.41): Message doesn't resemble known scam scripts

### False alarms (3)

- [delivery update, English] "Subject: Hello, We missed you today  Hello, We missed you today. Your parcel is at the local pickup point, bring ID to collect it. Thanks." → Combined score 0.74; driven by 'anomaly' (score 0.56): Unusual: 2 urgency keywords in the message (call duration unknown, time of day unknown, amount unknown, c
- [college circular, English] "Dear customer, Scholarship applications are open till the 15th. Apply only through the official student portal." → Combined score 0.56; driven by 'similarity' (score 0.54): Message: reads like a known fake scholarship or exam results script (similarity 0.29)
- [government notice, English] "Subject: Transport department: water supply will  Transport department: water supply will pause. Contact your local office with questions." → Combined score 0.46; driven by 'similarity' (score 0.44): Message doesn't resemble known scam scripts

## Fix

Added 25 missed scams to the scam examples and 3 false-alarm honest messages to the honest examples → bundle `models\candidate\fast_r11`.

## Gate

| Check | Result |
|---|---|
| all tests pass | pass |
| all 24 named scenarios keep their result | pass |
| dev recall at Caution not lower | pass |
| dev High false alarms not higher | pass |
| real-SMS false alarms at most +2 points over demo-safe | pass |

Tests: 109 passed in 5.85s. Scenario failures: none.
Dev recall at Caution 64.2% → 66.7%; dev High false alarms 0.0% → 0.0%; real-SMS false alarms 3.8% (demo-safe 4.4%).

**Result: accepted.** Best candidate is now **fast_r11**.
