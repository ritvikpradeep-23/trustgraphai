# Round 04 (synthetic data)

Round file verified against the manifest (sha256 `9aacf9b1b38937bd…`). Candidate before the fix: **fast_r03**. Cut-offs set on dev rounds 01-02: Caution 0.602, High 0.615.

## Test before fix

- Scams caught at Caution or above: **41.7%** [30.0%, 55.0%] of 60 (synthetic data); at High: 26.7%.
- Honest messages flagged at Caution: 14.2% of 120 (synthetic data).

| Scam type | Already in examples? | n | Caught (Caution) | Caught (High) |
|---|---|---|---|---|
| rental or booking deposit | no | 6 | 0/6 | 0/6 |
| QR-code scam | no | 5 | 0/5 | 0/5 |
| digital arrest | partly (tax or government threat) | 7 | 0/7 | 0/7 |
| wrong-number crypto investment | partly (investment or crypto scam) | 6 | 1/6 | 0/6 |
| AI trading-bot group | partly (investment or crypto scam) | 6 | 1/6 | 0/6 |
| UPI collect-request or refund | no | 7 | 2/7 | 0/7 |
| deepfake CEO video call | no | 7 | 6/7 | 5/7 |
| remote-access support | yes (tech support remote-access scam) | 7 | 6/7 | 6/7 |
| fake e-challan | no | 5 | 5/5 | 5/5 |
| fake job offer with upfront fee | yes (job or advance-fee scam) | 4 | 4/4 | 0/4 |

### Missed scams (35)

