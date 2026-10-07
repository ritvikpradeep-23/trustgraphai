# Website implementation audit — 6 October 2026

## Gaps completed

| Feature | Previously | Now |
| --- | --- | --- |
| Account profile name | Only edited browser preferences; signed-in identity did not change | `PATCH /api/auth/profile` saves the authenticated account name in PostgreSQL |
| Password change | Disabled placeholder | `POST /api/auth/password`, current-password verification, 15–128 character non-blank new passphrase, rate limits, all old website sessions revoked, fresh session/CSRF token |
| Website review / feedback | Disabled controls and unsupported service method | Owner-only `PATCH /api/workspace/detections/{id}` saves review status and feedback without changing risk scores |
| Delete history | No real backend route | `DELETE /api/workspace/detections` removes only the signed-in user's website and synced extension results; other users and pairing remain intact |
| Delete account | Disabled/unimplemented | `DELETE /api/auth/account`, current password plus explicit `DELETE` confirmation; removes account verdicts, sessions, pairing codes and extension tokens in dependent-first order |
| Legacy model interface | `TrustGraphAI.predict()` always returned pending for scams | Model-only adapter calls the existing original scam engine and preserves actual scores/signals. The website API still checks records first |
| Required message inputs | Blank text/channel and unbounded optional metadata accepted | Reject blank text/channel, oversized messages and oversized sender/URL/submission identifiers with 422 |

New authentication/profile/review/history mutation routes require a signed-in account and CSRF protection. Password/account changes are rate-limited and verify the current password. Bodies forbid extra account identifiers and arbitrary score changes. Validation responses do not echo credentials. No database-table migration is needed; existing account tables are reused.

Settings now reads account identity from the server rather than claiming a browser preference is the real profile. Estimate preferences remain browser-local by design. Account deletion clears this browser's local display preferences after successful server deletion. The confirmation dialog includes the current-password field in its keyboard focus loop, starts on Cancel, disables permanent deletion without a password, and describes its effect accurately.

## Verification

- Frontend production build and all 21 regression tests passed.
- 86 backend tests and 2,101 subtests passed, with 14 disposable-database fixtures skipped. Unit/API, model and isolated-upload regressions are exercised with `python -m pytest tests -q`; optional AI training/media suites live in `ai/tests/`. Real PostgreSQL controls were checked separately below.
- `scripts/verify_account_controls.py` creates two temporary accounts and paired extensions inside a temporary PostgreSQL schema. It checks profile persistence, review ownership, immutable scores, password/session rotation, stale-CSRF rejection, owner-only history deletion, account-dependent cleanup and extension-token revocation. The second account is checked throughout. All rows/schema are rolled back; existing user data is untouched.
- The live preview is `http://127.0.0.1:8002`. Browser inspection verified the account name is server-derived, new password controls are enabled, privacy actions are available and account deletion requires a password. The dialog was cancelled; no real account mutation was performed through the browser.
- The original scam-model health probe remains available. No rejected classifier was promoted, no model retrained, and records-first website detection order is unchanged.

## Still explicitly unavailable or limited

| Feature | What is missing / limit |
| --- | --- |
| Forgot-password email | A configured, verified email-delivery/recovery workflow; signed-in password changes now work separately |
| Notifications | An actual notification delivery service; disabled toggles do not pretend to deliver alerts |
| Contact page | A delivery destination/backend inquiry workflow and agreed handling of personal data; the form is clearly labelled demo-only |
| AI-written / audio | Applicable trained artifacts and optional runtimes. Audio has no implemented trained adapter. Parameters alone cannot supply missing models |
| Experimental scam text classifier | `ai/models/candidate/classifier_v1` is marked rejected by its own evaluation. It was not activated without informed experimental-use approval |
| Extension-result review from website | Synced extension snapshots remain read-only. Extension false-alarm feedback can be submitted by the extension; website-authored checks now support both review and feedback |
| URL analysis | Structural inspection only; does not visit or verify a site, and is not saved as a scam-message detection |
| Deleted synced history | Website deletion does not erase the extension's local cache. Future extension sync can add results again |
| Deployment | Local runtime/build checked; a Git push does not deploy or verify a cloud build |

Deletion is permanent when the account owner confirms it. Shared scam catalog rows and unowned legacy records are never removed by these account controls. Short-lived hashed authentication rate-limit counters expire independently of account deletion. Before public launch, further abuse/concurrency testing, trusted-proxy configuration and broader model validation remain necessary.
