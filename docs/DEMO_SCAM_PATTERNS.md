# Judge demo: 300 messages + naturally varied similarity scores

300 distinct synthetic scam messages are stored in PostgreSQL: the original 36 authored examples listed here plus 264 redacted ScamShield messages listed in `SCAMSHIELD_SAMPLE.md`. They illustrate common categories, not verified real-world incidents. Links use reserved .invalid domains. See `data/SCAMSHIELD_NOTICE.md` for source, license, uniqueness filtering, and limitations.

Open http://127.0.0.1:8001/app/analyze. For natural score variation, use the 13 paraphrases below: they are NOT stored as exact patterns. Results range from 72.3% to 96%. Exact normalized copies correctly return 100% text similarity. No scores are randomized or capped.

These scores are word/sequence similarity, not fraud probability. This is a seeded demonstration, not a real-world accuracy benchmark. No known match does not prove safety. Checks are not automatically saved. The service is unauthenticated: keep it private/local.

## Copy-paste paraphrases for the judges

### 1. KYC / OTP theft — measured 96% similarity

```text
Your KYC verification has expired and your bank account will be blocked today. Update your PAN details at https://kyc-demo.invalid and share the OTP to keep your account active.
```

### 2. Bank account suspension — measured 82% similarity

```text
Attention customer, your Lotus Bank account is suspended. Verify your password and card PIN at https://bank-demo.invalid before tomorrow or your account will be permanently closed.
```

### 3. Courier fee phishing — measured 94% similarity

```text
Your package is currently held at customs. Pay the clearance fee of Rs 49 at https://parcel-demo.invalid within 12 hours or it will be returned to the sender.
```

### 4. Lottery advance fee — measured 87% similarity

```text
Congratulations! Your number won Rs 25 lakh in our lucky draw. First pay a processing charge of Rs 1500 to release your prize money.
```

### 5. Job registration fee — measured 94% similarity

```text
You are selected for a work from home data entry job paying Rs 35000 per month. Pay the registration fee of Rs 999 today to receive your offer letter.
```

### 6. Electricity disconnection — measured 96% similarity

```text
Dear consumer, your electricity will be disconnected tonight at 10 pm because your bill is not updated. Transfer Rs 500 immediately to our officer to stop disconnection.
```

### 7. Verification code takeover — measured 82% similarity

```text
Hi, I accidentally sent a verification code to your phone. Please forward the six digit OTP you just received. It is urgent and I need it to log in.
```

### 8. Family emergency impersonation — measured 84% similarity

```text
Mum, this is my new number because I lost my phone. I urgently need cash to settle an unpaid bill. Transfer Rs 8000 to this account and please do not tell Dad.
```

### 9. UPI refund / PIN theft — measured 82% similarity

```text
Your refund of Rs 2000 has been approved. Approve the collect payment request in your UPI app and enter your UPI PIN to receive the money.
```

### 10. Guaranteed investment returns — measured 89% similarity

```text
Join our VIP trading group. Our bot guarantees 300 percent returns every month. Deposit Rs 6000 right now and withdraw guaranteed profit daily with zero risk.
```

### 11. Remote support scam — measured 86% similarity

```text
Hello, you are speaking to technical support. Your computer is infected and your bank account is at risk. Install the remote access app and share the access code so we can fix it.
```

### 12. Digital arrest / police impersonation — measured 92% similarity

```text
This is the cyber police. A parcel in your name contains illegal items and you are under digital arrest. Transfer Rs 45000 to our verification account immediately and do not contact anyone.
```

### 13. Bank suspension — partial match, 72.3% similarity

```text
Attention customer, your Lotus Bank account is suspended. Verify your password and card PIN at https://bank-demo.invalid before tomorrow or your account will be permanently closed. Please handle this request quickly.
```

## Limits and hierarchy

Recalibration against all 300 messages retained the 71.2% match threshold, from maximizing balanced accuracy on these 13 unseeded English paraphrases and 16 benign controls (`data/demo_benign_controls.json`), not an arbitrary requested percentage. It lies midway between the nearest benign warning (70.1%) and scam paraphrase (72.3%). All 13 pass and all 16 controls are rejected on this calibration set. This is threshold tuning on a small synthetic set, NOT independent validation, Hindi/Hinglish evaluation, or real-world accuracy.

Every eligible database pattern receives its own rank, similarity, and tier. The closest appears first. Tiers describe resemblance only:

| Tier | Similarity |
|---|---|
| Exact | 100% |
| Very strong | 90–under 100% |
| Strong | 80–under 90% |
| Partial | 71.2–under 80% |
| Below threshold | under 71.2%; comparison only, not a match |

