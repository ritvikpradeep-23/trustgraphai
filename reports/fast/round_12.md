# Round 12 (synthetic data)

Round file verified against the manifest (sha256 `c35ca28c7d2febbe…`). Candidate before the fix: **fast_r11**. Cut-offs set on dev rounds 01-02: Caution 0.437, High 0.615.

## Test before fix

- Scams caught at Caution or above: **75.0%** [63.3%, 85.0%] of 60 (synthetic data); at High: 33.3%.
- Honest messages flagged at Caution: 1.7% of 120 (synthetic data).

| Scam type | Already in examples? | n | Caught (Caution) | Caught (High) |
|---|---|---|---|---|
| fake customer-care number | no | 6 | 0/6 | 0/6 |
| deepfake CEO video call | no | 3 | 0/3 | 0/3 |
| fake e-challan | no | 7 | 3/7 | 2/7 |
| wrong-number crypto investment | partly (investment or crypto scam) | 4 | 3/4 | 3/4 |
| task or like-and-earn | partly (job or advance-fee scam) | 5 | 4/5 | 0/5 |
| QR-code scam | no | 6 | 6/6 | 0/6 |
| prize or lottery | yes (prize or lottery fee) | 5 | 5/5 | 0/5 |
| crypto airdrop or wallet drainer | partly (investment or crypto scam) | 8 | 8/8 | 0/8 |
| remote-access support | yes (tech support remote-access scam) | 9 | 9/9 | 8/9 |
| KYC or Aadhaar/PAN expiry | no | 7 | 7/7 | 7/7 |

### Missed scams (15)

- [fake customer-care number, English, leetspeak] "I'm from the official cust0m3r c4r3 t34m. Your complaint is registered; pay ₹99 refundable fee to activate it." → Combined score 0.13; driven by 'similarity' (score 0.10): Message doesn't resemble known scam scripts
- [deepfake CEO video call, English, none] "Dear customer, This is the MD. The call dropped, but as I said on screen, send the funds today, I'm authorising it personally." → Combined score 0.15; driven by 'similarity' (score 0.11): Message doesn't resemble known scam scripts
- [deepfake CEO video call, English, split_phrasing] "This is the MD. The call dropped, but as I said on screen, send the funds today, i'm authorising it personally." → Combined score 0.17; driven by 'similarity' (score 0.13): Message doesn't resemble known scam scripts
- [deepfake CEO video call, English, leetspeak] "Hi, This is the MD. The call dropped, but as I said on scr33n, s3nd the funds today, I'm authorising it personally." → Combined score 0.18; driven by 'similarity' (score 0.14): Message doesn't resemble known scam scripts
- [fake e-challan, English, none] "Dear customer, We noticed an unpaid toll violation linked to your vehicle. A small late fee applies after today. Settle it when you get a mo" → Combined score 0.20; driven by 'similarity' (score 0.16): Message doesn't resemble known scam scripts
- [fake customer-care number, English, split_phrasing] "Subject: Hello, I'm from the official  Hello, I'm from the official customer care team. Your complaint is registered; pay £750 refundable fe" → Combined score 0.21; driven by 'similarity' (score 0.18): Message doesn't resemble known scam scripts
- [fake customer-care number, English, casual_lowercase] "i'm from the official customer care team. your complaint is registered; pay $1,200 refundable fee to activate it. Cheers." → Combined score 0.25; driven by 'similarity' (score 0.22): Message doesn't resemble known scam scripts
- [fake e-challan, English, split_phrasing] "Hi, We noticed an unpaid toll violation linked to your vehicle. A small late fee applies after today. settle it when you get a moment: http:" → Combined score 0.25; driven by 'similarity' (score 0.21): Message doesn't resemble known scam scripts
- [fake customer-care number, English, leetspeak] "I'm fr0m the official customer care team. Your complaint is r3g1st3r3d; pay $99 refundable fee to 4ct1v4t3 it. Cheers." → Combined score 0.26; driven by 'similarity' (score 0.23): Message doesn't resemble known scam scripts
- [fake customer-care number, English, emoji_padding] "Hey, I'm from the official customer care team. Your complaint is registered; pay Rs 500 refundable fee to activate it. 🔔 Regards." → Combined score 0.31; driven by 'similarity' (score 0.28): Message doesn't resemble known scam scripts
- [task or like-and-earn, Hinglish, casual_lowercase] "ghar baithe video like karo aur roz rs. 15,000 kamao. pehle task ke baad thoda recharge karna hoga, phir bada profit. Cheers." → Combined score 0.31; driven by 'similarity' (score 0.29): Message doesn't resemble known scam scripts
- [fake customer-care number, English, none] "Hello, I'm from the official customer care team. Your complaint is registered; pay £1,200 refundable fee to activate it. Sent from my phone" → Combined score 0.33; driven by 'similarity' (score 0.30): Message doesn't resemble known scam scripts
- [fake e-challan, English, emoji_padding] "Hello, We noticed an unpaid toll violation linked to your vehicle. ❤️ A small late fee applies after today. Settle it when you get a moment:" → Combined score 0.38; driven by 'similarity' (score 0.35): Message doesn't resemble known scam scripts
- [fake e-challan, English, split_phrasing] "We noticed an unpaid toll violation linked to your vehicle. a small late fee applies after today. Settle it when you get a moment: my-help.i" → Combined score 0.39; driven by 'similarity' (score 0.36): Message doesn't resemble known scam scripts
- [wrong-number crypto investment, Manglish, leetspeak] "Dear customer, Sorry, wrong number aayi. Ningal enthu ch3yyunnu? Njan crypt0 tr4d1ng cheyyunnu, nalla laabham undu, padippikkatte? Thanks." → Combined score 0.43; driven by 'similarity' (score 0.41): Message doesn't resemble known scam scripts

### False alarms (2)

- [college circular, English] "Hello, Library books are due back before the term ends. Late returns are fined. Cheers." → Combined score 0.45; driven by 'similarity' (score 0.43): Message doesn't resemble known scam scripts
- [college circular, English] "Hi, Library books are due back before the term ends. Late returns are fined. Sent from my phone" → Combined score 0.44; driven by 'similarity' (score 0.42): Message doesn't resemble known scam scripts

## Fix

Added 15 missed scams to the scam examples and 2 false-alarm honest messages to the honest examples → bundle `models\candidate\fast_r12`.

## Gate

| Check | Result |
|---|---|
| all tests pass | pass |
| all 24 named scenarios keep their result | pass |
| dev recall at Caution not lower | pass |
| dev High false alarms not higher | pass |
| real-SMS false alarms at most +2 points over demo-safe | pass |

Tests: 109 passed in 6.25s. Scenario failures: none.
Dev recall at Caution 66.7% → 66.7%; dev High false alarms 0.0% → 0.0%; real-SMS false alarms 3.6% (demo-safe 4.4%).

**Result: accepted.** Best candidate is now **fast_r12**.
