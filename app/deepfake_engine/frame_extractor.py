"""Pick frames out of a video: about one per second, with a hard cap.

Neighbouring frames are nearly identical, so looking at every frame would
cost a lot and add little. Sampling also keeps request time predictable.
"""
import cv2
import numpy as np


def extract_frames(path: str, sample_fps: float, max_frames: int) -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(path))
    try:
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 1.0
        step = max(1, round(video_fps / sample_fps))  # keep every `step`-th frame
        frames, index = [], 0
        # Read sequentially instead of seeking: seeking in MP4 is often
        # inaccurate in OpenCV, and grab() skips frames cheaply.
        while len(frames) < max_frames and cap.grab():
            if index % step == 0:
                ok, frame = cap.retrieve()
                if ok:
                    frames.append(frame)
            index += 1
        return frames
    finally:
        cap.release()
