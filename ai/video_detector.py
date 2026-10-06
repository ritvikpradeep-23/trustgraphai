"""Step 4: deepfake video detector = EfficientNet-B0 (frozen) + your layer on top.

For one video:
  1. sample N frames spread evenly over the whole video
  2. crop the largest face in each frame (OpenCV face detector, with a margin)
  3. EfficientNet-B0 turns each face into 1280 features; your trained layer
     (the "head" from app/deepfake_engine/combined_model.py) gives a fake score
  4. the video score is the average of its frame scores

    python video_detector.py some_video.mp4          # prints the fake score

It uses the head saved by train_video.py (models/efficientnet_head.pt by
default), the same file the API uses with DEEPFAKE_MODE=efficientnet.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import torch

# The AI engine (EfficientNet-B0 + your layer) lives in backend/app/ai, shared with the server.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))  # the website backend holds the engine code

from app.ai import efficientnet_wrapper as effnet  # noqa: E402
from app.ai.combined_model import EfficientNetDeepfakeModel  # noqa: E402
from app.ai.engines import FACE_MARGIN  # noqa: E402  (same crop margin as the server)
from app.ai.face_detector import FaceDetector  # noqa: E402
from app.ai.frame_extractor import extract_evenly  # noqa: E402
from detection_common import best_device, load_config, resolve  # noqa: E402


def sample_frames(path: str, n: int) -> list[np.ndarray]:
    """n frames spread evenly from start to end (not just the first seconds).
    Same function the API uses, so the routine measures what the API does."""
    return extract_evenly(path, n)


def center_crop(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    side = min(h, w)
    y, x = (h - side) // 2, (w - side) // 2
    return frame[y:y + side, x:x + side]


def face_crops(path: str, n_frames: int, detector: FaceDetector) -> tuple[list[np.ndarray], bool]:
    """(face crops, faces_found). If no frame has a detectable face, the centre
    of each frame is used instead and faces_found is False, so a report can
    count those videos instead of silently treating them like the others."""
    frames = sample_frames(path, n_frames)
    crops = [c for c in (detector.largest_face(f) for f in frames) if c is not None]
    if crops:
        return crops, True
    return [center_crop(f) for f in frames], False


def pixel_batch(crops: list[np.ndarray], model_id: str) -> torch.Tensor:
    """EfficientNet's own preprocessing for a list of BGR crops."""
    processor, _ = effnet.load(model_id)
    return processor(images=[effnet.to_pil(c) for c in crops], return_tensors="pt")["pixel_values"]


class VideoDetector:
    def __init__(self, head_path: str | None = None, frames: int | None = None, device: str | None = None):
        cfg = load_config()["video"]
        self.head_path = str(resolve(head_path or cfg["model_path"]))
        self.frames = frames or cfg["frames_per_video"]
        self.device = device or best_device()
        self.model = EfficientNetDeepfakeModel(self.head_path)  # backbone frozen, as trained
        self.model.backbone.to(self.device)
        self.model.head.to(self.device)
        self.faces = FaceDetector(FACE_MARGIN)

    def frame_scores(self, crops: list[np.ndarray], batch_size: int = 32) -> list[float]:
        scores = []
        with torch.inference_mode():
            for i in range(0, len(crops), batch_size):
                pix = pixel_batch(crops[i:i + batch_size], self.model.model_id).to(self.device)
                logits = self.model.head(self.model.backbone(pixel_values=pix).pooler_output)
                scores += torch.sigmoid(logits).squeeze(1).cpu().tolist()
        return scores

    def score_video(self, path: str) -> dict:
        """{'score': average fake score 0-1, 'frames': n, 'faces_found': bool}"""
        crops, found = face_crops(path, self.frames, self.faces)
        if not crops:
            raise ValueError(f"could not read any frames from {path}")
        scores = self.frame_scores(crops)
        return {"score": float(np.mean(scores)), "frames": len(scores), "faces_found": found}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--head", help="trained head file (default: video.model_path in detection_config.json)")
    args = ap.parse_args(argv)
    result = VideoDetector(args.head).score_video(args.video)
    verdict = "likely fake" if result["score"] >= 0.5 else "likely real"
    print(f"{args.video}: fake score {result['score']:.3f} ({verdict}), {result['frames']} frames, "
          f"faces found: {result['faces_found']}")
    return result


if __name__ == "__main__":
    sys.exit(main() and 0)
