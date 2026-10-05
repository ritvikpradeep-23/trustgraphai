# Round 09 (synthetic data)

Round file verified against the manifest (sha256 `8e0f8f4cbe753153…`). Candidate before the fix: **fast_r08**. Cut-offs set on dev rounds 01-02: Caution 0.437, High 0.615.

## Test before fix

- Scams caught at Caution or above: **68.3%** [56.7%, 80.0%] of 60 (synthetic data); at High: 16.7%.
- Honest messages flagged at Caution: 0.0% of 120 (synthetic data).

| Scam type | Already in examples? | n | Caught (Caution) | Caught (High) |
|---|---|---|---|---|
| AI voice-clone family emergency | partly (family emergency or new-number scam) | 4 | 0/4 | 0/4 |
| electricity disconnection | no | 2 | 0/2 | 0/2 |
| task or like-and-earn | partly (job or advance-fee scam) | 4 | 0/4 | 0/4 |
| fake CAPTCHA paste-command | no | 4 | 1/4 | 0/4 |
| social-media verify-your-account DM | no | 5 | 2/5 | 0/5 |
| FASTag or toll balance | no | 5 | 4/5 | 0/5 |
| KYC or Aadhaar/PAN expiry | no | 6 | 5/6 | 0/6 |
| prize or lottery | yes (prize or lottery fee) | 7 | 6/7 | 3/7 |
| romance | yes (romance scam money request) | 2 | 2/2 | 0/2 |
| courier or customs parcel held | yes (parcel or delivery fee) | 5 | 5/5 | 2/5 |
| instant-loan harassment | no | 4 | 4/4 | 0/4 |
| fake customer-care number | no | 5 | 5/5 | 2/5 |
| boss gift-card request | yes (gift-card request from a boss or colleague) | 1 | 1/1 | 1/1 |
| crypto airdrop or wallet drainer | partly (investment or crypto scam) | 5 | 5/5 | 1/5 |
| fake scholarship or exam results | no | 1 | 1/1 | 1/1 |

### Missed scams (19)

