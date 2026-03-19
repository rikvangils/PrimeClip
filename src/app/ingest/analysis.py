from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import SourceAnalysisSignal, SourceVideo
from app.ingest.schemas import AudioMarker, SceneCut, TranscriptSegment


def _to_transcript_payload(segments: list[TranscriptSegment]) -> list[dict]:
    return [
        {"start_ts": s.start_ts, "end_ts": s.end_ts, "text": s.text}
        for s in segments
    ]


def _to_audio_payload(markers: list[AudioMarker]) -> list[dict]:
    return [{"timestamp": m.timestamp, "intensity": m.intensity} for m in markers]


def _to_scene_payload(cuts: list[SceneCut]) -> list[dict]:
    return [{"timestamp": c.timestamp, "confidence": c.confidence} for c in cuts]


def _build_fallback_transcript(title: str) -> list[TranscriptSegment]:
    return [
        TranscriptSegment(start_ts=0.0, end_ts=12.0, text=f"Hook moment: {title}"),
        TranscriptSegment(start_ts=30.0, end_ts=50.0, text="Funny reaction and chat spike"),
        TranscriptSegment(start_ts=75.0, end_ts=95.0, text="Unexpected moment, audience laughs"),
        TranscriptSegment(start_ts=120.0, end_ts=145.0, text="Clutch or fail sequence"),
        TranscriptSegment(start_ts=180.0, end_ts=205.0, text="Best stream highlight recap"),
    ]


def _build_fallback_audio_markers() -> list[AudioMarker]:
    return [
        AudioMarker(timestamp=34.0, intensity=0.78),
        AudioMarker(timestamp=82.0, intensity=0.86),
        AudioMarker(timestamp=133.0, intensity=0.74),
        AudioMarker(timestamp=192.0, intensity=0.91),
    ]


def _build_fallback_scene_cuts() -> list[SceneCut]:
    return [
        SceneCut(timestamp=12.0, confidence=0.65),
        SceneCut(timestamp=48.0, confidence=0.72),
        SceneCut(timestamp=92.0, confidence=0.69),
        SceneCut(timestamp=146.0, confidence=0.70),
        SceneCut(timestamp=206.0, confidence=0.66),
    ]


def extract_media_analysis_signals(
    db: Session,
    source_video_id: str,
    transcript_segments: list[TranscriptSegment] | None = None,
    audio_markers: list[AudioMarker] | None = None,
    scene_cuts: list[SceneCut] | None = None,
) -> SourceAnalysisSignal:
    """
    Persist transcript/audio/scene-level signals for a source video.

    The service accepts injected signals (for future real processors) and falls back
    to deterministic placeholder signals to keep Sprint 1 flow executable.
    """
    source_video = db.scalar(select(SourceVideo).where(SourceVideo.source_video_id == source_video_id))
    if not source_video:
        raise ValueError(f"Source video not found for analysis: {source_video_id}")

    segments = transcript_segments or _build_fallback_transcript(source_video.title)
    markers = audio_markers or _build_fallback_audio_markers()
    cuts = scene_cuts or _build_fallback_scene_cuts()

    signal = db.scalar(
        select(SourceAnalysisSignal).where(SourceAnalysisSignal.source_video_fk == source_video.id)
    )

    if signal is None:
        signal = SourceAnalysisSignal(
            source_video_fk=source_video.id,
            transcript_segments=_to_transcript_payload(segments),
            audio_markers=_to_audio_payload(markers),
            scene_cuts=_to_scene_payload(cuts),
        )
        db.add(signal)
    else:
        signal.transcript_segments = _to_transcript_payload(segments)
        signal.audio_markers = _to_audio_payload(markers)
        signal.scene_cuts = _to_scene_payload(cuts)

    db.commit()
    db.refresh(signal)
    return signal