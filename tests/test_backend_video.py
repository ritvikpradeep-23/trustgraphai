import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest
import torch
from fastapi.testclient import TestClient

from app.config import Settings
from app.deepfake_engine.aggregation import aggregate
from app.deepfake_engine.face_detector import FaceDetector, crop_with_margin
from app.deepfake_engine.frame_extractor import extract_frames
from app.deepfake_engine.model import MockDeepfakeModel, TorchScriptDeepfakeModel, load_deepfake_model
from app.main import create_app

# Sample per-face scores: a mostly-fake clip and a mostly-real clip.
FAKE_CLIP = [0.91, 0.87, 0.12, 0.95, 0.88, 0.79, 0.93, 0.15]
REAL_CLIP = [0.05, 0.12, 0.08, 0.61, 0.09, 0.11]


def make_mp4(path: Path, seconds: float, fps: int = 10, size=(96, 72)) -> Path:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    for i in range(int(seconds * fps)):
        writer.write(np.full((size[1], size[0], 3), (i * 7) % 255, np.uint8))
    writer.release()
    return path


class AlwaysFindsFace:
    """Stand-in detector: no real face images are available offline, so tests
    that need faces pretend the whole frame is one."""
    def largest_face(self, frame):
        return frame


class NoEmbedder:
    """The video tests never touch text; this keeps the real model from loading."""
    is_loaded = False


def client_with(tmp_path, **overrides):
    settings = Settings(reports_path=str(tmp_path / "r.json"), **overrides)
    return TestClient(create_app(settings, embedder=NoEmbedder())), settings


def upload(client, path, name="clip.mp4"):
    with open(path, "rb") as f:
        return client.post("/api/video/analyze", files={"file": (name, f, "video/mp4")})


# ------------------------------------------------------------ aggregation
def test_aggregation_on_a_mostly_fake_clip():
    out = aggregate(FAKE_CLIP, frames_examined=8, settings=Settings())
    assert out["result"] == "likely_fake"
    assert out["mean_score"] == pytest.approx(0.70) and out["median_score"] == pytest.approx(0.875)
    assert out["max_score"] == 0.95 and out["fake_frame_ratio"] == 0.75 and out["confidence"] == pytest.approx(0.70)


def test_aggregation_on_a_mostly_real_clip():
    out = aggregate(REAL_CLIP, frames_examined=6, settings=Settings())
    assert out["result"] == "likely_real" and out["fake_frame_ratio"] == pytest.approx(0.167)
    assert out["max_score"] == 0.61 and out["confidence"] == pytest.approx(0.823)


def test_one_odd_frame_does_not_flag_a_video():
    assert aggregate([0.1, 0.1, 0.99, 0.1], 4, Settings())["result"] == "likely_real"


def test_ratio_exactly_at_threshold_is_fake():
    assert aggregate([0.9, 0.1], 2, Settings(video_fake_ratio_threshold=0.5))["result"] == "likely_fake"


def test_no_faces_is_inconclusive():
    out = aggregate([], frames_examined=5, settings=Settings())
    assert out["result"] == "inconclusive" and out["faces_examined"] == 0 and out["frames_examined"] == 5


# ------------------------------------------------------------ pieces
def test_frames_sampled_about_one_per_second_and_capped(tmp_path):
    video = make_mp4(tmp_path / "v.mp4", seconds=5, fps=10)
    assert len(extract_frames(str(video), sample_fps=1.0, max_frames=30)) == 5
    assert len(extract_frames(str(video), sample_fps=1.0, max_frames=3)) == 3


def test_crop_adds_margin_and_stays_inside_the_frame():
    frame = np.zeros((100, 100, 3), np.uint8)
    assert crop_with_margin(frame, (40, 40, 20, 20), 0.5).shape[:2] == (40, 40)   # 10 px each side
    assert crop_with_margin(frame, (0, 0, 20, 20), 0.5).shape[:2] == (30, 30)     # clipped at the edge


def test_real_detector_finds_no_face_in_a_blank_frame():
    assert FaceDetector(0.2).largest_face(np.full((240, 320, 3), 128, np.uint8)) is None


def test_torchscript_adapter_handles_one_and_two_logits(tmp_path):
    class OneLogit(torch.nn.Module):
        def forward(self, x):
            return x.mean(dim=(1, 2, 3)).unsqueeze(1) * 0 + 2.0  # sigmoid(2) ~ 0.881

    class TwoLogits(torch.nn.Module):
        def forward(self, x):
            return torch.tensor([[0.0, 1.0]]).expand(x.shape[0], 2)  # softmax -> 0.731 fake

    face = np.full((50, 40, 3), 100, np.uint8)
    for module, expected in ((OneLogit(), 0.8808), (TwoLogits(), 0.7311)):
        path = tmp_path / f"{type(module).__name__}.pt"
        torch.jit.save(torch.jit.script(module), str(path))
        assert TorchScriptDeepfakeModel(str(path), 64).predict_fake_score(face) == pytest.approx(expected, abs=1e-3)


