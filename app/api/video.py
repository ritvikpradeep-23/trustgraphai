"""POST /api/video/analyze: multipart upload of one MP4 (form field "file")."""
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Request, UploadFile

from app.deepfake_engine.service import analyze_video
from app.deepfake_engine.validation import check_name, check_video, save_with_limit
from app.errors import ApiError
from app.schemas import ErrorOut, VideoAnalysisOut

router = APIRouter(prefix="/api/video", tags=["video"])


@router.post("/analyze", response_model=VideoAnalysisOut, response_model_exclude_none=True,
             responses={413: {"model": ErrorOut}, 415: {"model": ErrorOut}, 422: {"model": ErrorOut},
                        503: {"model": ErrorOut}})
def analyze(request: Request, file: UploadFile = File(...)) -> dict:
    state = request.app.state
    settings = state.settings
    # Without a model we can't give an answer, and we never make one up.
    if state.deepfake_model is None:
        raise ApiError(503, "model_not_configured",
                       f"no deepfake model for DEEPFAKE_MODE={settings.deepfake_mode}: train one with "
                       "train_video.py and set DEEPFAKE_MODE=efficientnet, or set DEEPFAKE_MODEL_PATH "
                       "to your TorchScript model (see models/README.md)")
    check_name(file.filename)

    # The upload goes to a temporary file (OpenCV reads from a path) and is
    # always deleted afterwards, whether analysis succeeds or fails.
    fd, tmp = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    try:
        save_with_limit(file.file, Path(tmp), settings.video_max_bytes)
        check_video(Path(tmp), settings)
        return analyze_video(tmp, state.deepfake_model, state.face_detector, settings)
    finally:
        Path(tmp).unlink(missing_ok=True)
