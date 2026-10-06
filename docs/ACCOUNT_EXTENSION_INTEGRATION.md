# Real accounts, original model and extension integration

## Run

The folders remain `backend/`, `front end/`, and `trustgraph_extension/`; there is no root `app/` directory. Root launchers and the single-project Vercel entrypoint still work. The frontend is the existing Vite/React/TypeScript application, not a framework migration.

Configure root `.env` privately, then run `./setup_combined.ps1 -SeedDemo -ScamModel` in PowerShell and `.\.venv\Scripts\python backend/run_server.py`. Open `/signup` to enter your own account credentials. For the current preview use `http://127.0.0.1:8002/login`; normal launcher default is port 8000.

## Login and account history

- `GET /api/auth/session` bootstraps the anonymous/session cookie and an in-memory CSRF token. Login/register rotate it; logout revokes the database session. Login redirects to `/dashboard` (`/app/dashboard` alias).
- Passwords are salted PBKDF2-SHA256 hashes with 600,000 iterations. Signup requires a non-blank 15–128-character passphrase. No password or auth token is logged or placed in localStorage.
- Opaque cookie: HttpOnly, SameSite=Lax, Secure on HTTPS/Vercel. Normal sessions expire after 8 hours; Remember me chooses a 30-day persistent session. Anonymous bootstrap sessions expire after 30 minutes. Expired sessions are cleaned when issuing sessions.
- Auth/session/pairing attempts use atomic PostgreSQL rate-limit counters; CSRF protection covers account and workspace writes. API validation does not echo passwords. Account queries only return the signed-in user's checks and extensions. Caches are cleared when accounts change.
- Six additive `tg_*` tables preserve all existing records. Old unowned history is not assigned to an arbitrary new account. Old extension tokens must be replaced by a new account-owned pairing. No old records were removed.
- Analyze processes text transiently and saves only a metadata projection via `/api/workspace/checks`. Raw messages, model explanation strings, sender identifiers and URL paths are not retained. `/api/detect` remains stateless for extensions. Hosted requests cannot attach to unowned legacy submissions.

## Pair the installed extension

1. Reload the updated unpacked `trustgraph_extension/` in Chrome/Edge yourself; no install or permission change was automated.
2. In extension Settings set **Backend URL** to the same backend origin, e.g. `http://127.0.0.1:8002`. Set **Web app URL** to that origin too (no `/api` suffix). If blank in remote-engine mode, it defaults to Backend URL. Save.
3. Sign in on the website, open `/app/settings`, click **New code**, and enter the one-time code in the extension popup. It expires after 10 minutes and works once. Pair only with a backend you trust.
4. New saved verdicts sync with a Bearer token. Heartbeats now use the same authenticated workspace client, including the backend-URL fallback. The dashboard counts only your extension's heartbeat; it becomes stale after 2 minutes. It does not prove every supported-site reader is functioning.
5. Check a non-sensitive test message. Open History/Analytics: they refresh every 15 seconds and separate all supported extension channels, unknown results, caution and high risk. Old local extension history is not bulk-uploaded automatically. Sync failures keep local results but are not guaranteed to replay later.

## The model actually used

`backend/app/ai/scam_engine.py` loads the existing `ai/models/anomaly_isolation_forest.joblib` and original `ai/src/trustgraph` four-signal pipeline: learned anomaly plus deterministic continuity, wording similarity and precedent. It resolves absolute paths without changing process working directory. Only observed text/urgency and supplied metadata are passed; call/payment history is not invented. The original engine handles absent features using its own defaults and evidence mask.

Rejected classifier/anomaly candidates are preserved, not promoted. This is not a new LLM or external AI provider. No message was sent to an external model service. AI-written and deepfake adapters still need their missing trained weights; they return unavailable rather than fake scores.

Catalog matching runs first. Qualified matches skip the model and return **text similarity**. Only when there is no qualifying match does the original scam engine provide the final **review score**. These meanings are not mixed or averaged and neither is a calibrated fraud probability. Catalog similarity is shown separately in its ranked hierarchy. Exact copies may legitimately match 100%; paraphrases vary naturally. The extension retains actual numeric model scores rather than forcing all Caution scores to 69 or inventing a High minimum.

The catalog has 1,038 unique synthetic message examples: 302 ScamShield-origin, 36 original authored and 700 additional authored variants. They are not independent scam mechanisms or verified incidents. See `SCAM_MESSAGE_PIPELINE.md`, `DEMO_SCAM_PATTERNS.md`, `SCAMSHIELD_SAMPLE.md` and `data/SCAMSHIELD_NOTICE.md` for examples and provenance. Its 71.2% threshold was reproduced against the expanded catalog; it is demo-calibrated, not independent validation, especially not a Hindi/Hinglish accuracy claim.

Real-runtime spot checks produced different scores (3.7, 76.1 and 61.9 / 100). The original model still has false negatives: a short lottery/registration-fee message outside the catalog returned LOW at 61.9 / 100 under its original bands. Connecting a trained model does not establish reliable scam accuracy. No band was lowered merely to make those demonstrations look successful; evaluate and calibrate on independent labelled messages before relying on it.

Standard backend dependencies now include the CPU scam runtime. Vercel packaging includes `ai/src/trustgraph/`, the original Isolation Forest, risk bands and public synthetic precedent fixture; rejected candidates and private data stay excluded. Eight genuine model API cases passed in an isolated local upload file set. `/health/scam-model` runs a real inference probe and returns 503 when unavailable. Read `VERCEL_DEPLOYMENT.md`; no cloud build/deployment has been performed.

## Verification and remaining limits

- `npm run build` and `npm test` in `front end/` check TypeScript, production assets and 18 regression tests. Login was visually checked at desktop, tablet and mobile widths, with no horizontal overflow, plus required/invalid-email feedback, Enter submission, password visibility and signup navigation.
- Backend tests: `python -m pytest tests -q` (the AI tests are in `ai/tests/`). Database-specific fixtures require a separate disposable `TEST_DATABASE_URL`; do not point them at existing user data. Heavy engine/deepfake suites need extra optional dependencies/weights and were not claimed as run.
- `python scripts/verify_account_integration.py` uses the configured PostgreSQL connection only inside a temporary schema and rolls back all test rows and the schema. It checks signup, hashed passwords, CSRF, login/logout, rotation/replay revocation, Remember me, rate limiting, single-use pairing, authenticated heartbeat, metadata sync/privacy and cross-account isolation. Public data is untouched by this verification.
- Five Node extension suites cover rules, styling contrast, verdict normalization, metadata validation and background flows, including authenticated heartbeat with a blank Web app URL. Browser reader/installed extension E2E still requires manual confirmation. The older `workspace-e2e.js` harness predates account login and is not current proof of integration.
- `python scripts/check_vercel_config.py` validates the ordinary one-project configuration against Vercel's official schema; source/layout tests exercise the entrypoint and rewrites. This is not proof of a cloud deployment.

Before a public release: add versioned database migrations, server pagination/retention, trusted proxy/IP rate-limit configuration, compromised-password checks, email verification and recovery, extension token revocation/expiry, account deletion, monitoring and an independent security/detector evaluation. Current auth limits can group users behind a shared proxy; do not blindly trust client-supplied forwarding headers. Public stateless detection/media endpoints need deployment-level abuse controls. Recovery/account-delete buttons honestly remain unavailable. Keep the prototype restricted until reviewed, and rotate any database credential previously shared in chat.

Password/session/CSRF design references: [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), and [CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html). These implementation choices do not imply a completed security audit.
