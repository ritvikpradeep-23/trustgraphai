# Judge demo: database pattern matching (no AI)

These 12 authored, synthetic examples illustrate common scam patterns. They are not verified real-world incidents. All links use the reserved .invalid domain; do not replace them with live phishing links.

Open http://127.0.0.1:8001/app/analyze, paste a full message below, and click **Analyze message**. Exact and case/punctuation-normalized examples should show HIGH, the matching category, and 100% **text similarity**. That is not a 100% fraud probability or measured real-world accuracy.

The database contains these examples in submissions/reports tagged demo_pattern / synthetic_demo. The checker uses normalized token Jaccard overlap averaged with sequence similarity, with a 72% threshold. It has no AI dependency. New or heavily paraphrased scams can be missed, and similar legitimate messages may be flagged. No match means UNKNOWN, not safe. Checks are not automatically saved to detection history.

## 1. KYC / OTP theft

Pattern ID: `demo_pattern_v1_01`

```text
Your KYC has expired and your bank account will be blocked today. Update your PAN details at https://kyc-demo.invalid and share the OTP to keep your account active.
```

## 2. Bank account suspension

Pattern ID: `demo_pattern_v1_02`

```text
Dear customer, your Lotus Bank account is suspended. Verify your password and card PIN at https://bank-demo.invalid within 24 hours or your account will be permanently closed.
```

## 3. Courier fee phishing

Pattern ID: `demo_pattern_v1_03`

```text
Your parcel is held at customs. Pay the clearance fee of Rs 49 at https://parcel-demo.invalid within 12 hours or it will be returned to the sender.
```

## 4. Lottery advance fee

Pattern ID: `demo_pattern_v1_04`

```text
Congratulations! Your number won Rs 25 lakh in our lucky draw. Pay a processing fee of Rs 2000 first to release your prize money.
```

## 5. Job registration fee

Pattern ID: `demo_pattern_v1_05`

```text
You are selected for a work from home data entry job paying Rs 30000 a month. Pay the registration fee of Rs 999 today to receive your offer letter.
```

## 6. Electricity disconnection

Pattern ID: `demo_pattern_v1_06`

```text
Dear consumer, your electricity will be disconnected tonight at 9 pm because your bill is not updated. Transfer Rs 500 immediately to our officer to stop disconnection.
```

## 7. Verification code takeover

Pattern ID: `demo_pattern_v1_07`

```text
Hi, I sent my verification code to your number by mistake. Please forward the six digit OTP you just received. It is urgent and I need it to log in.
```

## 8. Family emergency impersonation

Pattern ID: `demo_pattern_v1_08`

```text
Mum, this is my new number because I lost my phone. I urgently need money to pay a bill. Transfer Rs 8000 to this account and please do not tell Dad.
```

## 9. UPI refund / PIN theft

Pattern ID: `demo_pattern_v1_09`

```text
Your refund of Rs 1500 is ready. Approve the collect payment request in your UPI app and enter your UPI PIN to receive the money.
```

## 10. Guaranteed investment returns

Pattern ID: `demo_pattern_v1_10`

```text
Join our VIP trading group. Our bot guarantees 300 percent returns every month. Deposit Rs 5000 today and withdraw guaranteed profit daily with zero risk.
```

## 11. Remote support scam

Pattern ID: `demo_pattern_v1_11`

```text
This is technical support. Your computer is infected and your bank account is at risk. Install the remote access app and share the access code so we can fix it.
```

## 12. Digital arrest / police impersonation

Pattern ID: `demo_pattern_v1_12`

```text
This is the cyber police. A parcel in your name contains illegal items and you are under digital arrest. Transfer Rs 50000 to our verification account now and do not contact anyone.
```

## Benign controls (expected: No known match)

```text
Lunch at the canteen at one? Please bring your exam notes.
```

```text
Never share your OTP or UPI PIN with anyone. Contact your bank using its official number.
```

Short input such as `hh` should also have no match.

## Reproduce

From the repository root:

```text
.venv\Scripts\python scripts/seed_demo_patterns.py
.venv\Scripts\python scripts/verify_demo_patterns.py http://127.0.0.1:8001
```

Seeding is additive and idempotent; it does not delete or overwrite existing records. Use the real running port (8000 if started with the default run_server.py).
