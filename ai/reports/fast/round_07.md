# Round 07 (synthetic data)

Round file verified against the manifest (sha256 `f0731dbc65439d9d…`). Candidate before the fix: **fast_r04**. Cut-offs set on dev rounds 01-02: Caution 0.327, High 0.615.

## Test before fix

- Scams caught at Caution or above: **55.0%** [43.3%, 68.3%] of 60 (synthetic data); at High: 35.0%.
- Honest messages flagged at Caution: 0.0% of 120 (synthetic data).

| Scam type | Already in examples? | n | Caught (Caution) | Caught (High) |
|---|---|---|---|---|
| social-media verify-your-account DM | no | 5 | 0/5 | 0/5 |
| fake CAPTCHA paste-command | no | 6 | 0/6 | 0/6 |
| electricity disconnection | no | 2 | 0/2 | 0/2 |
| rental or booking deposit | no | 1 | 0/1 | 0/1 |
| AI voice-clone family emergency | partly (family emergency or new-number scam) | 5 | 1/5 | 0/5 |
| instant-loan harassment | no | 4 | 1/4 | 0/4 |
| romance | yes (romance scam money request) | 3 | 1/3 | 0/3 |
| fake scholarship or exam results | no | 5 | 2/5 | 2/5 |
| AI trading-bot group | partly (investment or crypto scam) | 2 | 1/2 | 0/2 |
| FASTag or toll balance | no | 6 | 6/6 | 5/6 |
| courier or customs parcel held | yes (parcel or delivery fee) | 6 | 6/6 | 1/6 |
| fake job offer with upfront fee | yes (job or advance-fee scam) | 4 | 4/4 | 4/4 |
| boss gift-card request | yes (gift-card request from a boss or colleague) | 5 | 5/5 | 5/5 |
| digital arrest | partly (tax or government threat) | 4 | 4/4 | 4/4 |
| UPI collect-request or refund | no | 2 | 2/2 | 0/2 |

### Missed scams (27)

