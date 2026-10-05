# Round 06 (synthetic data)

Round file verified against the manifest (sha256 `67cc3aeab9217287…`). Candidate before the fix: **fast_r04**. Cut-offs set on dev rounds 01-02: Caution 0.327, High 0.615.

## Test before fix

- Scams caught at Caution or above: **75.0%** [63.3%, 85.0%] of 60 (synthetic data); at High: 25.0%.
- Honest messages flagged at Caution: 12.5% of 120 (synthetic data).

| Scam type | Already in examples? | n | Caught (Caution) | Caught (High) |
|---|---|---|---|---|
| boss gift-card request | yes (gift-card request from a boss or colleague) | 6 | 0/6 | 0/6 |
| rental or booking deposit | no | 8 | 5/8 | 0/8 |
| UPI collect-request or refund | no | 6 | 4/6 | 0/6 |
| romance | yes (romance scam money request) | 5 | 4/5 | 0/5 |
| electricity disconnection | no | 6 | 5/6 | 0/6 |
| fake scholarship or exam results | no | 7 | 6/7 | 0/7 |
| AI trading-bot group | partly (investment or crypto scam) | 7 | 6/7 | 0/7 |
| AI voice-clone family emergency | partly (family emergency or new-number scam) | 8 | 8/8 | 8/8 |
| digital arrest | partly (tax or government threat) | 5 | 5/5 | 5/5 |
| fake job offer with upfront fee | yes (job or advance-fee scam) | 2 | 2/2 | 2/2 |

### Missed scams (15)

- [UPI collect-request or refund, English, none] "Your refund of $15,000 is ready. Accept the payment request in your UPI app and enter the PIN to receive it." → Combined score 0.09; driven by 'similarity' (score 0.05): Message doesn't resemble known scam scripts
- [fake scholarship or exam results, English, leetspeak] "Hey, C0ngr4tul4t10ns, you qualified for the national merit scholarship of $2,500. Pay the 4ppl1c4t10n fee to c0nf1rm your seat. Regards." → Combined score 0.10; driven by 'similarity' (score 0.07): Message doesn't resemble known scam scripts
- [boss gift-card request, English, leetspeak] "Are you fr33? I need you to handle s0m3th1ng for me discreetly t0d4y. Sent from my phone" → Combined score 0.10; driven by 'similarity' (score 0.07): Message doesn't resemble known scam scripts
- [electricity disconnection, English, none] "Dear customer, Electricity board: please download the support app so our officer can update your meter remotely. Sent from my phone" → Combined score 0.11; driven by 'similarity' (score 0.07): Message doesn't resemble known scam scripts
- [rental or booking deposit, English, obfuscated_link] "Subject: Hi, Hi, saw you liked  Hi, Hi, saw you liked the apartment. I'm out of town for work, but if you send a small holding deposit I'll " → Combined score 0.11; driven by 'similarity' (score 0.08): Message doesn't resemble known scam scripts
- [rental or booking deposit, English, none] "Hi, saw you liked the apartment. I'm out of town for work, but if you send a small holding deposit I'll reserve it for you. Sent from my pho" → Combined score 0.13; driven by 'similarity' (score 0.09): Message doesn't resemble known scam scripts
- [rental or booking deposit, English, none] "Subject: Hi, saw you liked the  Hi, saw you liked the apartment. I'm out of town for work, but if you send a small holding deposit I'll rese" → Combined score 0.15; driven by 'similarity' (score 0.12): Message doesn't resemble known scam scripts
- [boss gift-card request, English, none] "Dear customer, Are you free? I need you to handle something for me discreetly today." → Combined score 0.18; driven by 'similarity' (score 0.13): Message doesn't resemble known scam scripts
- [romance, English, leetspeak] "Dear customer, I'm s3nd1ng you a p4rc3l with gifts and some cash, you just need to pay the d3l1v3ry charge when they contact you." → Combined score 0.18; driven by 'similarity' (score 0.15): Message doesn't resemble known scam scripts
- [UPI collect-request or refund, English, leetspeak] "Dear customer, Your r3fund of £2,500 is ready. Accept the p4ym3nt request in y0ur UPI app and enter the PIN to receive it." → Combined score 0.22; driven by 'similarity' (score 0.19): Message doesn't resemble known scam scripts
- [AI trading-bot group, English, none] "Dear customer, Welcome to Smart Signals VIP! Our AI bot returned 300% this quarter. Deposit Rs 15,000 to unlock premium access." → Combined score 0.26; driven by 'similarity' (score 0.23): Message doesn't resemble known scam scripts
- [boss gift-card request, English, split_phrasing] "Hello, Are you free? I need you to handle something for me discreetly today." → Combined score 0.27; driven by 'similarity' (score 0.24): Message doesn't resemble known scam scripts
- [boss gift-card request, English, obfuscated_link] "Are you free? I need you to handle something for me discreetly today. Thanks." → Combined score 0.27; driven by 'similarity' (score 0.24): Message doesn't resemble known scam scripts
- [boss gift-card request, English, obfuscated_link] "Hey, Are you free? I need you to handle something for me discreetly today." → Combined score 0.27; driven by 'similarity' (score 0.24): Message doesn't resemble known scam scripts
- [boss gift-card request, English, none] "Are you free? I need you to handle something for me discreetly today." → Combined score 0.28; driven by 'similarity' (score 0.24): Message doesn't resemble known scam scripts

