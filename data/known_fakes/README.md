# Known fakes and reported scams

Put labelled items here and list them in `manifest.json` (see
`manifest.example.json`), then run `python scripts/seed_fingerprints.py`.
Add `--demo` for two demo scam messages and one synthetic demo image.

- Images become fingerprints in the `fingerprints` table (only hashes, label
  and source are stored).
- Texts become reported scams in `submissions`/`reports`, which
  `POST /api/detect` matches new messages against.
