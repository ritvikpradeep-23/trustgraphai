"""Pick frames out of a video, spread evenly from start to end.

Neighbouring frames are nearly identical, so looking at every frame would
cost a lot and add little. Sampling also keeps request time predictable.

extract_frames(path, sample_fps, max_frames)  about sample_fps frames per second
                                              of video, capped at max_frames, spread
                                              over the WHOLE video (a 60 s clip with
                                              a cap of 30 is not just its first 30 s)
extract_evenly(path, n)                       exactly n frames spread over the video
                                              (also used by video_detector.py, so the
                                              accuracy routine samples like the API)
"""
import cv2
import numpy as np


def _read(cap, wanted: set[int] | None, limit: int) -> list[np.ndarray]:
    """Read in order and keep the wanted frame numbers. Reading sequentially is
    used instead of seeking: seeking in MP4 is often inaccurate in OpenCV, and
    grab() skips frames cheaply. wanted=None means "the first `limit` frames"."""
    frames, index = [], 0
    while len(frames) < limit and cap.grab():
        if wanted is None or index in wanted:
            ok, frame = cap.retrieve()
            if ok:
                frames.append(frame)
        index += 1
    return frames


def _spread(total: int, n: int) -> set[int]:
    """n frame numbers spread evenly from the first frame to the last."""
    return set(np.linspace(0, total - 1, num=n).round().astype(int).tolist())


def extract_evenly(path: str, n: int) -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(path))
    try:
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if total <= 0:  # frame count unknown (some streams): take the first n
            return _read(cap, None, n)
        n = min(n, total)
        return _read(cap, _spread(total, n), n)
    finally:
        cap.release()


def extract_frames(path: str, sample_fps: float, max_frames: int) -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(path))
    try:
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 0
        if total > 0 and video_fps > 0:
            n = min(max_frames, total, max(1, round(total / video_fps * sample_fps)))
            return _read(cap, _spread(total, n), n)
        # Frame count or rate unknown: every k-th frame from the start, as before.
        step = max(1, round((video_fps or 1.0) / sample_fps))
        frames, index = [], 0
        while len(frames) < max_frames and cap.grab():
            if index % step == 0:
                ok, frame = cap.retrieve()
                if ok:
                    frames.append(frame)
            index += 1
        return frames
    finally:
        cap.release()
