from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class SourceVideoPayload:
    source_video_id: str
    channel_id: str
    title: str
    url: str
    published_at: datetime | None = None


@dataclass(slots=True)
class IngestGateDecision:
    allowed: bool
    reason: str | None = None


@dataclass(slots=True)
class TranscriptSegment:
    start_ts: float
    end_ts: float
    text: str


@dataclass(slots=True)
class AudioMarker:
    timestamp: float
    intensity: float


@dataclass(slots=True)
class SceneCut:
    timestamp: float
    confidence: float