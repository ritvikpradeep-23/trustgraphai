"""The AI engines inside the website backend (backend/app/ai) and how the
TrustGraphAI slot uses them. Uses an UNTRAINED EfficientNet-B0 of the real
shape and a tiny random text model (no download), so these tests check the
wiring, never detection quality."""
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
import torch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai import efficientnet_wrapper as effnet
from app.ai import engines
from app.ai.combined_model import EfficientNetDeepfakeModel, new_head, save_head
from app.api.ai_detectors import router as ai_detectors_router
from app.services.ai_model import TrustGraphAI
from test_detection_routine import tiny_text_model

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import train_efficientnet_head  # noqa: E402
import try_efficientnet_modes  # noqa: E402

FACE = np.random.default_rng(0).integers(0, 255, (120, 100, 3), dtype=np.uint8)


@pytest.fixture(autouse=True)
def untrained_b0(monkeypatch):
    """Put an untrained B0 in the wrapper's cache so nothing is downloaded."""
    monkeypatch.setattr(effnet, "_loaded", {})
    try_efficientnet_modes.use_random_weights(effnet.MODEL_ID)


@pytest.fixture
def head_file(tmp_path):
    torch.manual_seed(0)
    path = tmp_path / "efficientnet_head.pt"
    save_head(new_head(), str(path), note="random")
    return path


@pytest.fixture
def client():
    """Only the AI routes of the website: they need no database."""
    app = FastAPI()
    app.include_router(ai_detectors_router, prefix="/api")
    return TestClient(app)


class AlwaysFindsFace:
    def largest_face(self, frame):
        return frame


class NeverFindsFace:
    def largest_face(self, frame):
        return None


def small_video(path: Path) -> Path:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (96, 72))
    for i in range(20):
        writer.write(np.full((72, 96, 3), i * 10, np.uint8))
    writer.release()
    return path


# ---------------------------------------------------------------- EfficientNet
def test_wrapper_gives_1280_features_and_imagenet_labels():
    assert effnet.extract_features(FACE).shape == (1280,)
    assert effnet.extract_features(effnet.to_pil(FACE)).shape == (1280,)
    top = effnet.classify_imagenet(FACE, top_k=3)
    assert len(top) == 3 and top[0][1] >= top[1][1] >= top[2][1]


def test_wrapper_loads_the_model_once():
    assert effnet.load() is effnet.load()


def test_backbone_frozen_by_default_and_last_blocks_can_unfreeze(head_file):
    model = EfficientNetDeepfakeModel(str(head_file))
    assert not any(p.requires_grad for p in model.backbone.parameters())
    assert 0.0 <= model.predict_fake_score(FACE) <= 1.0
    model.unfreeze_last_blocks(2)
    blocks = model.backbone.encoder.blocks
    assert all(p.requires_grad for p in blocks[-1].parameters())
    assert not any(p.requires_grad for p in blocks[0].parameters())
    model.freeze_backbone()  # don't leave the shared cached model unfrozen


def _tiny_dataset(root: Path):
    rng = np.random.default_rng(1)
    for label, base in (("real", 60), ("fake", 190)):
        for video in range(3):
            folder = root / label / f"video{video}"
            folder.mkdir(parents=True)
            for frame in range(2):
                img = np.clip(base + rng.normal(0, 20, (64, 64, 3)), 0, 255).astype(np.uint8)
                cv2.imwrite(str(folder / f"f{frame}.png"), img)


def test_training_keeps_videos_together_and_saves_a_loadable_head(tmp_path):
    _tiny_dataset(tmp_path / "faces")
    items = train_efficientnet_head.find_images(tmp_path / "faces")
    train, val = train_efficientnet_head.split_by_group(items, 0.34, seed=0)
    assert not {g for _, _, g in train} & {g for _, _, g in val}  # no video on both sides
    out = tmp_path / "head.pt"
    metrics = train_efficientnet_head.main(["--data", str(tmp_path / "faces"), "--out", str(out), "--epochs", "20",
                                            "--val-share", "0.34"])
    assert "accuracy" in metrics
    assert 0.0 <= EfficientNetDeepfakeModel(str(out)).predict_fake_score(FACE) <= 1.0


