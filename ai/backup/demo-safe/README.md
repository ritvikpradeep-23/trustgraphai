# demo-safe backup

Copies of `models/` and `data/` taken at commit `6bb7d6d` (the "demo-safe" state, 2026-10-05), before the
fast improvement routine. The git tag `demo-safe` points at that commit in the workspace where it was made.
This session can't create tags on GitHub, so after pulling, recreate it with:

    git tag demo-safe 6bb7d6d

To run the server exactly as it was: `git checkout demo-safe` (or `6bb7d6d`), then start it as usual.
