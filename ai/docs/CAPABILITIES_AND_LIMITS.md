# TrustGraph: what it can do, where it falls short, and how to tune it

This covers everything built so far, so you can judge it and decide what to improve. Numbers marked
*synthetic data* come from generated messages, not real users. Nothing here is real-world accuracy.

## At a glance

| Function | Status today | Where |
|---|---|---|
| Browser extension (shield on messages, chat scan, verdicts) | ✅ Working | `trustgraph_extension/` |
| Scam-message check (4-signal engine) | ✅ Working, stand-alone (the website's `/api/score` now uses PostgreSQL report matching instead) | `src/trustgraph/`, `run_website.py` |
| Similar-report search ("others reported this") | ✅ Working, now the website's own word-similarity matching in PostgreSQL | `POST /api/detect`, `/api/reports` |
| New-scam learning routine | ✅ Working, fresh dataset every 2 hours | `learn_cycle.py` |
| Accuracy routine | ✅ Working, every 2 hours (needs trained models to score) | `run_cycle.py` |
| AI-written text check | ⚠️ Built into the website backend and tested, **not trained yet** | `backend/app/ai/`, `POST /api/text/ai-check` |
| Deepfake video check | ⚠️ Built into the website backend and tested, **not trained yet** | `backend/app/ai/`, `POST /api/video/analyze`, `/api/media/check` |
| Extension showing AI-text / video results | ❌ Not connected yet (waiting for trained models) | |
| Combining text + video + audio into one verdict | ❌ Not built (each is judged separately) | |

> **Important when judging:** the live engine is still the **starting ("demo-safe") version**. The improved
> versions from the improvement rounds (`fast_r12`) and the learning routine (`learn_*`) sit in `models/candidate/`
> until you promote one. So the extension currently gets the weaker engine (see the numbers below). See
> "Quickest wins" at the end.

> **Since the website reorganisation** (`backend/`, PostgreSQL): the AI-text and deepfake engines live in
> `backend/app/ai/` and answer through `TrustGraphAI.analyze` (`backend/app/services/ai_model.py`) once
> `requirements-ai.txt` is installed and the models are trained; otherwise "pending", never a made-up score. The
> extension's `/api/score` is now answered by the website's PostgreSQL report matching, not by the 4-signal engine
> below, and `/api/feedback` and `/api/accuracy` were removed (the website keeps its data in PostgreSQL only). The
> 4-signal engine and both routines still run as stand-alone scripts. Section 3 describes the older
> sentence-model search; the website now uses `docs/DEMO_SCAM_PATTERNS.md`'s word similarity.

---

## 1. Browser extension

**What it can do**
- A shield on each message on **Gmail, WhatsApp Web, LinkedIn, Telegram, Discord, Slack, Messenger and Instagram**,
  plus right-click "Check with TrustGraph" on any site, and a whole-chat scan in a side panel.
- A verdict of **Low / Caution / High**, with a 0–100 score, a plain-language explanation and the words that
  triggered it.
- **On-device rules** that work offline: urgency, money / gift-card / crypto requests, OTP or password requests,
  lookalike links, sender mismatch, impersonation, a sudden change in a sender's behaviour, and known scam wording.
- Rules in **English, Hindi, Hinglish, Malayalam and Manglish**. Leetspeak and spacing tricks are normalised, and
  negation is understood ("we will never ask for your OTP").
- It asks the local server (`/api/score`, the website's report matching) for a second opinion and combines both. If the server doesn't answer
  within 3 seconds, it uses its own rules.
- **Privacy:** the stored record has no message text (a test enforces this). History can be exported or deleted.

**Limits**
- It reads what the page shows. If a site changes its layout, the shield can disappear until the site's selectors
  are updated (the extension has fallbacks, but no guarantee).
- **Text only.** It doesn't look at images, voice notes or videos in a chat.
- It doesn't yet show the AI-text or video results, even though the server can produce them.

**Tune it**
- Extension settings → **Sensitivity**: `relaxed` / `balanced` / `strict`. Strict flags more scams but also more
  honest messages.
- Server address: `backend_url`, default `http://127.0.0.1:8000`.

---

## 2. Scam-message check (the core AI)

**How it decides:** four signals, combined with "noisy-OR" (any strong signal can raise the risk):

| Signal | What it looks for | Needs |
|---|---|---|
| **Similarity** | Wording close to known scam scripts (TF-IDF), plus red-flag rules: OTP/password requests, fees, "verify" links, gift cards, remote access… with negation understood | Message text |
| **Anomaly** | Unusual behaviour: odd hour, many contacts in 24 h, a new channel, urgency words (IsolationForest) | Metadata; text-only messages give it little to go on |
| **Continuity** | A known contact suddenly has a new payout account, number, email domain or name (takeover / CEO fraud) | Contact history |
| **Precedent** | A number, account, domain or wallet that was reported as a scam before | A reports database (synthetic now) |

**Measured** (synthetic data, except the UK SMS line):

| | Starting engine (live now) | Best improved version (`fast_r12`, not live) |
|---|---|---|
| Scams caught, locked final test (120 scams, 25 types) | 51.7% | **65.0%** |
| Honest messages wrongly flagged (same test) | 2.1% | 0.0% |
| Real UK text messages wrongly flagged (**real data**) | 4.4% | 3.6% |
| A scam type it has never seen (leave-one-type-out) | 57% | 75% |

**What it's good at**
- Scams that **ask for something risky**: OTP, card details, a fee, a "verify" link, remote access, gift cards.
- Rewordings and evasion tricks: spacing, leetspeak, emoji padding, links broken up.
- Mixed-language messages (Hinglish and Manglish did about as well as English on the final test).
- Explaining itself: every verdict names the signal and the words behind it.

**Limits**
- **Soft openers are mostly missed:** a friendly "wrong number", or "are you free?" with no request yet. Wording
  can't tell these apart; sender history has to.
- **New kinds of scam:** about 6 in 10 are caught (synthetic data); real life is probably lower. Calm, official-sounding
  formats (KYC renewal, e-challan) are the weakest.
- With text only, 2 of the 4 signals (continuity, precedent) have little to work with. Their full strength needs
  sender history and a real reports database.
- Almost all test data was generated by the same AI that built the detector, which flatters it.
- Learning some scam types made a few others slightly worse (e.g. instant-loan harassment 3/6 → 0/6 on the final
  test).

**Tune it**
- `models/risk_bands.json`: the Caution (0.676) and High (0.911) cut-offs. Lower catches more scams and flags more
  honest messages. Prefer re-setting them by calibration rather than by hand.
- `src/trustgraph/fusion.py` → `DEFAULT_WEIGHTS`: how much each signal counts.
- Red-flag rules: `src/trustgraph/similarity/detector.py`. **8 proposed rules** in `reports/fast/proposed_rules.md`
  were never applied. Reviewing them is cheap and targets known misses.
- Scam and honest examples: grown by the learning routine (section 4).
- An optional 5th signal (a classifier) can be switched on with `TRUSTGRAPH_CLASSIFIER=1`. It was not adopted: it
  helped on new scam types but didn't meet the improvement bar.

---

## 3. Similar-report search ("others reported this")

**What it can do:** stores scams people report (`POST /api/text/report`). For a new message (`/api/text/analyze`) it
finds the most similar reports by **meaning**, not exact words, using the `all-MiniLM-L6-v2` sentence model, and
answers LOW / MEDIUM / HIGH. **It never returns another person's report text.**

**Limits:** it's only as good as its reports, and it starts almost empty (10 example reports from
`scripts/seed_reports.py`). It's English-centred, and reports are not verified. The extension doesn't use it yet;
the learning routine does pick up its reports.

**Tune it:** `.env` → `SCAM_HIGH_THRESHOLD` (0.82), `SCAM_MEDIUM_THRESHOLD` (0.68), `SCAM_TOP_K` (5).

---

## 4. New-scam learning routine

**What it can do**
- Every 2 hours it takes **one fresh dataset it has never used**: your files in `data/learning/datasets/` first,
  then a new synthetic one. Reports and corrections you add with `add_examples.py` join each run.
- It records how many scams it caught **before** learning them. That's your running "new-scam catch rate".
- It learns the misses and the wrongly flagged honest messages.
- It keeps a new version only if the safety gate passes: all tests pass, all 24 demo scenarios are unchanged, dev
  recall is not lower, dev High false alarms are not higher, and real UK SMS false alarms are at most +2 points.
- It never changes the live engine without your yes (Claude Desktop task) or `AUTO_PROMOTE`.

**Measured** (synthetic data):
- Brand-new scam types (LPG e-KYC, 5G SIM, tax refund…): 9 of 14 caught before learning.
- After learning 3 tax-refund reports: rewordings went from 1/3 to **3/3** caught, with 0/2 honest messages flagged.
- Fresh synthetic datasets: 88% and 83% caught before learning, because these are scam types it had already studied.

**Limits**
- Synthetic datasets only teach new **wordings** of known scam types. New **kinds** of scam must come from your
  datasets or real reports.
- Reports aren't verified. The gate limits the harm a bad report can do, but can't make it zero.
- The "no drop on dev" rule is strict: one dev message can block a good version (that happened once).
- It runs only while the laptop is on (and, for the Claude Desktop task, the app is open). Each Desktop run uses
  your Claude plan.

**Tune it** (`detection_config.json` → `learning`):
- `LEARN_INTERVAL_HOURS` (2)
- `DATASET_CHUNK_ROWS` (300)
- `FRESH_SYNTHETIC_WHEN_EMPTY` (true)
- `SYNTHETIC_SCAMS` / `SYNTHETIC_HONEST` (60 / 120)
- `MIN_NEW_EXAMPLES` (5)
- `DEV_RECALL_TOLERANCE` (0; 0.01 allows a one-point dip)
- `AUTO_PROMOTE` (false)

---

## 5. AI-written text check

**What it will do once trained:** gives each text a 0–1 "AI-written" score (`/api/text/ai-check`). It uses `distilroberta-base` (Hugging Face, about 82M parameters), fine-tuned on
**HC3**: human and ChatGPT answers to the same questions.

**Limits** (expect these even after training):
- **The domain doesn't match.** HC3 is 2022 ChatGPT answering questions. It is not chat messages, and not newer AI
  models, so expect much weaker results on short WhatsApp/SMS texts.
- **Short texts are unreliable.** A one-line message carries very little evidence.
- Easy to fool with light human editing or a "rewrite this casually" prompt. Weak on Hindi, Malayalam and code-mixed
  text (HC3 is English).
- **"AI-written" is not "scam".** Plenty of honest messages are AI-assisted. That's why it's kept separate from the
  scam verdict.

**Tune it:**
- `train_text.py`: `--max-train` (more data), `--epochs` (2), `--max-length` (256), `--base-model` (e.g. a larger
  `roberta-base` if your GPU allows).
- `AI_THRESHOLD` environment variable (0.5), shared with the video check.
- Best improvement: add **real** short messages, both human and AI-written, as a CSV with
  `prepare_data.py text --csv`.

---

## 6. Deepfake video check

**What it will do once trained:**
1. It picks 16 frames spread over the whole video (the API does the same). The extension's media check sends its
   own captured frames.
2. It crops the largest face in each frame.
3. **EfficientNet-B0** (Hugging Face, frozen) plus **your trained layer** score each face, and the scores are
   averaged. The answer is LIKELY_FAKE / LIKELY_REAL, or INCONCLUSIVE when no face is found.

**Limits:**
- **Faces only:** it ignores the voice (cloned voices aren't checked), lip-sync and the background.
- The OpenCV face detector misses side profiles, small or dark faces. A video with no detectable face is
  "inconclusive", never a guess.
- **Each frame is judged alone.** Motion over time (flicker, unnatural blinking) isn't used.
- **Dataset bias:** Celeb-DF / FaceForensics++ deepfakes come from older methods. Newer generators, heavy
  WhatsApp compression and screen recordings can score much worse.

**Tune it:**
- `train_video.py`:
  - `--epochs`
  - `--unfreeze-last N`: lets the last blocks adapt; usually the biggest gain once you have enough data
  - `--frames`
- Environment variables: `AI_THRESHOLD` (0.5), `EFFICIENTNET_HEAD_PATH` (`models/efficientnet_head.pt`).
- `backend/app/ai/engines.py`: `FRAMES_PER_VIDEO` (16), `FACE_MARGIN` (0.2).
- More varied training data (DFDC, recent deepfakes, compressed clips) helps more than any setting.

---

## 7. Accuracy routine, server and privacy

- `run_cycle.py` scores **one unused test batch** per detector every 2 hours, never reuses a batch, and never trains.
  It reports accuracy, precision, recall, F1, ROC-AUC and the confusion matrix (`show_report.py`).
  It needs the trained models.
- The website backend, `python backend/run_server.py`, at `127.0.0.1:8000` (needs PostgreSQL, see
  `TRUSTGRAPH_HANDOFF.md`). `/docs` lists every endpoint.
- Privacy:
  - Message text is never written to the server log.
  - Reports are never returned to anyone.
  - Learning data and versions built from it are kept out of git.

---

## Overall limits to keep in mind

1. **No real-world validation yet.** Almost all numbers are synthetic data. The only real-data check is 4,827 UK
   text messages, used for false alarms only.
2. **Not multimodal.** Text, video and (missing) audio are judged separately; a scam with a deepfake video attached
   isn't scored as one thing.
3. **No voice or image checks.** Voice-clone calls and fake screenshots aren't covered.
4. **It depends on your laptop:** server, routines and models run locally. Nothing protects users while it's off,
   except the extension's own rules.
5. **Reports are unverified,** so learning from them can be misled. The gate limits this but doesn't remove it.

---

## Quickest wins, roughly in order of impact

1. **Promote the improved scam engine:**
   `python scripts/promote_model.py models/candidate/fast_r12 --yes`, or the latest accepted `learn_*` version from
   `runs/learning_best.json`. (This is the stand-alone engine; the website doesn't use it.) This moved scams caught on the final test from 51.7% to 65.0%
   (synthetic data). `--rollback` undoes it.
2. **Feed it real data.** Real scam messages and real honest messages, as CSVs in `data/learning/datasets/`. This
   matters more than any setting.
3. **Review the 8 proposed red-flag rules** in `reports/fast/proposed_rules.md`. They target known misses.
4. **Train the two models:**
   - AI text: `prepare_data.py text --hc3`, then `train_text.py`.
   - Video: request Celeb-DF v2, then `train_video.py`, then `--unfreeze-last 2`.
5. **Show the AI-text and video results** in the extension/website once both are trained (`/api/text/ai-check`
   answers `"available": true`).
6. **Later:** late fusion (one verdict from text plus video), a voice-clone check, a stronger face detector, and a
   real shared reports database for the precedent signal.
