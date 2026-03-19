from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class YouTubeUpload:
    source_video_id: str
    channel_id: str
    title: str
    url: str
    published_at: datetime | None = None