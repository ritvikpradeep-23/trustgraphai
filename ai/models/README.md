# ai/models/

The `python ...` commands below run from the `ai` folder unless they say otherwise.

The original scam artifact is committed and active. Optional media/text trained weights are not present.

**The scam engine's baseline files** (`anomaly_isolation_forest.joblib`, `risk_bands.json`) are used by the original `src/trustgraph` four-signal engine and `backend/app/ai/scam_engine.py`. The learned component is a fitted Isolation Forest, combined with deterministic wording similarity, continuity and precedent; it is not an LLM or an end-to-end text classifier. Standard backend/API requirements now include the CPU runtime. The API checks records first, skipping the model on qualifying matches; unmatched text gets the model's final review score. Run `python scripts/verify_scam_model.py` from the repository root or request `/health/scam-model` to verify genuine inference.

`candidate/` preserves experiments; standard setup does not select them or enable the experimental classifier. Do not set `TRUSTGRAPH_MODEL_DIR` or `TRUSTGRAPH_CLASSIFIER` for the baseline demo. Original weights and bands are unchanged. Only load trusted joblib artifacts: pickle-based files can execute code. Versions are pinned to the tested runtime. Synthetic training and observed false negatives/positives limit reliability; review scores are not calibrated fraud probabilities.

Vercel configuration now includes the baseline CPU scam assets and synthetic precedent fixture. Isolated local bundle inference passed, but a cloud build/deployment has not been verified. Candidate models, private data and optional media weights remain excluded.

**The AI-written text model**, `models/text_detector/`: distilroberta-base fine-tuned on human vs AI text by
`python train_text.py`. The website's `POST /api/text/ai-check` uses it (folder: `AI_TEXT_MODEL_DIR`).

**The deepfake model's trained layer**, `models/efficientnet_head.pt` (~6 KB), made by `python train_video.py` or
`python scripts/train_efficientnet_head.py --data path/to/faces` (`faces/real/...`, `faces/fake/...`). The website's
`POST /api/video/analyze` and the extension's media check (`POST /api/media/check`) use it (file:
`EFFICIENTNET_HEAD_PATH`).

## How the website uses them

Optional media/text engines are in `backend/app/ai/` and are reached through `TrustGraphAI.analyze` in
`backend/app/services/ai_model.py`. Those checks give a score only when both are true:

1. the AI packages are installed: `python -m pip install -r ai/requirements-ai.txt`
2. its trained model above exists

Otherwise it answers "pending AI integration; no score was produced". No score is ever made up. Restart the server
after training so it loads the new model. `AI_THRESHOLD` (default 0.5) sets where a score counts as AI-written / fake.

## EfficientNet-B0 (Hugging Face)

- **The pretrained model downloads on first use.** `google/efficientnet-b0` is public (~21 MB, no token or API key)
  and is cached by the `transformers` library.
- **It doesn't spot deepfakes on its own.** It was trained on 1,000 everyday ImageNet objects. It turns each face into
  1,280 numbers; the real/fake decision comes from your trained layer on top.
- Each video: 16 frames spread over the whole clip, the largest face in each (OpenCV), each face scored, then
  averaged. No face in any frame means no score.
- To check it on one image:

  ```
  python scripts/try_efficientnet_modes.py --image some_face.jpg
  python scripts/try_efficientnet_modes.py --random-weights      # plumbing check, no download
  ```
