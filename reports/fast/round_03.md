# Round 03 (synthetic data)

Round file verified against the manifest (sha256 `6cedd917b2303d89…`). Candidate before the fix: **demo-safe**. Cut-offs set on dev rounds 01-02: Caution 0.356, High 0.615.

## Test before fix

- Scams caught at Caution or above: **41.7%** [30.0%, 53.3%] of 60 (synthetic data); at High: 3.3%.
- Honest messages flagged at Caution: 0.0% of 120 (synthetic data).

| Scam type | Already in examples? | n | Caught (Caution) | Caught (High) |
|---|---|---|---|---|
| rental or booking deposit | no | 6 | 0/6 | 0/6 |
| fake customer-care number | no | 2 | 0/2 | 0/2 |
| UPI collect-request or refund | no | 4 | 0/4 | 0/4 |
| task or like-and-earn | partly (job or advance-fee scam) | 3 | 0/3 | 0/3 |
| deepfake CEO video call | no | 4 | 0/4 | 0/4 |
| wrong-number crypto investment | partly (investment or crypto scam) | 5 | 1/5 | 0/5 |
| fake e-challan | no | 4 | 1/4 | 0/4 |
| AI trading-bot group | partly (investment or crypto scam) | 7 | 3/7 | 0/7 |
| crypto airdrop or wallet drainer | partly (investment or crypto scam) | 2 | 1/2 | 0/2 |
| KYC or Aadhaar/PAN expiry | no | 2 | 1/2 | 0/2 |
| digital arrest | partly (tax or government threat) | 5 | 3/5 | 0/5 |
| QR-code scam | no | 4 | 3/4 | 0/4 |
| remote-access support | yes (tech support remote-access scam) | 4 | 4/4 | 0/4 |
| prize or lottery | yes (prize or lottery fee) | 2 | 2/2 | 0/2 |
| fake job offer with upfront fee | yes (job or advance-fee scam) | 6 | 6/6 | 2/6 |

### Missed scams (35)

