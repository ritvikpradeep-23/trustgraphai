# Round 08 (synthetic data)

Round file verified against the manifest (sha256 `8ac0688fed19e0c1…`). Candidate before the fix: **fast_r07**. Cut-offs set on dev rounds 01-02: Caution 0.355, High 0.615.

## Test before fix

- Scams caught at Caution or above: **66.7%** [55.0%, 78.3%] of 60 (synthetic data); at High: 21.7%.
- Honest messages flagged at Caution: 0.0% of 120 (synthetic data).

| Scam type | Already in examples? | n | Caught (Caution) | Caught (High) |
|---|---|---|---|---|
| electricity disconnection | no | 8 | 0/8 | 0/8 |
| FASTag or toll balance | no | 2 | 0/2 | 0/2 |
| instant-loan harassment | no | 7 | 1/7 | 0/7 |
| fake scholarship or exam results | no | 7 | 5/7 | 3/7 |
| social-media verify-your-account DM | no | 4 | 3/4 | 2/4 |
| romance | yes (romance scam money request) | 6 | 5/6 | 0/6 |
| fake CAPTCHA paste-command | no | 7 | 7/7 | 0/7 |
| courier or customs parcel held | yes (parcel or delivery fee) | 8 | 8/8 | 0/8 |
| boss gift-card request | yes (gift-card request from a boss or colleague) | 8 | 8/8 | 8/8 |
| AI voice-clone family emergency | partly (family emergency or new-number scam) | 3 | 3/3 | 0/3 |

### Missed scams (20)

- [electricity disconnection, English, obfuscated_link] "Dear consumer, last month's bill is not updated. To avoid disconnection, pay the pending amount at [LINK]. Thanks." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [electricity disconnection, English, casual_lowercase] "Hi, dear consumer, last month's bill is not updated. to avoid disconnection, pay the pending amount at [link]." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [electricity disconnection, English, none] "Hello, Dear consumer, last month's bill is not updated. To avoid disconnection, pay the pending amount at [LINK]. Regards." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [electricity disconnection, English, emoji_padding] "Dear customer, Dear consumer, your meter is not verified. 🙏 To avoid disconnection, install the support app. ❤️ Regards." → Combined score 0.08; driven by 'similarity' (score 0.04): Message doesn't resemble known scam scripts
- [FASTag or toll balance, English, none] "Dear customer, Toll notice: your tag was charged twice. Claim your refund by entering your card details here." → Combined score 0.08; driven by 'similarity' (score 0.05): Message doesn't resemble known scam scripts
- [instant-loan harassment, English, spacing] "Hi, Your loan is overdue by 1 day. Pay $15,000 now or we will send your p h o t o s to e v e r y o n e in your contact list. Cheers." → Combined score 0.09; driven by 'similarity' (score 0.05): Message doesn't resemble known scam scripts
- [electricity disconnection, English, spacing] "Subject: Hi, Dear consumer, your meter  Hi, Dear consumer, your meter is not v e r i f i e d. To avoid d i s c o n n e c t i o n, install th" → Combined score 0.12; driven by 'similarity' (score 0.09): Message doesn't resemble known scam scripts
- [FASTag or toll balance, English, emoji_padding] "Hey, Toll notice: your tag was charged twice. Claim your refund by entering your card details here. Cheers." → Combined score 0.16; driven by 'similarity' (score 0.12): Message doesn't resemble known scam scripts
- [electricity disconnection, English, none] "Subject: Hi, Dear consumer, last month's  Hi, Dear consumer, last month's bill is not updated. To avoid disconnection, call our officer on [" → Combined score 0.19; driven by 'similarity' (score 0.16): Message doesn't resemble known scam scripts
- [instant-loan harassment, English, emoji_padding] "Dear customer, Your loan is overdue by 1 day. Pay ₹1,200 now or we will send your photos to everyone in your contact list. Sent from my phon" → Combined score 0.22; driven by 'similarity' (score 0.19): Message doesn't resemble known scam scripts
- [instant-loan harassment, English, emoji_padding] "Your loan is overdue by 1 day. 💰 Pay ₹249 now or we will send your photos to everyone in your contact list. 💰 Sent from my phone" → Combined score 0.23; driven by 'similarity' (score 0.20): Message doesn't resemble known scam scripts
- [romance, English, spacing] "Dear customer, dear, I can't wait to meet you. I just need help with the h o s p i t a l bill. C o u l d you send $4,999? Sent from my phone" → Combined score 0.24; driven by 'similarity' (score 0.21): Message doesn't resemble known scam scripts
- [instant-loan harassment, English, spacing] "Hello, Your loan is o v e r d u e by 1 day. Pay $2,500 now or we will send your photos to everyone in your c o n t a c t list. Regards." → Combined score 0.28; driven by 'similarity' (score 0.25): Message doesn't resemble known scam scripts
- [electricity disconnection, English, none] "Hey, Dear consumer, your meter is not verified. To avoid disconnection, pay the pending amount at [LINK]." → Combined score 0.28; driven by 'similarity' (score 0.26): Message doesn't resemble known scam scripts
- [instant-loan harassment, English, none] "Subject: Hey, Your loan is overdue  Hey, Your loan is overdue by 1 day. Pay ₹4,999 now or we will send your photos to everyone in your conta" → Combined score 0.29; driven by 'similarity' (score 0.26): Message doesn't resemble known scam scripts
- [electricity disconnection, English, none] "Hi, Dear consumer, your meter is not verified. To avoid disconnection, pay the pending amount at [LINK]. Thanks." → Combined score 0.29; driven by 'similarity' (score 0.26): Message doesn't resemble known scam scripts
- [social-media verify-your-account DM, English, emoji_padding] "Subject: Hey, Your account has been  Hey, Your account has been flagged for review. Verify now at http://pay15.test/my within 24 hours or it" → Combined score 0.31; driven by 'similarity' (score 0.27): Message doesn't resemble known scam scripts
- [fake scholarship or exam results, English, none] "Subject: Last date to claim your  Last date to claim your education grant is today. Register at https://update.example.com/apguz9 with your " → Combined score 0.32; driven by 'similarity' (score 0.29): Message doesn't resemble known scam scripts
- [fake scholarship or exam results, English, none] "Hello, Last date to claim your education grant is today. Register at [LINK] with your card details. Regards." → Combined score 0.33; driven by 'similarity' (score 0.29): Message doesn't resemble known scam scripts
- [instant-loan harassment, English, none] "Your loan is overdue by 1 day. Pay ₹750 now or we will send your photos to everyone in your contact list. Thanks." → Combined score 0.35; driven by 'similarity' (score 0.33): Message doesn't resemble known scam scripts

### False alarms (0)


## Fix

Added 20 missed scams to the scam examples and 0 false-alarm honest messages to the honest examples → bundle `models\candidate\fast_r08`.

## Gate

| Check | Result |
|---|---|
| all tests pass | pass |
| all 24 named scenarios keep their result | pass |
| dev recall at Caution not lower | pass |
| dev High false alarms not higher | pass |
| real-SMS false alarms at most +2 points over demo-safe | pass |

Tests: 109 passed in 4.14s. Scenario failures: none.
Dev recall at Caution 63.3% → 64.2%; dev High false alarms 0.0% → 0.0%; real-SMS false alarms 3.8% (demo-safe 4.4%).

**Result: accepted.** Best candidate is now **fast_r08**.
