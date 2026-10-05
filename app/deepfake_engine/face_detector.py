"""Find the face to check in each frame.

Uses OpenCV's built-in Haar cascade: no download, fast on CPU, good enough
for front-facing faces (it misses strong side profiles). Only the LARGEST
face per frame is used: in a call or a selfie video that is the speaker, and
background faces would just add noise.
"""
import cv2
import numpy as np


def crop_with_margin(frame: np.ndarray, box: tuple[int, int, int, int], margin: float) -> np.ndarray:
    """Crop box (x, y, w, h) plus `margin` of the face size on every side,
    clipped to the frame. Deepfake artefacts often sit at the face's edges
    (hairline, jaw), so a tight crop would hide them."""
    x, y, w, h = box
    pad = int(round(margin * max(w, h)))
    height, width = frame.shape[:2]
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(width, x + w + pad), min(height, y + h + pad)
    return frame[y0:y1, x0:x1].copy()


class FaceDetector:
    def __init__(self, margin: float):
        self.margin = margin
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self._cascade = cv2.CascadeClassifier(path)
        if self._cascade.empty():
            raise RuntimeError(f"OpenCV face detector not found at {path}")

    def largest_face(self, frame: np.ndarray) -> np.ndarray | None:
        gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        boxes = self._cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
        if len(boxes) == 0:
            return None
        biggest = max(boxes, key=lambda b: b[2] * b[3])
        return crop_with_margin(frame, tuple(int(v) for v in biggest), self.margin)