### False alarms (15)

- [work message with deadline, English] "Subject: Hello, Urgent: payroll closes tomorrow  Hello, Urgent: payroll closes tomorrow, please submit your timesheet tonight. Sent from my " → Combined score 0.88; driven by 'anomaly' (score 0.88): Unusual: 3 urgency keywords in the message (call duration unknown, time of day unknown, amount unknown, c
- [recruiter outreach, English] "Hey, Hi Leena, I saw your profile and think you'd fit a backend role at our company. Open to a quick call this week? Cheers." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known fake customer-care number script (similarity 0.23)
- [work message with deadline, English] "Hi, Urgent: payroll closes tomorrow, please submit your timesheet tonight. Cheers." → Combined score 0.60; driven by 'anomaly' (score 0.56): Unusual: 2 urgency keywords in the message (call duration unknown, time of day unknown, amount unknown, c
- [work message with deadline, English] "Urgent: payroll closes tomorrow, please submit your timesheet tonight. 🔔 Sent from my phone" → Combined score 0.59; driven by 'anomaly' (score 0.56): Unusual: 2 urgency keywords in the message (call duration unknown, time of day unknown, amount unknown, c
- [work message with deadline, English] "Hello, Urgent: payroll closes tomorrow, please submit your timesheet tonight. Cheers." → Combined score 0.56; driven by 'anomaly' (score 0.56): Unusual: 2 urgency keywords in the message (call duration unknown, time of day unknown, amount unknown, c
- [work message with deadline, English] "Hi, Urgent: payroll closes tomorrow, please submit your timesheet tonight. Thanks." → Combined score 0.56; driven by 'anomaly' (score 0.56): Unusual: 2 urgency keywords in the message (call duration unknown, time of day unknown, amount unknown, c
- [recruiter outreach, English] "Hi Divya, I saw your profile and think you'd fit a backend role at our company. Open to a quick call this week?" → Combined score 0.49; driven by 'similarity' (score 0.48): Message: reads like a known fake customer-care number script (similarity 0.21)
- [recruiter outreach, English] "Hello, Hi Asha, I saw your profile and think you'd fit a backend role at our company. Open to a quick call this week?" → Combined score 0.49; driven by 'similarity' (score 0.47): Message: reads like a known fake customer-care number script (similarity 0.20)
- [recruiter outreach, English] "Hello, Hi Mina, I saw your profile and think you'd fit a backend role at our company. Open to a quick call this week? Thanks." → Combined score 0.48; driven by 'similarity' (score 0.46): Message: reads like a known fake customer-care number script (similarity 0.19)
- [recruiter outreach, English] "Hi Neha, I saw your profile and think you'd fit a backend role at our company. Open to a quick call this week? Regards." → Combined score 0.47; driven by 'similarity' (score 0.45): Message: reads like a known fake customer-care number script (similarity 0.20)
- [recruiter outreach, English] "Hi, hi mina, i saw your profile and think you'd fit a backend role at our company. open to a quick call this week?" → Combined score 0.47; driven by 'similarity' (score 0.45): Message: reads like a known fake customer-care number script (similarity 0.19)
- [recruiter outreach, English] "hi vikram, i saw your profile and think you'd fit a backend role at our company. open to a quick call this week?" → Combined score 0.46; driven by 'similarity' (score 0.44): Message doesn't resemble known scam scripts
- [recruiter outreach, English] "Hey, Hi Divya, I saw your profile and think you'd fit a backend role at our company. Open to a quick call this week? Thanks." → Combined score 0.45; driven by 'similarity' (score 0.43): Message doesn't resemble known scam scripts
- [recruiter outreach, English] "Hey, Hi Mina, I saw your profile and think you'd fit a backend role at our company. Open to a quick call this week? Regards." → Combined score 0.43; driven by 'similarity' (score 0.41): Message doesn't resemble known scam scripts
- [recruiter outreach, English] "Subject: Hello, Hi Omar, I saw  Hello, Hi Omar, I saw your profile and think you'd fit a backend role at our company. Open to a quick call t" → Combined score 0.43; driven by 'similarity' (score 0.41): Message doesn't resemble known scam scripts

## Fix

Added 15 missed scams to the scam examples and 15 false-alarm honest messages to the honest examples → bundle `models\candidate\fast_r06`.

## Gate

| Check | Result |
|---|---|
| all tests pass | pass |
| all 24 named scenarios keep their result | pass |
| dev recall at Caution not lower | **fail** |
| dev High false alarms not higher | pass |
| real-SMS false alarms at most +2 points over demo-safe | pass |

Tests: 109 passed in 6.17s. Scenario failures: none.
Dev recall at Caution 57.5% → 54.2%; dev High false alarms 0.0% → 0.0%; real-SMS false alarms 2.9% (demo-safe 4.4%).

**Result: reverted.** Best candidate is now **fast_r04**.
