# Pitch summary: five honest bullets

- **What we trained:**
  - grew the wording-match examples (the similarity signal)
  - tried a learned text classifier as a fifth signal
  - retrained the "unusual behaviour" model on 20,000 normal interactions

  Every version was saved as a package that can be switched on or rolled back in one step.
- **On what data:** about 1,400 labeled training messages (29 scam types, 13 honest types, English, Hinglish and
  Manglish), all **synthetic** (AI-written, fake placeholders only). The only real data was 4,827 honest UK text
  messages, used purely as a false-alarm check.
- **How it was tested:**
  - every version was compared at the same false-alarm rate
  - on message families it never trained on
  - with each scam type held out in turn
  - and once on a frozen test set, locked with a fingerprint
- **Results (synthetic data):** the best version caught **91% of test scams, up from 76%**, and 75% of scam types
  held out from its examples (up from 57%). But it also flagged more honest test messages (11.6% vs 8.6%). The
  learned classifier and the retrained anomaly model were **rejected** by our own rules.
- **Limits:**
  - **The biggest real-world gain came from 40 casual everyday texts.** Adding them to the honest examples cut real-text false alarms from 19% to 10%.
  - Generated data flatters the numbers: the classifier scored 100% on familiar templates but 67% on unfamiliar scam types.
  - Real messages are what's needed next.
