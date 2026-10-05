# models/

Two things live here.

**The original TrustGraph detector's files** (`anomaly_isolation_forest.joblib`, `risk_bands.json`, `candidate/`).
These are used by `src/trustgraph` and the demo website. The backend in `app/` doesn't use them.

**The deepfake video model for the backend API.** It is *not* included: no weights are bundled.
To enable `POST /api/video/analyze`:

1. Put a TorchScript model here, e.g. `models/deepfake.pt`.
2. Set `DEEPFAKE_MODEL_PATH=models/deepfake.pt` in `.env`.
3. Restart the server. `GET /health` shows `"deepfake_model": "configured"`.

What the adapter (`app/deepfake_engine/model.py`) expects from the model:

- **Input:** one face crop as a float tensor of shape `1 x 3 x S x S`. It is RGB, scaled to 0-1, then normalised
  with the ImageNet mean `(0.485, 0.456, 0.406)` and std `(0.229, 0.224, 0.225)`. `S` is `DEEPFAKE_INPUT_SIZE`
  (default 224). If your model was trained with different preprocessing, change `_preprocess` to match.
- **Output:** either one logit (sigmoid gives the fake probability) or two logits `[real, fake]` (softmax, index 1
  is "fake").

Without a model file the endpoint answers `503 {"error": "model_not_configured"}` and never makes up a score.
`DEEPFAKE_MOCK=1` switches on a fake model for demos only; every answer it gives contains `"mock": true`.
