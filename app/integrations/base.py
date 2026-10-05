"""The contract every messaging-platform adapter (Telegram, WhatsApp, ...) follows.

Adapters are transport only: they turn a platform's incoming message into
NormalizedContent, send it to this API, and post the API's answer back. They
contain no scam or deepfake logic, so every channel gets the same verdicts.
No real platform code lives here yet.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

ContentType = Literal["text", "video", "image", "audio"]


@dataclass(frozen=True)
class NormalizedContent:
    source: str                       # which channel it came from, e.g. "telegram"
    content_type: ContentType
    text: str | None = None           # message text, for content_type "text"
    media_url: str | None = None      # where to fetch the media, for video/image/audio
    external_message_id: str | None = None  # the platform's own id, to reply to the right message


class PlatformAdapter(ABC):
    """Subclass once per platform."""

    source: str  # set by each subclass, e.g. "telegram"

    @abstractmethod
    def normalize(self, raw_update: dict) -> NormalizedContent | None:
        """Turn the platform's raw incoming payload into NormalizedContent.
        Return None for updates that aren't something to check (joins, edits...)."""

    @abstractmethod
    def send_reply(self, content: NormalizedContent, reply_text: str) -> None:
        """Post the verdict back to the user on the platform."""
