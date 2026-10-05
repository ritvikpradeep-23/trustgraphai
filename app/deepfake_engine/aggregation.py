"""Turn per-face scores into one verdict for the whole video.

Statistics: mean, median, max, and the fake-frame ratio (share of faces
scoring at or above FRAME_FAKE_THRESHOLD).

Decision rule:
- no face in any frame        -> "inconclusive" (nothing was checked, so we
                                 must not say "likely_real")
- fake-frame ratio >= VIDEO_FAKE_RATIO_THRESHOLD -> "likely_fake"
- otherwise                   -> "likely_real"

The ratio decides rather than the max, because one odd frame (motion blur, a
bad crop) shouldn't flag a whole video. Confidence is how far the average
score leans toward the chosen answer: mean score for likely_fake, 1 - mean
for likely_real.
"""
from statistics import median

from app.config import Settings


def aggregate(scores: list[float], frames_examined: int, settings: Settings) -> dict:
    if not scores:
        return {"result": "inconclusive", "confidence": 0.0, "frames_examined": frames_examined,
                "faces_examined": 0, "fake_frame_ratio": 0.0,
                "mean_score": None, "median_score": None, "max_score": None}
    mean = sum(scores) / len(scores)
    ratio = sum(s >= settings.frame_fake_threshold for s in scores) / len(scores)
    fake = ratio >= settings.video_fake_ratio_threshold
    return {
        "result": "likely_fake" if fake else "likely_real",
        "confidence": round(mean if fake else 1.0 - mean, 3),
        "frames_examined": frames_examined,
        "faces_examined": len(scores),
        "fake_frame_ratio": round(ratio, 3),
        "mean_score": round(mean, 3),
        "median_score": round(median(scores), 3),
        "max_score": round(max(scores), 3),
    }
