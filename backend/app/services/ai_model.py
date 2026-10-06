"""Single provider-agnostic boundary for all future AI capabilities."""

from dataclasses import dataclass
from typing import Any


@dataclass
class DetectionResult:
    anomaly: float | None
    continuity: float | None
    similarity: float | None
    precedent: float | None
    risk_score: float | None
    risk_level: str
    reasons: list[str]
    available: bool = False
    model: str = "AI integration pending"


class TrustGraphAI:
    """
    Route all AI capabilities through ``analyze``. A future implementation
    belongs behind this interface; no provider or model is assumed here.
    """

    def predict(
        self,
        channel: str,
        sender: str | None,
        text: str,
        url: str | None,
    ) -> DetectionResult:
        return self.analyze("scam", {"channel": channel, "sender": sender, "text": text, "url": url})

    def analyze(self, capability: str, payload: Any) -> DetectionResult:
        """Return an explicit unavailable result until an AI is supplied."""
        reasons = {
            "scam": "Scam analysis is pending AI integration; no score was produced.",
            "ai_content": "AI-content analysis is pending AI integration; no score was produced.",
            "image": "Image analysis is pending AI integration; no score was produced.",
            "audio": "Audio analysis is pending AI integration; no score was produced.",
            "video": "Video analysis is pending AI integration; no score was produced.",
            "multimodal": "Multimodal analysis is pending AI integration; no score was produced.",
        }
        return DetectionResult(
            anomaly=None, continuity=None, similarity=None, precedent=None,
            risk_score=None, risk_level="PENDING",
            reasons=[reasons.get(capability, "AI analysis is pending integration; no score was produced.")],
            available=False,
        )
