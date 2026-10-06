# Scam messages: records first, model second

## Decision order

1. Normalize the message and compare its SHA-256 fingerprint and wording against stored report records. Exact normalized copies score 1.0; non-exact comparison averages token overlap and sequence resemblance.
2. If any record reaches the demo-calibrated 0.712 threshold, return the catalog verdict and **skip the model entirely**. The score means text similarity.
3. Otherwise call the existing original scam engine. Its result is the final model review score, not an average with weak record matches. If the model cannot run, return UNKNOWN with a null score, not a safe zero.

Responses expose `decision_source`, `model_used`, `method` and `score_kind`. A model skipped on a match is not the same as a model outage. Pattern comparisons remain ranked even when no record qualifies.

The current engine is the existing trained Isolation Forest anomaly signal plus deterministic wording, continuity and precedent signals. This change does not train a new language model or promote rejected candidates. The new catalog is comparison data, not newly trained model weights. Missing call/payment/identity history is not invented. Scores are not calibrated fraud probabilities and false positives/negatives remain possible.

## Catalog provenance

| Source | Unique messages |
| --- | ---: |
| Clean ScamShield publisher-authored synthetic subset | 302 |
| Original TrustGraph-authored examples | 36 |
| New TrustGraph-authored synthetic variants | 700 |
| Total | 1,038 |

Only 302 source-authored ScamShield messages survive the normalized/number-only duplicate filter. The user approved authored supplementation. The 700 added examples span 25 families, seven social-engineering contexts and four concrete asks per family. They are template variants, not 700 independent fraud mechanisms or verified incidents, and must not be described as imported ScamShield data.

All catalog IDs and normalized/number-only text skeletons are unique. Existing seed records are preserved. Running `python scripts/seed_demo_patterns.py` again adds zero rows. Attribution and source SHA-256 are in `data/SCAMSHIELD_NOTICE.md`; authored provenance is in `data/authored_scam_provenance.json`. Reproduce authored rows with `scripts/build_authored_scam_catalog.py` and source selection with `scripts/import_scamshield_sample.py --count 302`; both emit JSON without database writes.

Recalibration on 13 unseeded English paraphrases and 16 benign controls retained 0.712 against the expanded catalog. This is a small synthetic calibration set, not independent accuracy evidence or multilingual validation.

## Persistence and extension display

Every successful signed-in website message check is saved to `AccountCheck`, including HIGH, CAUTION, LOW and UNKNOWN. History/Analytics read those account-owned results. Only verdict metadata, signal scores, method, decision source and model-used state are retained, not raw message text. A failed database save is not shown as a successful saved check. URL structure checks are not scam-message detections and remain separate.

The dashboard connected/not-connected card and its status polling/loading dependency are removed. Pairing and authenticated extension sync remain functional; the UI does not fabricate a healthy connection. Website analysis does not depend on extension heartbeat status. Extension-origin records still require actual pairing/sync; removing an indicator does not connect an unpaired extension.

For the current records-first API, both single-message and chat-batch extension scoring preserve the backend's final score/band rather than letting local rules override it. Local rules remain the unavailable/offline fallback, and older server formats keep their compatibility behavior. Reload the unpacked extension to pick up the changed JavaScript.

## Demo cases

The following measured cases were submitted to the running backend with PostgreSQL and all 1,038 records. Review scores below are out of 100, **not percentages of fraud certainty**. These eight model cases are not seeded catalog rows. Do not seed them, or the route may change from model to records.

| Case | Best stored similarity | Final review score | Band | Route |
| --- | ---: | ---: | --- | --- |
| Safe-account impersonation | 27.0% | 92.3 | HIGH | Model |
| Boss gift-card impersonation | 34.9% | 88.4 | CAUTION | Model |
| Remote-access credential theft | 24.5% | 96.5 | HIGH | Model |
| OTP takeover | 32.7% | 88.4 | CAUTION | Model |
| Fake government threat | 33.1% | 96.5 | HIGH | Model |
| Private-video extortion | 33.1% | 92.3 | HIGH | Model |
| Ordinary planning control | 24.7% | 3.7 | LOW | Model |
| Security advice control | 22.5% | 8.2 | LOW | Model |

### 1. Safe-account impersonation

```text
You are speaking with regional fraud prevention. Ignore the branch staff and migrate your savings to the secure holding account I specify.
```

### 2. Boss gift-card impersonation

```text
I'm the interim office lead. Pick up Apple gift cards, scratch their backs and email me the redemption codes; do not contact your manager.
```

### 3. Remote-access credential theft

```text
For a warranty diagnostic session, start TeamViewer and give me the access code. Keep your online banking signed in while I investigate.
```

### 4. OTP takeover

```text
To restore the backup of your chats, forward the WhatsApp verification code you just received to my private inbox.
```

### 5. Fake government threat

```text
An arrest warrant will be executed unless you buy gift cards and transmit the redemption codes to this investigator. Do not contact the police.
```

### 6. Private-video extortion (text analysis, not video detection)

```text
I recorded you through your camera. Transfer bitcoin to my wallet address before midnight or I will send the private video to your family.
```

### 7. Ordinary planning control

```text
The volunteer committee moved our planning session to Wednesday afternoon. Please bring your notes and a reusable water bottle.
```

### 8. Security advice control

```text
Never share your OTP or password with callers. If someone asks for a verification code, contact your bank through its official app.
```

For the **records-first** branch, copy any stored message from the catalog: its normalized exact copy yields 100% similarity and model skipped. For varied non-exact matching, use `data/demo_judge_queries.json`: 13 paraphrases score 72.3–96.0% similarity. Exact copies must not be artificially capped or randomized.

## Verification and deployment limits

- 81 backend tests and 2,096 subtests passed; 14 disposable-database fixtures skipped. Another 79 tests passed for the original scam signals/fusion without optional media packages. Real PostgreSQL checks were performed separately below.
- `python scripts/verify_scam_pipeline.py` checks all 1,038 seeded records, idempotence, a records match with a model-call trap, eight genuine model fallbacks, all four bands' persistence, metadata privacy and cross-account isolation in a temporary schema. Every verification row/schema is rolled back; public data is untouched.
- Frontend production build and regression tests passed. Extension verdict, rules, result privacy, background syncing and token/style suites passed. These are functional fixtures, not proof of real-world accuracy or an installed-browser reader end-to-end test.
- The current preview is `http://127.0.0.1:8002`. Sign in and open `/app/analyze`; each result links to its saved detail page.
- Normal backend setup now installs the original CPU scam runtime and runs `scripts/verify_scam_model.py`. `/health/scam-model` proves real inference, returning 503 if model, bands or precedent assets are missing. Original weights and thresholds are unchanged; no remote model receives messages.
- Vercel upload rules now retain the engine, baseline model/bands and synthetic precedent file. Eight genuine API inference cases passed in an isolated upload file set, and missing-artifact failures were checked. No cloud build/deployment, Linux install, bundle-size or cold-start claim is made.
- Additional model-only challenges exposed two false negatives (short lottery fee, unfamiliar investment pitch) and one false positive (IT warning mentioning remote access). Run `python scripts/verify_scam_model.py --json` to inspect all scores/signals. These functional examples are not an independent accuracy benchmark, and the model is not yet validated for production fraud decisions.
- Git publication is separate from deployment. Secrets, local dependencies and user-submitted records must not be committed.
