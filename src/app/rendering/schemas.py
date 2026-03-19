from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RenderProfile:
    width: int = 1080
    height: int = 1920
    fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    crf: int = 21
    preset: str = "veryfast"


@dataclass(slots=True)
class RenderResult:
    rendered_clip_id: str
    output_path: str
    status: str