- [task or like-and-earn, English, none] "Subject: Your task balance is frozen  Your task balance is frozen because of a wrong rating. Recharge £2,500 to restore it and get your prof" → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [AI voice-clone family emergency, English, casual_lowercase] "Hello, dad, this is the voice note i promised, i'm stuck at the station without my wallet. send rs. 15,000 to my friend's account, i'll expl" → Combined score 0.13; driven by 'similarity' (score 0.10): Message doesn't resemble known scam scripts
- [social-media verify-your-account DM, English, none] "Dear customer, Your page violated community guidelines. Submit a review form with your login to restore it. Cheers." → Combined score 0.14; driven by 'similarity' (score 0.11): Message doesn't resemble known scam scripts
- [electricity disconnection, English, none] "Dear customer, Hello, our records show a small mismatch on your electricity account. Please give our officer a call when free so it doesn't " → Combined score 0.15; driven by 'similarity' (score 0.12): Message doesn't resemble known scam scripts
- [electricity disconnection, English, emoji_padding] "Hello, our records show a small mismatch on your electricity account. Please give our officer a call when free so it doesn't cause trouble l" → Combined score 0.20; driven by 'similarity' (score 0.17): Message doesn't resemble known scam scripts
- [prize or lottery, English, none] "Hi, Lucky customer! Spin the wheel at https://pay.example.com/243jeh and claim your free smartphone, only delivery charges apply. Regards." → Combined score 0.20; driven by 'similarity' (score 0.17): Message doesn't resemble known scam scripts
- [task or like-and-earn, English, none] "Task 12 done! Your earnings are on hold. Deposit Rs 750 to restore your account and withdraw everything. Cheers." → Combined score 0.20; driven by 'similarity' (score 0.17): Message doesn't resemble known scam scripts
- [AI voice-clone family emergency, English, leetspeak] "Hi, Dad, this is the voice n0t3 I pr0m1s3d, I'm stuck at the station without my wallet. Send £1,200 to my friend's 4cc0unt, I'll explain lat" → Combined score 0.21; driven by 'similarity' (score 0.18): Message doesn't resemble known scam scripts
- [task or like-and-earn, English, split_phrasing] "your task balance is frozen because of a wrong rating. recharge rs. 249 to restore it and get your profit back. Sent from my phone" → Combined score 0.22; driven by 'similarity' (score 0.19): Message doesn't resemble known scam scripts
- [task or like-and-earn, English, leetspeak] "Hi, Task 5 done! Your 34rn1ngs are on hold. Deposit Rs 500 to c0mpl3t3 the merchant task and withdraw 3v3ryth1ng." → Combined score 0.22; driven by 'similarity' (score 0.19): Message doesn't resemble known scam scripts
- [fake CAPTCHA paste-command, English, none] "Hello, Your browser needs a manual update to show this file. Run the copied script to finish the update. Sent from my phone" → Combined score 0.25; driven by 'similarity' (score 0.23): Message doesn't resemble known scam scripts
- [AI voice-clone family emergency, English, emoji_padding] "Dad, this is the voice note I promised, I'm stuck at the station without my wallet. 👍 Send Rs. 😊 4,999 to my friend's account, I'll explain " → Combined score 0.28; driven by 'similarity' (score 0.25): Message doesn't resemble known scam scripts
- [social-media verify-your-account DM, English, none] "Dear customer, Your page violated community guidelines. Submit a review form with your login to restore it. Regards." → Combined score 0.28; driven by 'similarity' (score 0.25): Message doesn't resemble known scam scripts
- [KYC or Aadhaar/PAN expiry, English, none] "Hey, Your wallet KYC is pending. Account will be suspended in 24 hours. Call [PHONE] to complete it. Sent from my phone" → Combined score 0.29; driven by 'similarity' (score 0.26): Message doesn't resemble known scam scripts
- [FASTag or toll balance, English, none] "Hi, FASTag balance low. Recharge now through this link to avoid penalty at the next toll plaza: http://orders94.test/secure Regards." → Combined score 0.30; driven by 'similarity' (score 0.27): Message doesn't resemble known scam scripts
- [fake CAPTCHA paste-command, English, split_phrasing] "Hey, robot check failed. Open your system's run tool and paste the fix we copied, then it will restore your access. Thanks." → Combined score 0.34; driven by 'similarity' (score 0.32): Message doesn't resemble known scam scripts
- [fake CAPTCHA paste-command, English, none] "Subject: Hello, Robot check failed. Open  Hello, Robot check failed. Open your system's run tool and paste the fix we copied, then it will r" → Combined score 0.36; driven by 'similarity' (score 0.33): Message doesn't resemble known scam scripts
- [AI voice-clone family emergency, English, none] "Hey, Dad, this is the voice note I promised, I'm stuck at the station without my wallet. Send Rs. 2,500 to my friend's account, I'll explain" → Combined score 0.41; driven by 'similarity' (score 0.38): Message doesn't resemble known scam scripts
- [social-media verify-your-account DM, English, split_phrasing] "Your page violated community guidelines. Submit a review form with your login to restore it. Regards." → Combined score 0.42; driven by 'similarity' (score 0.39): Message doesn't resemble known scam scripts

### False alarms (0)


## Fix

Added 19 missed scams to the scam examples and 0 false-alarm honest messages to the honest examples → bundle `models\candidate\fast_r09`.

## Gate

| Check | Result |
|---|---|
| all tests pass | pass |
| all 24 named scenarios keep their result | pass |
| dev recall at Caution not lower | **fail** |
| dev High false alarms not higher | pass |
| real-SMS false alarms at most +2 points over demo-safe | pass |

Tests: 109 passed in 4.01s. Scenario failures: none.
Dev recall at Caution 64.2% → 62.5%; dev High false alarms 0.0% → 0.0%; real-SMS false alarms 3.4% (demo-safe 4.4%).

**Result: reverted.** Best candidate is now **fast_r08**.