- [instant-loan harassment, English, emoji_padding] "You took a loan of 3,000 and must repay 6,500 within 7 days. Late fees apply every hour. Cheers." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [instant-loan harassment, English, none] "Hey, You took a loan of 3,000 and must repay 6,500 within 7 days. Late fees apply every hour. Regards." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [fake CAPTCHA paste-command, English, none] "Subject: Hi, Security verification required: complete  Hi, Security verification required: complete the on-screen steps and run the copied c" → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [instant-loan harassment, English, none] "Hey, You took a loan of 3,000 and must repay 6,500 within 7 days. Late fees apply every hour. Thanks." → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [fake CAPTCHA paste-command, English, split_phrasing] "Subject: Dear customer, Security verification required  Dear customer, Security verification required: complete the on-screen steps and run " → Combined score 0.07; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [electricity disconnection, English, none] "Hey, Your smart meter subscription has expired. Renew at help-track.invalid/hyrk5s or the power will stop." → Combined score 0.08; driven by 'similarity' (score 0.04): Message doesn't resemble known scam scripts
- [social-media verify-your-account DM, Manglish, none] "Ningalude account review il aanu. 24 manikkoor il help-secure.invalid/ugj57s il verify cheyyuka, illenkil permanent aayi block aakum. Cheers" → Combined score 0.09; driven by 'similarity' (score 0.06): Message doesn't resemble known scam scripts
- [electricity disconnection, English, split_phrasing] "Dear customer, Your smart meter subscription has expired. renew at http://claim8.test/help or the power will stop. Thanks." → Combined score 0.10; driven by 'similarity' (score 0.07): Message doesn't resemble known scam scripts
- [romance, English, emoji_padding] "Dear customer, Good morning sweetheart, thinking of you. ❤️ Life on the base is lonely. Tell me about your day? Regards." → Combined score 0.11; driven by 'similarity' (score 0.07): Message doesn't resemble known scam scripts
- [romance, English, none] "Dear customer, Good morning sweetheart, thinking of you. Life on the base is lonely. Tell me about your day? Regards." → Combined score 0.11; driven by 'similarity' (score 0.07): Message doesn't resemble known scam scripts
- [fake scholarship or exam results, Manglish, none] "Subject: Dear customer, Ningalkku scholarship kitti  Dear customer, Ningalkku scholarship kitti. Seat urappikkan Rs. 15,000 application fee " → Combined score 0.11; driven by 'similarity' (score 0.08): Message doesn't resemble known scam scripts
- [AI voice-clone family emergency, English, obfuscated_link] "Hi, Mum, it's me, Grace. My phone fell in the river, so I'm on a friend's number. I need Rs. 249 for a hospital deposit, can you send it tod" → Combined score 0.15; driven by 'similarity' (score 0.11): Message doesn't resemble known scam scripts
- [social-media verify-your-account DM, English, none] "Subject: You're eligible for the blue  You're eligible for the blue verification badge! Confirm your login details at http://secure52.test/a" → Combined score 0.16; driven by 'similarity' (score 0.13): Message doesn't resemble known scam scripts
- [AI voice-clone family emergency, English, none] "Hey, it's your nephew. Recording this quickly, I've lost my bag abroad. Can you send something for a ticket home? I'll pay back next week." → Combined score 0.18; driven by 'similarity' (score 0.14): Message doesn't resemble known scam scripts
- [AI voice-clone family emergency, English, split_phrasing] "Hello, hey, it's your nephew. recording this quickly, i've lost my bag abroad. Can you send something for a ticket home? i'll pay back next " → Combined score 0.18; driven by 'similarity' (score 0.14): Message doesn't resemble known scam scripts
- [fake scholarship or exam results, Manglish, none] "Ningalkku scholarship kitti. Seat urappikkan ₹1,200 application fee adakkuka. Thanks." → Combined score 0.20; driven by 'similarity' (score 0.17): Message doesn't resemble known scam scripts
- [fake scholarship or exam results, Manglish, leetspeak] "Ningalkku sch0l4rsh1p kitti. Seat ur4pp1kk4n Rs 4,999 application fee 4d4kkuk4. Cheers." → Combined score 0.22; driven by 'similarity' (score 0.19): Message doesn't resemble known scam scripts
- [social-media verify-your-account DM, English, none] "You're eligible for the blue verification badge! Confirm your login details at http://portal28.test/claim to activate it. Thanks." → Combined score 0.23; driven by 'similarity' (score 0.20): Message doesn't resemble known scam scripts
- [social-media verify-your-account DM, English, split_phrasing] "you're eligible for the blue verification badge! confirm your login details at http://portal26.test/help to activate it. Regards." → Combined score 0.23; driven by 'similarity' (score 0.20): Message doesn't resemble known scam scripts
- [social-media verify-your-account DM, English, none] "Hey, You're eligible for the blue verification badge! Confirm your login details at https://account-orders.example.org/2ewq76 to activate it" → Combined score 0.25; driven by 'similarity' (score 0.22): Message doesn't resemble known scam scripts
- [fake CAPTCHA paste-command, English, none] "Hey, Verify you are human: follow the 3 steps shown and run the command this page has copied for you to continue to the document. Regards." → Combined score 0.25; driven by 'similarity' (score 0.22): Message doesn't resemble known scam scripts
- [fake CAPTCHA paste-command, English, none] "Verify you are human: follow the 3 steps shown and run the command this page has copied for you to continue to the document. Thanks." → Combined score 0.26; driven by 'similarity' (score 0.23): Message doesn't resemble known scam scripts
- [AI trading-bot group, English, none] "Subject: Hi, Our artificial intelligence robot  Hi, Our artificial intelligence robot trades for you 24/7. Members withdraw profit daily. Mi" → Combined score 0.27; driven by 'similarity' (score 0.24): Message doesn't resemble known scam scripts
- [fake CAPTCHA paste-command, English, emoji_padding] "Security verification required: complete the on-screen steps and run the copied command to prove you are not a bot. 📦 Cheers." → Combined score 0.27; driven by 'similarity' (score 0.24): Message doesn't resemble known scam scripts
- [fake CAPTCHA paste-command, English, casual_lowercase] "Hey, verify you are human: follow the 3 steps shown and run the command this page has copied for you to continue to the document." → Combined score 0.29; driven by 'similarity' (score 0.26): Message doesn't resemble known scam scripts
- [rental or booking deposit, English, emoji_padding] "Your holiday villa booking is confirmed once you transfer the security deposit today. The listing site will refund it later." → Combined score 0.29; driven by 'similarity' (score 0.25): Message doesn't resemble known scam scripts
- [AI voice-clone family emergency, English, emoji_padding] "Grandpa, it's me, Hari. 👍 My phone fell in the river, so I'm on a friend's number. ⚠️ I need $4,999 for a hospital deposit, can you send it " → Combined score 0.32; driven by 'similarity' (score 0.28): Message doesn't resemble known scam scripts

### False alarms (0)


## Fix

Added 27 missed scams to the scam examples and 0 false-alarm honest messages to the honest examples → bundle `models\candidate\fast_r07`.

## Gate

| Check | Result |
|---|---|
| all tests pass | pass |
| all 24 named scenarios keep their result | pass |
| dev recall at Caution not lower | pass |
| dev High false alarms not higher | pass |
| real-SMS false alarms at most +2 points over demo-safe | pass |

Tests: 109 passed in 4.37s. Scenario failures: none.
Dev recall at Caution 57.5% → 63.3%; dev High false alarms 0.0% → 0.0%; real-SMS false alarms 5.6% (demo-safe 4.4%).

**Result: accepted.** Best candidate is now **fast_r07**.