- [rental or booking deposit, English, none] "Hi, Great, the flat is available for your dates. To hold it, send the deposit of $4,999 now; I have other interested tenants. Thanks." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [wrong-number crypto investment, English, none] "Oops, sent to the wrong person. Since we're chatting, my uncle taught me a trading method that made me Rs. 1,200 last month. Sent from my ph" → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [deepfake CEO video call, English, emoji_padding] "Join the quick video briefing. Afterwards process the payment to the new supplier, the board has already approved it." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [wrong-number crypto investment, English, obfuscated_link] "Hi, Oops, sent to the wrong person. Since we're chatting, my uncle taught me a trading method that made me ₹1,200 last month." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [rental or booking deposit, English, none] "Hello, Great, the flat is available for your dates. To hold it, send the deposit of $4,999 now; I have other interested tenants. Thanks." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [rental or booking deposit, English, none] "Hey, Thanks for your interest in the room. The landlord asks for a token advance to block it before the weekend. Thanks." → Combined score 0.06; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [wrong-number crypto investment, English, none] "Where are you based? My mentor's gold futures platform is giving steady daily profit. Start with just Rs. 249, I'll send the link. Cheers." → Combined score 0.06; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [wrong-number crypto investment, English, none] "Where are you based? My mentor's gold futures platform is giving steady daily profit. Start with just $2,500, I'll send the link. Regards." → Combined score 0.06; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [UPI collect-request or refund, English, spacing] "C a s h b a c k alert: approve the i n c o m i n g request to credit Rs 4,999 to your account." → Combined score 0.07; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [rental or booking deposit, English, none] "Thanks for your interest in the room. The landlord asks for a token advance to block it before the weekend." → Combined score 0.10; driven by 'similarity' (score 0.07): Message doesn't resemble known scam scripts
- [rental or booking deposit, English, obfuscated_link] "Hello, Thanks for your interest in the room. The landlord asks for a token advance to block it before the weekend. Cheers." → Combined score 0.11; driven by 'similarity' (score 0.07): Message doesn't resemble known scam scripts
- [UPI collect-request or refund, English, none] "Hey, Cashback team sent you a request for ₹15,000. The order was cancelled. Approve it with your UPI PIN to credit your cashback. Regards." → Combined score 0.11; driven by 'similarity' (score 0.07): Message doesn't resemble known scam scripts
- [deepfake CEO video call, English, obfuscated_link] "Hello, Join the quick video briefing. Afterwards process the payment to the new supplier, the board has already approved it. Thanks." → Combined score 0.12; driven by 'similarity' (score 0.08): Message doesn't resemble known scam scripts
- [rental or booking deposit, English, obfuscated_link] "Hi, Thanks for your interest in the room. The landlord asks for a token advance to block it before the weekend. Sent from my phone" → Combined score 0.13; driven by 'similarity' (score 0.10): Message doesn't resemble known scam scripts
- [UPI collect-request or refund, English, none] "Hi, Cashback alert: approve the incoming request to credit Rs. 4,999 to your account. Sent from my phone" → Combined score 0.13; driven by 'similarity' (score 0.10): Message doesn't resemble known scam scripts
- [AI trading-bot group, English, spacing] "Dear customer, Hi, you were a d d e d to our learning community for investors. No pressure, we share market lessons and a smart bot's p i c " → Combined score 0.15; driven by 'similarity' (score 0.12): Message doesn't resemble known scam scripts
- [task or like-and-earn, English, obfuscated_link] "Part-time job: rate hotels online and earn commission. No experience needed. Join our group: http://pay14 dot test/update Sent from my phone" → Combined score 0.15; driven by 'similarity' (score 0.12): Message doesn't resemble known scam scripts
- [deepfake CEO video call, English, none] "Hi, You'll get a short video call from me now, don't worry it's really me. I need an urgent wire transfer handled quietly before the deal le" → Combined score 0.16; driven by 'similarity' (score 0.11): Message doesn't resemble known scam scripts
- [deepfake CEO video call, English, casual_lowercase] "you'll get a short video call from me now, don't worry it's really me. i need an urgent wire transfer handled quietly before the deal leaks." → Combined score 0.16; driven by 'similarity' (score 0.11): Message doesn't resemble known scam scripts
- [fake e-challan, English, emoji_padding] "Hello, Hi, a traffic camera recorded your vehicle without a helmet. View and settle the challan here: [LINK] Sent from my phone" → Combined score 0.16; driven by 'similarity' (score 0.12): Message doesn't resemble known scam scripts
- [fake e-challan, English, emoji_padding] "Hi, Hi, a traffic camera recorded your vehicle without a helmet. View and settle the challan here: https://account.example.com/3stbt3 Sent f" → Combined score 0.16; driven by 'similarity' (score 0.13): Message doesn't resemble known scam scripts
- [AI trading-bot group, English, none] "Dear customer, Hi, you were added to our learning community for investors. No pressure, we share market lessons and a smart bot's picks ever" → Combined score 0.16; driven by 'similarity' (score 0.13): Message doesn't resemble known scam scripts
- [UPI collect-request or refund, English, obfuscated_link] "Refund desk sent you a request for ₹4,999. The order was cancelled. Approve it with your UPI PIN to receive the money. Regards." → Combined score 0.16; driven by 'similarity' (score 0.13): Message doesn't resemble known scam scripts
- [AI trading-bot group, English, obfuscated_link] "Hey, Hi, you were added to our learning community for investors. No pressure, we share market lessons and a smart bot's picks every morning." → Combined score 0.17; driven by 'similarity' (score 0.13): Message doesn't resemble known scam scripts
- [AI trading-bot group, English, none] "Hi, Hi, you were added to our learning community for investors. No pressure, we share market lessons and a smart bot's picks every morning." → Combined score 0.17; driven by 'similarity' (score 0.13): Message doesn't resemble known scam scripts
- [task or like-and-earn, English, none] "Dear customer, Part-time job: rate hotels online and earn commission. No experience needed. Join our group: https://claim-help.example.org/j" → Combined score 0.21; driven by 'similarity' (score 0.18): Message doesn't resemble known scam scripts
- [QR-code scam, Hinglish, leetspeak] "Bhaiya maine QR bheja hai, scan k4rk3 UPI PIN daal do, paise aapke 4cc0unt mein aa j4y3ng3. Regards." → Combined score 0.24; driven by 'similarity' (score 0.21): Message doesn't resemble known scam scripts
- [crypto airdrop or wallet drainer, English, spacing] "To restore your wallet, confirm your p r i v a t e key with our support a g e n t. Only the first 500 wallets qualify." → Combined score 0.24; driven by 'similarity' (score 0.21): Message doesn't resemble known scam scripts
- [fake customer-care number, English, none] "We saw your post about the failed payment. Our support team can help, call [PHONE] and keep your banking app open. Cheers." → Combined score 0.28; driven by 'similarity' (score 0.25): Message doesn't resemble known scam scripts
- [fake customer-care number, English, none] "We saw your post about the failed payment. Our support team can help, call [PHONE] and keep your banking app open." → Combined score 0.28; driven by 'similarity' (score 0.26): Message doesn't resemble known scam scripts
- [task or like-and-earn, English, none] "Part-time job: rate hotels online and earn commission. No experience needed. Join our group: http://track43.test/app" → Combined score 0.29; driven by 'similarity' (score 0.26): Message doesn't resemble known scam scripts
- [digital arrest, Hinglish, emoji_padding] "Hello, Main CBI officer bol raha hoon. Aapke naam pe case darj hai. 💰 Video call band mat karna, warna turant giraftari hogi. Kisi ko kuch m" → Combined score 0.30; driven by 'similarity' (score 0.28): Message doesn't resemble known scam scripts
- [digital arrest, Hinglish, none] "Main CBI officer bol raha hoon. Aapke naam pe case darj hai. Video call band mat karna, warna turant giraftari hogi. Kisi ko kuch mat batana" → Combined score 0.31; driven by 'similarity' (score 0.28): Message doesn't resemble known scam scripts
- [KYC or Aadhaar/PAN expiry, English, spacing] "Dear customer, Account services: your A a d h a a r KYC is incomplete. Update at app-my.invalid/j4gcdb within 24 h o u r s or your account w" → Combined score 0.31; driven by 'similarity' (score 0.29): Message doesn't resemble known scam scripts
- [fake e-challan, Hinglish, none] "Hello, Aapki gaadi ka challan pending hai. Aaj hi https://my.example.com/uhpyh2 pe $15,000 bharein warna licence block ho jayega. Cheers." → Combined score 0.34; driven by 'similarity' (score 0.31): Message doesn't resemble known scam scripts

### False alarms (0)


## Fix

Added 35 missed scams to the scam examples and 0 false-alarm honest messages to the honest examples → bundle `models\candidate\fast_r03`.

## Gate

| Check | Result |
|---|---|
| all tests pass | pass |
| all 24 named scenarios keep their result | pass |
| dev recall at Caution not lower | pass |
| dev High false alarms not higher | pass |
| real-SMS false alarms at most +2 points over demo-safe | pass |

Tests: 109 passed in 5.01s. Scenario failures: none.
Dev recall at Caution 48.3% → 48.3%; dev High false alarms 0.0% → 0.0%; real-SMS false alarms 1.1% (demo-safe 4.4%).

**Result: accepted.** Best candidate is now **fast_r03**.
