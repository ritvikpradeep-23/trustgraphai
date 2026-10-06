from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SubmissionSource(str, Enum):
    BROWSER_EXTENSION = "browser_extension"
    WEB_APP = "web_app"


class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LINK = "link"
    MULTIMODAL = "multimodal"


class Submission(BaseModel):
    submission_id: Optional[str] = None
    source: SubmissionSource
    content_type: ContentType

    text: Optional[str] = None
    caption: Optional[str] = None
    url: Optional[str] = None
    media_reference: Optional[str] = None

    sender: Optional[str] = None
    source_timestamp: Optional[datetime] = None

    user_consent: bool = True
    created_at: datetime
