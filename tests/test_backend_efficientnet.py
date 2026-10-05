"""EfficientNet integration. Uses an UNTRAINED EfficientNet-B0 of the real
shape (no download), so these tests check the wiring, not detection quality."""
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
import torch
from fastapi.testclient import TestClient

from app.config import Settings
from app.deepfake_engine import efficientnet_wrapper as effnet
from app.deepfake_engine.combined_model import (CombinedDeepfakeModel, EfficientNetDeepfakeModel, new_head,
                                                save_head)
from app.deepfake_engine.model import DeepfakeModel, TorchScriptDeepfakeModel, load_deepfake_model
from app.main import create_app

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
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
def mine_file(tmp_path):
    path = tmp_path / "mine.pt"
    (tmp_path / "mine_src.py").write_text(
        "import torch\n"
        "class Mine(torch.nn.Module):\n"
        "    def forward(self, x):\n"
        "        return x.mean(dim=(1, 2, 3)).unsqueeze(1) * 0 + 2.0\n")
    sys.path.insert(0, str(tmp_path))
    from mine_src import Mine  # TorchScript needs the class in a real .py file
    torch.jit.save(torch.jit.script(Mine()), str(path))
    return path


class Fixed(DeepfakeModel):
    def __init__(self, score):
        self.score = score

    def predict_fake_score(self, face_bgr):
        return self.score


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


def test_combined_modes():
    mine, eff = Fixed(0.9), Fixed(0.3)
    assert CombinedDeepfakeModel("mine", mine, None).predict_fake_score(FACE) == 0.9
    assert CombinedDeepfakeModel("efficientnet", None, eff).predict_fake_score(FACE) == 0.3
    both = CombinedDeepfakeModel("both", mine, eff, weight_mine=0.75)
    assert both.predict_fake_score(FACE) == pytest.approx(0.75 * 0.9 + 0.25 * 0.3)
    assert both.scores_by_branch(FACE) == {"mine": 0.9, "efficientnet": 0.3}
    with pytest.raises(ValueError):
        CombinedDeepfakeModel("both", mine, None)
    with pytest.raises(ValueError):
        CombinedDeepfakeModel("everything", mine, eff)


def test_loader_respects_mode_and_never_invents_a_model(tmp_path, head_file, mine_file):
    missing = str(tmp_path / "missing.pt")
    assert load_deepfake_model(Settings(deepfake_mode="efficientnet", efficientnet_head_path=missing))[1] == "not_configured"
    model, status = load_deepfake_model(Settings(deepfake_mode="efficientnet", efficientnet_head_path=str(head_file)))
    assert status == "configured" and isinstance(model, EfficientNetDeepfakeModel)
    assert load_deepfake_model(Settings(deepfake_mode="both", efficientnet_head_path=str(head_file)))[1] == "not_configured"
    model, status = load_deepfake_model(Settings(deepfake_mode="both", efficientnet_head_path=str(head_file),
                                                 deepfake_model_path=str(mine_file)))
    assert status == "configured" and isinstance(model, CombinedDeepfakeModel)
    model, status = load_deepfake_model(Settings(deepfake_model_path=str(mine_file)))  # default mode = mine
    assert status == "configured" and isinstance(model, TorchScriptDeepfakeModel)


def test_api_with_efficientnet_mode(tmp_path, head_file):
    class NoEmbedder:
        is_loaded = False

    class AlwaysFindsFace:
        def largest_face(self, frame):
            return frame
    settings = Settings(reports_path=str(tmp_path / "r.json"), deepfake_mode="efficientnet",
                        efficientnet_head_path=str(head_file))
    client = TestClient(create_app(settings, embedder=NoEmbedder()))
    client.app.state.face_detector = AlwaysFindsFace()
    video = tmp_path / "v.mp4"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 10, (96, 72))
    for i in range(20):
        writer.write(np.full((72, 96, 3), i * 10, np.uint8))
    writer.release()
    with open(video, "rb") as f:
        body = client.post("/api/video/analyze", files={"file": ("v.mp4", f, "video/mp4")}).json()
    assert body["faces_examined"] == 2 and body["result"] in ("likely_fake", "likely_real") and "mock" not in body
    health = client.get("/health").json()
    assert health["deepfake_model"] == "configured" and health["deepfake_mode"] == "efficientnet"


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


def test_demo_script_runs_all_three_modes(tmp_path, monkeypatch, capsys, mine_file, head_file):
    monkeypatch.setenv("DEEPFAKE_MODEL_PATH", str(mine_file))
    monkeypatch.setenv("EFFICIENTNET_HEAD_PATH", str(head_file))
    try_efficientnet_modes.main([])
    out = capsys.readouterr().out
    assert "[mine] fake score" in out and "[efficientnet] fake score" in out and "[both] fake score" in out
