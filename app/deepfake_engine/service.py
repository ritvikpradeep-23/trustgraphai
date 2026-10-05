"""Video -> frames -> largest face per frame -> score each face -> verdict."""
import logging

from app.config import Settings
from app.deepfake_engine.aggregation import aggregate
from app.deepfake_engine.face_detector import FaceDetector
from app.deepfake_engine.frame_extractor import extract_frames
from app.deepfake_engine.model import DeepfakeModel

logger = logging.getLogger("trustgraph.deepfake")


def analyze_video(path: str, model: DeepfakeModel, detector: FaceDetector, settings: Settings) -> dict:
    frames = extract_frames(path, settings.video_sample_fps, settings.video_max_frames)
    faces = [face for face in (detector.largest_face(f) for f in frames) if face is not None]
    scores = [model.predict_fake_score(face) for face in faces]
    result = aggregate(scores, len(frames), settings)
    logger.info("video: %d frames, %d faces, mean=%s max=%s -> %s", result["frames_examined"],
                result["faces_examined"], result["mean_score"], result["max_score"], result["result"])
    if model.is_mock:
        result["mock"] = True
    return result