These display bands are not independently calibrated fraud probabilities. Below-threshold patterns remain inspectable in the page hierarchy. Inputs shorter than 24 normalized characters are not comparable.

## All 36 stored examples

### 1. KYC / OTP theft

Pattern ID: `demo_pattern_v1_01`

```text
Your KYC has expired and your bank account will be blocked today. Update your PAN details at https://kyc-demo.invalid and share the OTP to keep your account active.
```

### 2. Bank account suspension

Pattern ID: `demo_pattern_v1_02`

```text
Dear customer, your Lotus Bank account is suspended. Verify your password and card PIN at https://bank-demo.invalid within 24 hours or your account will be permanently closed.
```

### 3. Courier fee phishing

Pattern ID: `demo_pattern_v1_03`

```text
Your parcel is held at customs. Pay the clearance fee of Rs 49 at https://parcel-demo.invalid within 12 hours or it will be returned to the sender.
```

### 4. Lottery advance fee

Pattern ID: `demo_pattern_v1_04`

```text
Congratulations! Your number won Rs 25 lakh in our lucky draw. Pay a processing fee of Rs 2000 first to release your prize money.
```

### 5. Job registration fee

Pattern ID: `demo_pattern_v1_05`

```text
You are selected for a work from home data entry job paying Rs 30000 a month. Pay the registration fee of Rs 999 today to receive your offer letter.
```

### 6. Electricity disconnection

Pattern ID: `demo_pattern_v1_06`

```text
Dear consumer, your electricity will be disconnected tonight at 9 pm because your bill is not updated. Transfer Rs 500 immediately to our officer to stop disconnection.
```

### 7. Verification code takeover

Pattern ID: `demo_pattern_v1_07`

```text
Hi, I sent my verification code to your number by mistake. Please forward the six digit OTP you just received. It is urgent and I need it to log in.
```

### 8. Family emergency impersonation

Pattern ID: `demo_pattern_v1_08`

```text
Mum, this is my new number because I lost my phone. I urgently need money to pay a bill. Transfer Rs 8000 to this account and please do not tell Dad.
```

### 9. UPI refund / PIN theft

Pattern ID: `demo_pattern_v1_09`

```text
Your refund of Rs 1500 is ready. Approve the collect payment request in your UPI app and enter your UPI PIN to receive the money.
```

### 10. Guaranteed investment returns

Pattern ID: `demo_pattern_v1_10`

```text
Join our VIP trading group. Our bot guarantees 300 percent returns every month. Deposit Rs 5000 today and withdraw guaranteed profit daily with zero risk.
```

### 11. Remote support scam

Pattern ID: `demo_pattern_v1_11`

```text
This is technical support. Your computer is infected and your bank account is at risk. Install the remote access app and share the access code so we can fix it.
```

### 12. Digital arrest / police impersonation

Pattern ID: `demo_pattern_v1_12`

```text
This is the cyber police. A parcel in your name contains illegal items and you are under digital arrest. Transfer Rs 50000 to our verification account now and do not contact anyone.
```

### 13. Rental deposit fraud

Pattern ID: `demo_pattern_v1_13`

```text
The apartment is available but many people want it. Transfer the security deposit before viewing the property and I will send you the keys by courier.
```

### 14. Loan processing fee

Pattern ID: `demo_pattern_v1_14`

```text
Your instant loan of Rs 200000 is approved without any credit check. Pay Rs 2500 as an advance processing fee today before we release the loan.
```

### 15. Government grant impersonation

Pattern ID: `demo_pattern_v1_15`

```text
You have been selected for a government relief grant of Rs 50000. Send your Aadhaar details and pay the application fee to claim the benefit.
```

### 16. Crypto wallet recovery

Pattern ID: `demo_pattern_v1_16`

```text
We can recover your lost crypto wallet funds. Send the twelve word seed phrase and pay a recovery deposit so our expert can restore your coins.
```

### 17. QR code to receive money

Pattern ID: `demo_pattern_v1_17`

```text
I want to pay you for the item. Scan this QR code and enter your UPI PIN to receive my payment immediately.
```

### 18. Romance emergency

Pattern ID: `demo_pattern_v1_18`

```text
I love you and want to visit you soon. I am stranded at the airport and need an urgent transfer for customs fees. Please send money and keep this between us.
```

### 19. Task job deposit

Pattern ID: `demo_pattern_v1_19`

```text
Earn Rs 5000 daily by liking videos. You completed the first task successfully. Deposit Rs 3000 to unlock premium tasks and withdraw your commission.
```

