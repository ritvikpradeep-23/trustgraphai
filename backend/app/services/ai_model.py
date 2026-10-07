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
        """A trained engine's answer when one is installed (app.ai.engines),
        otherwise an explicit unavailable result. Never an invented score."""
        answer = None
        if capability == "scam":
            answer = self._scam(payload)
        elif capability == "ai_content":
            answer = self._ai_content(payload)
        return answer or self._unavailable(capability)

    # ---- trained engines (only used when their model files exist) ----------
    def _scam(self, payload: Any) -> DetectionResult | None:
        # Model-only adapter for legacy callers. The website's /api/detect still
        # performs database comparison first; this service has no DB session.
        from app.ai.scam_engine import analyze
        if not isinstance(payload, dict):
            return None
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip() or len(text) > 20000:
            return None
        result = analyze(text, payload.get("sender"), payload.get("url"))
        if result is None:
            return None
        signals = result["signals"]
        return DetectionResult(
            anomaly=signals.get("anomaly"), continuity=signals.get("continuity"),
            similarity=signals.get("similarity"), precedent=signals.get("precedent"),
            risk_score=result["score"], risk_level=result["level"], reasons=result["reasons"],
            available=True, model="original-scam-engine")

    def _ai_content(self, payload: Any) -> DetectionResult | None:
        from app.ai import engines
        text = (payload or {}).get("text") if isinstance(payload, dict) else None
        if not text or not text.strip() or engines.text_engine() is None:
            return None
        score = engines.score_text(text)
        level = "LIKELY_AI" if score >= engines.threshold() else "LIKELY_HUMAN"
        return DetectionResult(
            anomaly=None, continuity=None, similarity=None, precedent=None,
            risk_score=round(score, 4), risk_level=level, available=True,
            model="distilroberta-base fine-tuned on human vs AI text (ai/models/text_detector)",
            reasons=[f"AI-written score {score:.0%} from the fine-tuned text model. "
                     "AI-written is not the same as a scam, and short messages carry little evidence."],
        )

    def _unavailable(self, capability: str) -> DetectionResult:
        """Explicit unavailable result: no engine installed for this capability."""
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
