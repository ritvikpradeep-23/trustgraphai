# How TrustGraph's AI works

A plain-language walk-through of what happens to a message or video, from the moment it arrives to the answer you
see. For what it can't do and how to tune it, see `CAPABILITIES_AND_LIMITS.md` in this folder.

---

## 1. The short version

TrustGraph has **three separate checks**. None of them is a chatbot or a large language model you talk to, and none
needs an API key.

| Check | Question it answers | How | Status |
|---|---|---|---|
| **Scam check** | "Is this message trying to scam me?" | First looks for a matching scam report in the database. If none, the **4-signal engine** scores it. | Working, in the website and extension |
| **Deepfake check** | "Has the face in this video been faked?" | Google's **EfficientNet-B0** turns each face into numbers; **your small trained layer** turns those into a fake score. | Built, **not trained yet** |
| **AI-written check** | "Did an AI write this text?" | **distilroberta**, a small language model, fine-tuned to tell human from AI text. | Built, **not trained yet** |

Each check works on its own. A message with a video attached gets two separate answers, not one combined verdict.

---

## 2. The big picture

```
  Browser extension                      Website (React)
  (WhatsApp, Gmail, ...)                 Analyze page
        │                                      │
        │ on-device rules answer instantly     │
        │ + asks the server for a 2nd opinion  │
        ▼                                      ▼
  ┌──────────────────────── Website backend (backend/) ────────────────────────┐
  │                                                                             │
  │  Text message ──► STAGE 1: stored scam reports (PostgreSQL)                 │
  │                     similar enough (≥ 71.2%)? ──yes──► answer = that match  │
  │                              │ no                                           │
  │                              ▼                                              │
  │                   STAGE 2: 4-signal scam engine ──► Low / Caution / High    │
  │                   (backend/app/ai/scam_engine.py → ai/src/trustgraph)       │
  │                                                                             │
  │  Video / image ──► deepfake check  ─┐  through TrustGraphAI.analyze         │
  │  Text          ──► AI-written check ┘  (backend/app/services/ai_model.py)   │
  │                    no trained model? → "pending, no score" (never invented) │
  └─────────────────────────────────────────────────────────────────────────────┘
                     ▲ loads models from ai/models
                     │
  ┌──────────────────────────── ai/ (this folder) ──────────────────────────────┐
  │ models, engine code, training, and two routines that run every 2 hours:     │
  │   learn_cycle.py  learns new scams      run_cycle.py  measures accuracy     │
  └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. The scam check, step by step

### Stage 1: has someone reported this before?

The website compares the message with every scam report stored in its database, by word overlap and wording order.
If the best match is at least **71.2% similar**, that report is the answer, and the engine isn't run. This
catches copies and close rewordings of known scams. It can't recognise a scam nobody has reported yet, and "no match"
means "unknown", not "safe". The 71.2% cut-off was set by your teammate on a small set of paraphrases and honest
messages (`docs/DEMO_SCAM_PATTERNS.md` at the repository root).

### Stage 2: the 4-signal engine

When nothing matches, the message goes to the engine in `src/trustgraph/`. Four independent "signals" each look at
the message from a different angle and each give a score from 0 (no concern) to 1 (strong concern), with a
reason.

#### Signal 1: Similarity: "does it read like a scam?"

Two kinds of evidence, combined:

1. **Script match.** The message is compared with a list of known scam scripts *and* a list of ordinary honest
   messages, using **TF-IDF** (a way of turning text into numbers by word and letter patterns, so typos and
   rewordings still match). What counts is how much closer it is to the nearest scam than to the nearest honest
   message. That way, a message full of banking words isn't flagged just for talking about a bank. Wording alone
   can push this part to **0.6 at most**: looking like a scam isn't proof.
2. **Red flags.** Specific requests that honest messages almost never make, each with its own strength:

   | Red flag | Strength |
   |---|---|
   | Move your money to a "safe account" | 0.8 |
   | Send a one-time code, PIN or password | 0.7 |
   | Gift-card codes | 0.7 |
   | Remote access to your device | 0.7 |
   | Pay to get or start a job | 0.7 |
   | Threat to share private photos or videos | 0.6 |
   | "Our bank details have changed" | 0.5 |
   | Pay in crypto | 0.5 |
   | Threat of arrest or legal action | 0.5 |
   | Upfront fee to release money, a prize or a job | 0.4 |
   | "Keep this secret" | 0.4 |

   Negation is understood: "we will **never** ask for your OTP" doesn't trigger the OTP flag. Text is cleaned first,
   so spacing tricks, leetspeak ("0TP") and broken-up links don't hide a flag.

#### Signal 2: Anomaly: "is the behaviour unusual?"

A machine-learning model called an **Isolation Forest**. It was trained on normal interactions and learned what
"normal" looks like across six facts: call length, time of day, how unusual the amount is, how many times the
contact got in touch in 24 hours, the number of urgency words, and whether the channel is new. It flags combinations
that are easy to separate from normal ones. A second check catches one fact being extreme on its own (for example, 9×
the usual amount), which Isolation Forests tend to miss.

Facts it isn't told are filled with the typical value, which counts as no evidence either way. The website only gives
it the **urgency words it can count in the text** ("urgent", "immediately", "today", ...). It never invents call or
payment history. So for a plain text message, this signal reacts only to urgency.

#### Signal 3: Continuity: "has this contact suddenly changed?"

For a contact you already know, it compares today's details with past ones. A **new payout account** is the strongest
warning (0.8), the classic sign of invoice or CEO fraud. Then come a new email domain (0.6), a new phone number (0.5)
and a new display name (0.3). A *lookalike* of a known value ("acme-c0rp.com") is worse than an honestly new one.
It needs contact history, so for a one-off message it says "No identity history to compare" and scores 0.

#### Signal 4: Precedent: "has this number, account or link been reported?"

It checks phone numbers, accounts, domains, email addresses and crypto wallets (in the message or its sender) against
a list of reported scam identifiers. Matching is exact after cleaning, so "+44 (0)7700 900123" matches "07700900123",
but a number one digit off does not. Evidence grows with the number of reports and fades with age, because numbers
get recycled to innocent owners. The current list is synthetic (made up for testing).

### Combining the four: "noisy-OR"

Each signal is treated as an independent chance that the message is risky:

```
combined = 1 − (1 − similarity) × (1 − anomaly) × (1 − continuity) × (1 − precedent)
```

So one strong signal is enough to raise the score, and signals that agree push it higher still. One weak signal
can't be cancelled out by the others being calm.

### From score to verdict

| Combined score | Verdict |
|---|---|
| below 0.676 | **Low** |
| 0.676 to 0.911 | **Caution** |
| 0.911 and above | **High** |

These cut-offs (`models/risk_bands.json`) were set on normal test traffic so that about **10%** of normal
interactions reach Caution and about **1%** reach High. The explanation names the signal that drove the score most,
plus any other signal scoring 0.3 or more.

### Three real examples

These are run through the live engine exactly as the website calls it:

**"Your bank account will be blocked today. Send the OTP you just received immediately to verify."**

| Signal | Score | Reason |
|---|---|---|
| Similarity | 0.76 | asks for a one-time code, PIN or password |
| Anomaly | 0.56 | 2 urgency words ("today", "immediately") |
| Continuity | 0.00 | no contact history |
| Precedent | 0.00 | no reported identifiers |

Combined: 1 − (0.24 × 0.44) = **0.895 → Caution**, just under High.

**"Hi, are we still meeting at 6 for dinner tonight?"** Similarity 0.00, anomaly 0.05, others 0 → **0.048 → Low**.

**"Dear customer, your parcel is held. Pay the 49 rupee customs fee at india-post-redeliver.top to release it"**
Similarity 0.21, anomaly 0.04 → **0.236 → Low.** This is a **miss**: a calmly worded fake-delivery scam. No red flag
fired, and the wording isn't close enough to a known script. This is exactly the kind of scam the learning routine
(section 6) and stage 1 reports exist to catch.

### What the extension does with it

The extension has its own on-device rules, which answer instantly and work offline. It also asks the server for a
second opinion. The higher of the two wins. If the server doesn't answer in time, the on-device answer stands. The
message text is never stored in the extension's history.

---

## 4. The deepfake check (built, not trained yet)

1. **Pick frames:** 16 frames spread evenly across the whole video (not just the start).
2. **Find the face:** OpenCV's face detector finds the largest face in each frame and crops it, with a 20% margin.
3. **Describe the face:** **EfficientNet-B0** (by Google, downloaded once from Hugging Face, about 21 MB, no account
   needed) turns each face into **1,280 numbers**. It was trained on everyday photos, not deepfakes. Its job is only
   to describe the face well. It stays frozen (unchanged).
4. **Judge the face:** **your trained layer** (one small layer, about 6 KB, `models/efficientnet_head.pt`) turns
   those 1,280 numbers into a fake score from 0 to 1. This is the part that learns real vs fake, from labelled
   videos.
5. **Average:** the face scores are averaged. **0.5 or more → likely fake**, below → likely real. No face in any
   frame → **inconclusive**, with no score.

This is called **transfer learning**: a big model's general skill (describing faces), plus a small layer you train for
your specific question. Optionally, training can also adjust EfficientNet's last few blocks, very gently.

It checks faces only: no voice, no lip-sync, and no motion between frames.

---

## 5. The AI-written check (built, not trained yet)

1. The text is split into word pieces (up to 256).
2. **distilroberta-base** (a small language model, about 82 million parameters) reads it. Fine-tuning by
   `train_text.py` on the HC3 dataset (human vs ChatGPT answers to the same questions) teaches it this one task.
3. It outputs the probability the text is AI-written. **0.5 or more → likely AI.**

"AI-written" is not the same as "scam". Many honest messages are AI-assisted, so this stays separate from the scam
verdict. Short messages carry little evidence.

---

## 6. How it gets better over time

### The learning routine (`learn_cycle.py`, every 2 hours)

1. Takes **one fresh dataset it has never used**: your CSV files in `data/learning/datasets/` first, otherwise a new
   synthetic one. Anything added with `add_examples.py` is included too.
2. **Tests before learning:** it records how many of the new scams the current engine already catches. That number is
   your honest "new-scam catch rate".
3. **Learns:** adds the scams it missed, and the honest messages it wrongly flagged, to the similarity signal's
   example lists. It then re-sets the Low/Caution/High cut-offs.
4. **Safety gate:** keeps the new version only if every test passes, the 24 demo scenarios are unchanged, it catches
   at least as many development scams with no more false alarms, and real UK text messages don't get more than 2
   points more false alarms.
5. **Waits for you:** an accepted version sits in `models/candidate/` until you promote it
   (`python scripts/promote_model.py models/candidate/<version> --yes`). The website's scam check uses this engine
   too, so promoting changes its answers. Agree with your teammate first.

It doesn't retrain the anomaly model, and it doesn't touch the deepfake or AI-written models.

### The accuracy routine (`run_cycle.py`, every 2 hours)

It scores one **never-used** batch of labelled test data with the trained deepfake and AI-written models. It reports
accuracy, precision, recall, F1 and ROC-AUC, then marks the batch as used forever. It never trains anything. Its job
is to show honestly whether a retrained model really got better. It has nothing to score until you train the two
models.

---

## 7. Where each part lives

| Part | File |
|---|---|
| The four signals | `src/trustgraph/similarity/`, `anomaly/`, `continuity/`, `precedent/` |
| Combining and verdict | `src/trustgraph/fusion.py`, `models/risk_bands.json` |
| Live model files | `models/anomaly_isolation_forest.joblib`, `models/risk_bands.json` |
| Website ↔ engine bridge | `backend/app/ai/scam_engine.py` (repository root) |
| Stage 1 report matching | `backend/app/services/previous_report_matcher.py` (repository root) |
| Deepfake and AI-written code | `backend/app/ai/` (repository root); training: `train_video.py`, `train_text.py` |
| Routines | `learn_cycle.py`, `run_cycle.py`, settings in `detection_config.json` |

---

## 8. What to keep in mind

- **Almost all the numbers are synthetic data.** On a locked synthetic test, the live engine caught about **52%** of
  scams, and the best improved version (not live) about **65%**. On 4,827 real UK text messages, it wrongly flagged
  **4.4%** of honest ones. None of this is real-world accuracy.
- **Brand-new kinds of scam:** about 6 in 10 are caught on synthetic data, probably fewer in real life. Scams that
  *ask* for something risky are caught best. Calm, official-sounding ones (fake delivery fees, KYC renewals) and
  friendly openers with no request yet are missed most.
- **A text message alone gives two of the four signals (continuity, precedent) almost nothing to work with.** They
  need contact history and a real reports database.
- **The deepfake and AI-written checks give no scores until you train them** on real data (Celeb-DF, HC3).