### 20. Delivery address phishing

Pattern ID: `demo_pattern_v1_20`

```text
We could not deliver your package because the address is incomplete. Update your card details and pay the redelivery fee at https://delivery-demo.invalid now.
```

### 21. Tax refund phishing

Pattern ID: `demo_pattern_v1_21`

```text
Your income tax refund is approved. Confirm your bank login password and OTP at https://refund-demo.invalid to receive your money today.
```

### 22. Subscription renewal phishing

Pattern ID: `demo_pattern_v1_22`

```text
Your streaming subscription will stop today. Enter your card number security code and bank OTP at https://renew-demo.invalid to avoid losing access.
```

### 23. Fake charity collection

Pattern ID: `demo_pattern_v1_23`

```text
We urgently need donations for a child emergency operation. Transfer money to my personal account now. There is no time to verify the hospital or charity registration.
```

### 24. Social account verification

Pattern ID: `demo_pattern_v1_24`

```text
Your social media account will be deleted for copyright violations. Send your login code and password at https://social-demo.invalid to appeal the ban.
```

### 25. Marketplace overpayment

Pattern ID: `demo_pattern_v1_25`

```text
I accidentally sent you more money than the item costs. The payment confirmation is attached. Refund the difference to another account before checking your bank balance.
```

### 26. Ticket advance payment

Pattern ID: `demo_pattern_v1_26`

```text
I have two sold out concert tickets at half price. Transfer the full amount immediately and I will send screenshots of the tickets. No buyer protection is available.
```

### 27. Fake escrow service

Pattern ID: `demo_pattern_v1_27`

```text
Your buyer has deposited funds into our escrow service. Pay the account activation fee at https://escrow-demo.invalid before the payment can be released.
```

### 28. Account recovery phishing

Pattern ID: `demo_pattern_v1_28`

```text
We detected a suspicious login to your email. Reply with your recovery codes and current password so our security team can prevent permanent account closure.
```

### 29. Recruitment training fee

Pattern ID: `demo_pattern_v1_29`

```text
You passed the interview for our international company. Pay a mandatory training deposit and equipment insurance fee today to secure your job offer.
```

### 30. Visa advance fee

Pattern ID: `demo_pattern_v1_30`

```text
Your overseas visa is guaranteed without an embassy interview. Pay the priority clearance fee to this personal account today so we can release your passport.
```

### 31. Miracle cure sales

Pattern ID: `demo_pattern_v1_31`

```text
Our secret herbal treatment permanently cures diabetes in three days. Doctors do not want you to know. Pay in advance now for this guaranteed cure.
```

### 32. Fake cheque refund

Pattern ID: `demo_pattern_v1_32`

```text
Deposit the cheque I sent for your work. Keep your wages and transfer the extra amount to my supplier today before the cheque has fully cleared.
```

### 33. Invoice bank account change

Pattern ID: `demo_pattern_v1_33`

```text
Our company bank account has changed. Ignore the payment details on the original invoice and urgently send the outstanding amount to this new account without calling us.
```

### 34. CEO gift card impersonation

Pattern ID: `demo_pattern_v1_34`

```text
This is your CEO. I am in a confidential meeting and need you to buy gift cards immediately. Send me the card codes and do not discuss this with anyone.
```

### 35. Insurance payout fee

Pattern ID: `demo_pattern_v1_35`

```text
Your insurance claim of Rs 100000 is approved. Transfer an advance release fee to our officer personal account before we can send your payout.
```

### 36. School fee impersonation

Pattern ID: `demo_pattern_v1_36`

```text
This is your school administration. The fee payment account changed this morning. Transfer your child tuition to this personal UPI ID immediately to avoid cancellation.
```

## Benign controls — expected No known match

```text
Lunch at the canteen at one? Please bring your exam notes.
```

```text
Never share your OTP or UPI PIN with anyone. Contact your bank using its official number.
```

Short input `hh` also returns No known match.

## Reproduce

From the repository root:

```text
.venv\Scripts\python scripts/seed_demo_patterns.py
.venv\Scripts\python scripts/verify_demo_patterns.py http://127.0.0.1:8001
```

Use port 8000 for the default launcher. Seeding is additive/idempotent and does not overwrite existing records. The matcher averages normalized token Jaccard overlap and sequence similarity, then applies the demo-calibrated 71.2% threshold. Reproduce calibration with `python scripts/calibrate_demo_threshold.py`. New scams/paraphrases may be missed; similar benign messages may be flagged. The verifier checks all 300 exact patterns, 13 paraphrases, 16 benign controls, and short input. Exact-copy matching does not measure generalization.