def test_finetuned_backbone_is_saved_and_kept_separate(tmp_path):
    _tiny_dataset(tmp_path / "faces")
    out = tmp_path / "head_ft.pt"
    train_efficientnet_head.main(["--data", str(tmp_path / "faces"), "--out", str(out), "--epochs", "1",
                                  "--unfreeze-last", "1", "--val-share", "0.34"])
    assert "backbone_state_dict" in torch.load(out, weights_only=True)
    _, shared = effnet.load()
    model = EfficientNetDeepfakeModel(str(out))
    assert model.backbone is not shared.efficientnet  # private copy; the shared model is unchanged
    for p in shared.efficientnet.parameters():
        p.requires_grad = False


def test_demo_script_with_and_without_a_trained_layer(tmp_path, monkeypatch, capsys, head_file):
    monkeypatch.setenv("EFFICIENTNET_HEAD_PATH", str(head_file))
    try_efficientnet_modes.main([])
    assert "fake score:" in capsys.readouterr().out
    monkeypatch.setenv("EFFICIENTNET_HEAD_PATH", str(tmp_path / "missing.pt"))
    try_efficientnet_modes.main([])
    out = capsys.readouterr().out
    assert "no deepfake score" in out and "\nfake score:" not in out


# ------------------------------------------------- the TrustGraphAI slot
def test_no_trained_models_gives_the_exact_pending_answers(client, tmp_path):
    text = client.post("/api/text/ai-check", json={"text": "ordinary text"}).json()
    assert text["ai_written_score"] is None and text["available"] is False
    assert text["reasons"] == ["AI-content analysis is pending AI integration; no score was produced."]
    with open(small_video(tmp_path / "v.mp4"), "rb") as f:
        video = client.post("/api/video/analyze", files={"file": ("v.mp4", f, "video/mp4")}).json()
    assert video["fake_score"] is None and video["available"] is False
    assert video["reasons"] == ["Video analysis is pending AI integration; no score was produced."]


def test_trained_text_model_answers_ai_check(client, tmp_path, monkeypatch):
    texts = ["hello there my friend", "as an ai language model i can help", "see you at six tonight"]
    monkeypatch.setenv("AI_TEXT_MODEL_DIR", str(tiny_text_model(tmp_path / "text_model", texts)))
    engines.reset()
    body = client.post("/api/text/ai-check", json={"text": "hello there my friend"}).json()
    assert body["available"] is True and 0.0 <= body["ai_written_score"] <= 1.0
    assert "distilroberta" in body["model"]
    # empty text: nothing to judge, so the pending answer, not a score
    result = TrustGraphAI().analyze("ai_content", {"text": "   "})
    assert result.risk_score is None and result.risk_level == "PENDING"


def test_trained_head_answers_video_analyze(client, tmp_path, monkeypatch, head_file):
    monkeypatch.setenv("EFFICIENTNET_HEAD_PATH", str(head_file))
    engines.reset()
    engines.video_engine()["faces"] = AlwaysFindsFace()  # the drawn frames have no real face
    with open(small_video(tmp_path / "v.mp4"), "rb") as f:
        body = client.post("/api/video/analyze", files={"file": ("v.mp4", f, "video/mp4")}).json()
    assert body["available"] is True and 0.0 <= body["fake_score"] <= 1.0
    assert "EfficientNet-B0" in body["model"] and "16 frame(s)" in body["reasons"][0]
    # frames from the extension's media check (PIL images) use the same engine
    from PIL import Image
    result = TrustGraphAI().analyze("image", {"images": [Image.fromarray(FACE)]})
    assert result.available and result.risk_level in ("LIKELY_FAKE", "LIKELY_REAL")


def test_no_face_means_no_score(monkeypatch, head_file):
    monkeypatch.setenv("EFFICIENTNET_HEAD_PATH", str(head_file))
    engines.reset()
    engines.video_engine()["faces"] = NeverFindsFace()
    result = TrustGraphAI().analyze("video", {"images": [FACE, FACE]})
    assert result.risk_score is None and result.risk_level == "INCONCLUSIVE" and result.available


def test_unreadable_upload_gives_no_score(tmp_path, monkeypatch, head_file):
    monkeypatch.setenv("EFFICIENTNET_HEAD_PATH", str(head_file))
    engines.reset()
    bad = tmp_path / "bad.mp4"
    bad.write_bytes(b"not a video")
    with open(bad, "rb") as f:
        result = TrustGraphAI().analyze("video", {"file": f, "filename": "bad.mp4"})
    assert result.risk_score is None and result.risk_level in ("ERROR", "INCONCLUSIVE")