- [rental or booking deposit, English, none] "I'm abroad so I can't show the apartment, but pay the first month via the agency link and I'll courier the keys: [LINK]" → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [remote-access support, English, spacing] "Hi, Hi, it's tech support following up on the slow laptop you reported. When you're free, we can c o n n e c t r e m o t e l y and have a lo" → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [rental or booking deposit, English, none] "Dear customer, I'm abroad so I can't show the apartment, but pay the first month via the agency link and I'll courier the keys: http://pay91" → Combined score 0.04; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [QR-code scam, Manglish, none] "Hi, Chetta, njan QR ayachittundu, scan cheythu UPI PIN adichal paisa ningalude account il varum. Thanks." → Combined score 0.07; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [QR-code scam, Manglish, none] "Dear customer, Chetta, njan QR ayachittundu, scan cheythu UPI PIN adichal paisa ningalude account il varum. Cheers." → Combined score 0.07; driven by 'anomaly' (score 0.04): Insufficient data to assess (call duration unknown, time of day unknown, amount unknown, contact frequenc
- [wrong-number crypto investment, English, obfuscated_link] "Dear customer, Hi, is this Asha? Sorry, wrong number. Where are you based? I trade forex and made Rs 2,500 last month, want to see how?" → Combined score 0.09; driven by 'similarity' (score 0.06): Message doesn't resemble known scam scripts
- [QR-code scam, Manglish, none] "Subject: Chetta, njan QR ayachittundu, scan  Chetta, njan QR ayachittundu, scan cheythu UPI PIN adichal paisa ningalude account il varum." → Combined score 0.14; driven by 'similarity' (score 0.11): Message doesn't resemble known scam scripts
- [QR-code scam, Manglish, split_phrasing] "Hello, Chetta, njan qr ayachittundu, scan cheythu UPI PIN adichal paisa ningalude account il varum. Regards." → Combined score 0.15; driven by 'similarity' (score 0.12): Message doesn't resemble known scam scripts
- [QR-code scam, Manglish, none] "Subject: Dear customer, Chetta, njan QR  Dear customer, Chetta, njan QR ayachittundu, scan cheythu UPI PIN adichal paisa ningalude account i" → Combined score 0.17; driven by 'similarity' (score 0.14): Message doesn't resemble known scam scripts
- [digital arrest, English, leetspeak] "This is Officer Mehta from the narcotics bureau. Your bank account was us3d for money laundering. Stay on this call, do not t3ll 4ny0n3, and" → Combined score 0.21; driven by 'similarity' (score 0.18): Message doesn't resemble known scam scripts
- [wrong-number crypto investment, English, obfuscated_link] "Subject: Hi, is this Vikram? Sorry  Hi, is this Vikram? Sorry, wrong number. Funny how these mistakes happen. I trade gold futures and made " → Combined score 0.22; driven by 'similarity' (score 0.19): Message doesn't resemble known scam scripts
- [wrong-number crypto investment, English, leetspeak] "Hi, Hi, is this Mina? Sorry, wrong number. You seem friendly! I tr4d3 digital currency and made $99 l4st month, w4nt to see how?" → Combined score 0.23; driven by 'similarity' (score 0.20): Message doesn't resemble known scam scripts
- [wrong-number crypto investment, English, none] "Dear customer, Hi, is this Hari? Sorry, wrong number. Funny how these mistakes happen. I trade gold futures and made £750 last month, want t" → Combined score 0.30; driven by 'similarity' (score 0.27): Message doesn't resemble known scam scripts
- [wrong-number crypto investment, English, none] "Hey, Hi, is this Asha? Sorry, wrong number. Funny how these mistakes happen. I trade forex and made £500 last month, want to see how? Cheers" → Combined score 0.31; driven by 'similarity' (score 0.28): Message doesn't resemble known scam scripts
- [rental or booking deposit, English, none] "Subject: I'm abroad so I can't  I'm abroad so I can't show the apartment, but pay the first month via the agency link and I'll courier the k" → Combined score 0.34; driven by 'similarity' (score 0.32): Message doesn't resemble known scam scripts
- [deepfake CEO video call, English, spacing] "As we discussed on the video call, the vendor needs paying. Transfer ₹15,000 to the e s c r o w account in the next hour and keep it c o n f" → Combined score 0.36; driven by 'similarity' (score 0.34): Message doesn't resemble known scam scripts
- [UPI collect-request or refund, English, emoji_padding] "Hello, Hi, it's the seller from the marketplace. 👍 My app shows the money didn't go. 🎉 I've sent a request; approve and you'll get it back. " → Combined score 0.39; driven by 'similarity' (score 0.37): Message doesn't resemble known scam scripts
- [UPI collect-request or refund, English, none] "Hey, Hi, it's the seller from the marketplace. My app shows the money didn't go. I've sent a request; approve and you'll get it back." → Combined score 0.39; driven by 'similarity' (score 0.37): Message doesn't resemble known scam scripts
- [AI trading-bot group, Hinglish, none] "AI trading bot se roz profit kamao. Group join karo, admin aapka account khol denge. Minimum Rs 1,200. Regards." → Combined score 0.39; driven by 'similarity' (score 0.37): Message doesn't resemble known scam scripts
- [digital arrest, English, none] "This is Inspector Rao from the customs investigation team. A parcel in your name contained drugs. Stay on this call, do not tell anyone, and" → Combined score 0.44; driven by 'similarity' (score 0.42): Message: asks to keep it secret
- [digital arrest, English, none] "This is Officer Mehta from the customs investigation team. Your SIM card is linked to a fraud case. Stay on this call, do not tell anyone, a" → Combined score 0.45; driven by 'similarity' (score 0.43): Message: asks to keep it secret
- [digital arrest, English, none] "Dear customer, This is Agent Kumar from the customs investigation team. Your SIM card is linked to a fraud case. Stay on this call, do not t" → Combined score 0.45; driven by 'similarity' (score 0.43): Message: asks to keep it secret
- [AI trading-bot group, Hinglish, none] "Hey, AI trading bot se roz profit kamao. Group join karo, admin aapka account khol denge. Minimum Rs. 249. Regards." → Combined score 0.45; driven by 'similarity' (score 0.43): Message doesn't resemble known scam scripts
- [UPI collect-request or refund, English, none] "Hi, it's the seller from the marketplace. My app shows the money didn't go. I've sent a request; approve and you'll get it back. Cheers." → Combined score 0.45; driven by 'similarity' (score 0.43): Message doesn't resemble known scam scripts
- [AI trading-bot group, Hinglish, leetspeak] "Hello, AI trading bot se roz profit k4m40. Group join k4r0, admin aapka account khol denge. M1n1mum Rs. 4,999. Cheers." → Combined score 0.47; driven by 'similarity' (score 0.45): Message doesn't resemble known scam scripts
- [digital arrest, English, none] "This is Officer Mehta from the central investigation agency. Your bank account was used for money laundering. Stay on this call, do not tell" → Combined score 0.47; driven by 'similarity' (score 0.45): Message: asks to keep it secret
- [digital arrest, English, split_phrasing] "this is agent kumar from the narcotics bureau. Your bank account was used for money laundering. Stay on this call, do not tell anyone, and t" → Combined score 0.47; driven by 'similarity' (score 0.45): Message: asks to keep it secret
- [rental or booking deposit, English, emoji_padding] "Hello, I'm abroad so I can't show the apartment, but pay the first month via the agency link and I'll courier the keys: http://pay54.test/ap" → Combined score 0.49; driven by 'similarity' (score 0.47): Message: reads like a known task or like-and-earn script (similarity 0.19)
- [AI trading-bot group, Hinglish, none] "Hi, AI trading bot se roz profit kamao. Group join karo, admin aapka account khol denge. Minimum $2,500. Thanks." → Combined score 0.50; driven by 'similarity' (score 0.48): Message: reads like a known investment or crypto scam script (similarity 0.22)
- [rental or booking deposit, English, none] "I'm abroad so I can't show the apartment, but pay the first month via the agency link and I'll courier the keys: https://pay-info.example.or" → Combined score 0.50; driven by 'similarity' (score 0.48): Message: reads like a known task or like-and-earn script (similarity 0.19)
- [AI trading-bot group, Hinglish, none] "Hi, AI trading bot se roz profit kamao. Group join karo, admin aapka account khol denge. Minimum $750. Cheers." → Combined score 0.51; driven by 'similarity' (score 0.49): Message: reads like a known investment or crypto scam script (similarity 0.23)
- [UPI collect-request or refund, English, leetspeak] "Hi, it's the seller fr0m the marketplace. My app sh0ws the money didn't go. I've sent a request; 4ppr0v3 and you'll get it back. Sent from m" → Combined score 0.54; driven by 'similarity' (score 0.52): Message: reads like a known UPI collect-request or refund script (similarity 0.26)
- [rental or booking deposit, English, split_phrasing] "Hello, I'm abroad so I can't show the apartment, but pay the first month via the agency link and i'll courier the keys: http://claim13.test/" → Combined score 0.54; driven by 'similarity' (score 0.53): Message: reads like a known task or like-and-earn script (similarity 0.20)
- [digital arrest, English, none] "This is Agent Kumar from the customs investigation team. Your SIM card is linked to a fraud case. Stay on this call, do not tell anyone, and" → Combined score 0.56; driven by 'similarity' (score 0.54): Message: asks to keep it secret
- [UPI collect-request or refund, English, none] "Dear customer, Hi, it's the seller from the marketplace. My app shows the money didn't go. I've sent a request; approve and you'll get it ba" → Combined score 0.60; driven by 'similarity' (score 0.59): Message: reads like a known UPI collect-request or refund script (similarity 0.26)

### False alarms (17)

- [real urgent family message, English] "Subject: Dear customer, Urgent but not  Dear customer, Urgent but not serious: my phone is on 2%. Can you ring the plumber? Regards." → Combined score 0.73; driven by 'anomaly' (score 0.56): Unusual: 2 urgency keywords in the message (call duration unknown, time of day unknown, amount unknown, c
- [UPI payment confirmation, English] "Hi, Refund of ₹500 for your cancelled order was credited to your UPI-linked account. Cheers." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known UPI collect-request or refund script (similarity 0.36)
- [UPI payment confirmation, English] "Refund of Rs. 15,000 for your cancelled order was credited to your UPI-linked account. Cheers." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known UPI collect-request or refund script (similarity 0.38)
- [UPI payment confirmation, English] "Subject: Hi, Refund of $15,000 for  Hi, Refund of $15,000 for your cancelled order was credited to your UPI-linked account." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known UPI collect-request or refund script (similarity 0.35)
- [UPI payment confirmation, English] "Hello, Refund of Rs. 15,000 for your cancelled order was credited to your UPI-linked account." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known UPI collect-request or refund script (similarity 0.39)
- [UPI payment confirmation, English] "Refund of Rs 500 for your cancelled order was credited to your UPI-linked account." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known UPI collect-request or refund script (similarity 0.37)
- [UPI payment confirmation, English] "Refund of ₹750 for your cancelled order was credited to your UPI-linked account." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known UPI collect-request or refund script (similarity 0.40)
- [UPI payment confirmation, English] "Dear customer, Refund of Rs 2,500 for your cancelled order was credited to your UPI-linked account. Cheers." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known UPI collect-request or refund script (similarity 0.31)
- [UPI payment confirmation, English] "Refund of $2,500 for your cancelled order was credited to your UPI-linked account." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known UPI collect-request or refund script (similarity 0.37)
- [UPI payment confirmation, English] "Refund of £15,000 for your cancelled order was credited to your UPI-linked account. Sent from my phone" → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known UPI collect-request or refund script (similarity 0.38)
- [UPI payment confirmation, English] "Refund of £4,999 for your cancelled order was credited to your UPI-linked account. Thanks." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known UPI collect-request or refund script (similarity 0.40)
- [UPI payment confirmation, English] "Refund of ₹2,500 for your cancelled order was credited to your UPI-linked account. Cheers." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known UPI collect-request or refund script (similarity 0.36)
- [real promotion, English] "Subject: Dear customer, Hi from Novamart  Dear customer, Hi from Novamart! free delivery on all orders. T&Cs apply. Regards." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known AI trading-bot group script (similarity 0.33)
- [UPI payment confirmation, English] "Hello, Refund of $2,500 for your cancelled order was credited to your UPI-linked account." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known UPI collect-request or refund script (similarity 0.36)
- [UPI payment confirmation, English] "Dear customer, Refund of ₹500 for your cancelled order was credited to your UPI-linked account." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known UPI collect-request or refund script (similarity 0.34)
- [UPI payment confirmation, English] "Refund of Rs 1,200 for your cancelled order was credited to your UPI-linked account. Regards." → Combined score 0.61; driven by 'similarity' (score 0.60): Message: reads like a known UPI collect-request or refund script (similarity 0.42)
- [real promotion, English] "Dear customer, Hi from Zippa! buy one get one free. T&Cs apply. Thanks." → Combined score 0.60; driven by 'similarity' (score 0.59): Message: reads like a known AI trading-bot group script (similarity 0.22)

## Fix

Added 35 missed scams to the scam examples and 17 false-alarm honest messages to the honest examples → bundle `models\candidate\fast_r04`.

## Gate

| Check | Result |
|---|---|
| all tests pass | pass |
| all 24 named scenarios keep their result | pass |
| dev recall at Caution not lower | pass |
| dev High false alarms not higher | pass |
| real-SMS false alarms at most +2 points over demo-safe | pass |

Tests: 109 passed in 6.24s. Scenario failures: none.
Dev recall at Caution 48.3% → 57.5%; dev High false alarms 0.0% → 0.0%; real-SMS false alarms 6.0% (demo-safe 4.4%).

**Result: accepted.** Best candidate is now **fast_r04**.
