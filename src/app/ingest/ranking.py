from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import CandidateSegment, SourceAnalysisSignal, SourceVideo


FUNNY_KEYWORDS = ("haha", "lol", "wtf", "no way", "funny", "laugh")


def _score_segment(segment: dict, audio_markers: list[dict], scene_cuts: list[dict]) -> float:
    start = float(segment.get("start_ts", 0.0))
    end = float(segment.get("end_ts", start + 10.0))
    text = str(segment.get("text", "")).lower()

    text_bonus = 0.0
    if any(keyword in text for keyword in FUNNY_KEYWORDS):
        text_bonus += 0.2

    midpoint = start + ((end - start) / 2)

    audio_bonus = 0.0
    for marker in audio_markers:
        marker_ts = float(marker.get("timestamp", -1.0))
        if abs(marker_ts - midpoint) <= 8.0:
            audio_bonus = max(audio_bonus, float(marker.get("intensity", 0.0)) * 0.5)

    scene_bonus = 0.0
    for cut in scene_cuts:
        cut_ts = float(cut.get("timestamp", -1.0))
        if start <= cut_ts <= end:
            scene_bonus = max(scene_bonus, float(cut.get("confidence", 0.0)) * 0.3)

    base = 0.35
    return round(base + text_bonus + audio_bonus + scene_bonus, 4)


def rank_candidate_moments(db: Session, source_video_id: str, min_segments: int = 5) -> list[CandidateSegment]:
    """Generate ranked candidate moments from stored source analysis signals."""
    source_video = db.scalar(select(SourceVideo).where(SourceVideo.source_video_id == source_video_id))
    if not source_video:
        raise ValueError(f"Source video not found for ranking: {source_video_id}")

    signals = db.scalar(
        select(SourceAnalysisSignal).where(SourceAnalysisSignal.source_video_fk == source_video.id)
    )
    if not signals:
        raise ValueError(f"No analysis signals found for source video: {source_video_id}")

    transcript_segments = signals.transcript_segments or []
    audio_markers = signals.audio_markers or []
    scene_cuts = signals.scene_cuts or []

    if not transcript_segments:
        transcript_segments = [
            {"start_ts": i * 30.0, "end_ts": (i * 30.0) + 18.0, "text": "fallback segment"}
            for i in range(min_segments)
        ]

    scored: list[dict] = []
    for segment in transcript_segments:
        score = _score_segment(segment, audio_markers, scene_cuts)
        scored.append(
            {
                "start_ts": float(segment.get("start_ts", 0.0)),
                "end_ts": float(segment.get("end_ts", 15.0)),
                "ranking_score": score,
            }
        )

    scored.sort(key=lambda item: item["ranking_score"], reverse=True)

    # Keep stable top-N slice while ensuring at least min_segments candidates.
    selected = scored[: max(min_segments, len(scored))]
    if len(selected) < min_segments:
        last_end = selected[-1]["end_ts"] if selected else 0.0
        for _ in range(min_segments - len(selected)):
            start = last_end + 5.0
            end = start + 15.0
            selected.append({"start_ts": start, "end_ts": end, "ranking_score": 0.35})
            last_end = end

    db.execute(delete(CandidateSegment).where(CandidateSegment.source_video_fk == source_video.id))

    result: list[CandidateSegment] = []
    for item in selected[: max(min_segments, 5)]:
        candidate = CandidateSegment(
            source_video_fk=source_video.id,
            start_ts=item["start_ts"],
            end_ts=item["end_ts"],
            ranking_score=item["ranking_score"],
        )
        db.add(candidate)
        result.append(candidate)

    db.commit()
    for candidate in result:
        db.refresh(candidate)
    return result