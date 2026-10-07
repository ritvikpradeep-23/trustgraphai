# ai/models/

The `python ...` commands below run from the `ai` folder unless they say otherwise.

The original scam artifact is committed and active. The optional AI-text trained weights are not present.

**The scam engine's baseline files** (`anomaly_isolation_forest.joblib`, `risk_bands.json`) are used by the original `src/trustgraph` four-signal engine and `backend/app/ai/scam_engine.py`. The learned component is a fitted Isolation Forest, combined with deterministic wording similarity, continuity and precedent; it is not an LLM or an end-to-end text classifier. Standard backend/API requirements now include the CPU runtime. The API checks records first, skipping the model on qualifying matches; unmatched text gets the model's final review score. Run `python scripts/verify_scam_model.py` from the repository root or request `/health/scam-model` to verify genuine inference.

`candidate/` preserves experiments; standard setup does not select them or enable the experimental classifier. Do not set `TRUSTGRAPH_MODEL_DIR` or `TRUSTGRAPH_CLASSIFIER` for the baseline demo. Original weights and bands are unchanged. Only load trusted joblib artifacts: pickle-based files can execute code. Versions are pinned to the tested runtime. Synthetic training and observed false negatives/positives limit reliability; review scores are not calibrated fraud probabilities.

Vercel configuration now includes the baseline CPU scam assets and synthetic precedent fixture. Isolated local bundle inference passed, but a cloud build/deployment has not been verified. Candidate models, private data and optional AI-text weights remain excluded.

**The AI-written text model**, `models/text_detector/`: distilroberta-base fine-tuned on human vs AI text by
`python train_text.py`. The website's `POST /api/text/ai-check` uses it (folder: `AI_TEXT_MODEL_DIR`).

## How the website uses them

The optional AI-text engine is in `backend/app/ai/` and is reached through `TrustGraphAI.analyze` in
`backend/app/services/ai_model.py`. It gives a score only when both are true:

1. the AI packages are installed: `python -m pip install -r ai/requirements-ai.txt`
2. its trained model above exists

Otherwise it answers "pending AI integration; no score was produced". No score is ever made up. Restart the server
after training so it loads the new model. `AI_THRESHOLD` (default 0.5) sets where a score counts as AI-written.
