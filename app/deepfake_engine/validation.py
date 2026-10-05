"""Check an uploaded video before doing any real work on it.

MP4 only (checked from the file's own bytes, not just its name, because
names and Content-Type headers are easy to fake), size limit while
streaming to disk, duration limit, and it must actually decode.
"""
from dataclasses import dataclass
from pathlib import Path

import cv2

from app.config import Settings
from app.errors import ApiError

CHUNK = 1024 * 1024  # copy uploads 1 MB at a time instead of loading them into memory


@dataclass
class VideoInfo:
    fps: float
    frame_count: int
    duration_seconds: float


def check_name(filename: str | None):
    if not filename or Path(filename).suffix.lower() != ".mp4":
        raise ApiError(415, "unsupported_media_type", "only .mp4 videos are accepted")


def save_with_limit(upload, dest: Path, max_bytes: int) -> int:
    """Copy the upload to dest, stopping as soon as it passes max_bytes."""
    size = 0
    with open(dest, "wb") as out:
        while chunk := upload.read(CHUNK):
            size += len(chunk)
            if size > max_bytes:
                raise ApiError(413, "file_too_large", f"at most {max_bytes // (1024 * 1024)} MB")
            out.write(chunk)
    if size == 0:
        raise ApiError(422, "empty_file", "the upload was empty")
    return size


def check_video(path: Path, settings: Settings) -> VideoInfo:
    # Every MP4 starts with a box whose type, at bytes 4-8, is "ftyp".
    with open(path, "rb") as f:
        head = f.read(12)
    if len(head) < 8 or head[4:8] != b"ftyp":
        raise ApiError(415, "unsupported_media_type", "the file is not an MP4 video")

    cap = cv2.VideoCapture(str(path))
    try:
        fps, frames = cap.get(cv2.CAP_PROP_FPS), int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        decodes = cap.isOpened() and cap.read()[0]
    finally:
        cap.release()
    if not decodes or fps <= 0 or frames <= 0:
        raise ApiError(422, "video_unreadable", "the video could not be decoded")
    duration = frames / fps
    if duration > settings.video_max_seconds:
        raise ApiError(422, "video_too_long", f"at most {settings.video_max_seconds:g} seconds")
    return VideoInfo(fps=fps, frame_count=frames, duration_seconds=duration)
