# models/

Three things live here. None of the trained AI weights are committed: you make them on your own computer.

**The scam engine's files** (`anomaly_isolation_forest.joblib`, `risk_bands.json`, `candidate/`). These are used by
`src/trustgraph`, the accuracy and learning routines, and the demo website (`run_website.py`).

**The AI-written text model**, `models/text_detector/`: distilroberta-base fine-tuned on human vs AI text by
`python train_text.py`. The website's `POST /api/text/ai-check` uses it (folder: `AI_TEXT_MODEL_DIR`).

**The deepfake model's trained layer**, `models/efficientnet_head.pt` (~6 KB), made by `python train_video.py` or
`python scripts/train_efficientnet_head.py --data path/to/faces` (`faces/real/...`, `faces/fake/...`). The website's
`POST /api/video/analyze` and the extension's media check (`POST /api/media/check`) use it (file:
`EFFICIENTNET_HEAD_PATH`).

## How the website uses them

The engines are in `backend/app/ai/` and are reached only through `TrustGraphAI.analyze` in
`backend/app/services/ai_model.py`. A check gives a score only when both are true:

1. the AI packages are installed: `python -m pip install -r requirements-ai.txt`
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