def test_model_loading_rules(tmp_path):
    assert load_deepfake_model(Settings())[1] == "not_configured"
    assert load_deepfake_model(Settings(deepfake_model_path=str(tmp_path / "missing.pt")))[1] == "not_configured"
    model, status = load_deepfake_model(Settings(deepfake_mock=True))
    assert status == "mock" and isinstance(model, MockDeepfakeModel)


# ------------------------------------------------------------ endpoint
def test_no_model_is_503_and_never_a_score(tmp_path):
    client, _ = client_with(tmp_path)
    r = upload(client, make_mp4(tmp_path / "v.mp4", 3))
    assert r.status_code == 503 and r.json()["error"] == "model_not_configured"
    assert client.get("/health").json()["deepfake_model"] == "not_configured"


def test_mock_blank_video_is_inconclusive_and_says_mock(tmp_path):
    client, _ = client_with(tmp_path, deepfake_mock=True)
    r = upload(client, make_mp4(tmp_path / "v.mp4", 4))
    body = r.json()
    assert r.status_code == 200 and body["mock"] is True
    assert body["result"] == "inconclusive" and body["frames_examined"] == 4 and body["faces_examined"] == 0
    assert set(body) == {"result", "confidence", "frames_examined", "faces_examined", "fake_frame_ratio", "mock"}


def test_mock_with_faces_gives_a_verdict_and_says_mock(tmp_path):
    client, _ = client_with(tmp_path, deepfake_mock=True)
    client.app.state.face_detector = AlwaysFindsFace()
    body = upload(client, make_mp4(tmp_path / "v.mp4", 3)).json()
    assert body["result"] in ("likely_fake", "likely_real") and body["faces_examined"] == 3 and body["mock"] is True


def test_real_torchscript_model_end_to_end_has_no_mock_flag(tmp_path):
    class Fake(torch.nn.Module):
        def forward(self, x):
            return x.mean(dim=(1, 2, 3)).unsqueeze(1) * 0 + 3.0  # every face ~0.95 fake
    path = tmp_path / "deepfake.pt"
    torch.jit.save(torch.jit.script(Fake()), str(path))
    client, _ = client_with(tmp_path, deepfake_model_path=str(path))
    client.app.state.face_detector = AlwaysFindsFace()
    body = upload(client, make_mp4(tmp_path / "v.mp4", 3)).json()
    assert body == {"result": "likely_fake", "confidence": pytest.approx(0.953, abs=1e-3), "frames_examined": 3,
                    "faces_examined": 3, "fake_frame_ratio": 1.0}
    assert client.get("/health").json()["deepfake_model"] == "configured"


@pytest.mark.parametrize("name, content, limits, status, error", [
    ("clip.avi", None, {}, 415, "unsupported_media_type"),
    ("clip.mp4", b"not a video at all", {}, 415, "unsupported_media_type"),
    ("clip.mp4", b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 200, {}, 422, "video_unreadable"),
    ("clip.mp4", None, {"video_max_bytes": 1000}, 413, "file_too_large"),
    ("clip.mp4", None, {"video_max_seconds": 2}, 422, "video_too_long"),
])
def test_bad_uploads_are_rejected(tmp_path, name, content, limits, status, error):
    client, _ = client_with(tmp_path, deepfake_mock=True, **limits)
    path = make_mp4(tmp_path / "v.mp4", 5) if content is None else tmp_path / "v.bin"
    if content is not None:
        path.write_bytes(content)
    r = upload(client, path, name)
    assert r.status_code == status and r.json()["error"] == error


def test_temporary_upload_is_deleted(tmp_path, monkeypatch):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(uploads))
    client, _ = client_with(tmp_path, deepfake_mock=True)
    upload(client, make_mp4(tmp_path / "ok.mp4", 2))                       # success
    upload(client, make_mp4(tmp_path / "long.mp4", 5), "long.mp4")         # fine too
    client2, _ = client_with(tmp_path, deepfake_mock=True, video_max_seconds=1)
    upload(client2, make_mp4(tmp_path / "toolong.mp4", 3))                 # rejected after saving
    assert list(uploads.iterdir()) == []
