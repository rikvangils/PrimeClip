from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CandidateSegment, Platform, RenderedClip, SourceVideo


@dataclass(slots=True)
class SchedulingRecommendation:
    rendered_clip_id: str
    recommended_platform: Platform
    recommended_time_slot: str
    confidence: float
    rationale: list[str]


def _choose_platform(authenticity_score: float | None, ranking_score: float) -> tuple[Platform, list[str]]:
    reasons: list[str] = []

    score = authenticity_score if authenticity_score is not None else 0.0
    if score >= 80 and ranking_score >= 0.75:
        reasons.append("High authenticity and ranking suggest broader discovery potential")
        return Platform.tiktok, reasons

    if score >= 70:
        reasons.append("Strong authenticity score suitable for short-form recommendation feeds")
        return Platform.instagram, reasons

    reasons.append("Conservative platform choice due to moderate confidence")
    return Platform.instagram, reasons


def _choose_time_slot(source_title: str, ranking_score: float) -> tuple[str, list[str]]:
    reasons: list[str] = []

    title_lower = source_title.lower()
    if "stream" in title_lower or "live" in title_lower:
        reasons.append("Source appears stream-like; evening audience window prioritized")
        return "18:00-21:00", reasons

    if ranking_score >= 0.8:
        reasons.append("High-ranking moment prioritized for peak afternoon window")
        return "15:00-18:00", reasons

    reasons.append("Default reliability window selected for baseline distribution")
    return "12:00-15:00", reasons


def get_scheduling_recommendation(db: Session, rendered_clip_id: str) -> SchedulingRecommendation:
    row = db.execute(
        select(RenderedClip, CandidateSegment, SourceVideo)
        .join(CandidateSegment, CandidateSegment.id == RenderedClip.candidate_segment_fk)
        .join(SourceVideo, SourceVideo.id == CandidateSegment.source_video_fk)
        .where(RenderedClip.id == rendered_clip_id)
    ).first()

    if row is None:
        raise ValueError(f"Rendered clip not found: {rendered_clip_id}")

    clip, segment, source = row

    platform, platform_reasons = _choose_platform(
        authenticity_score=clip.authenticity_score,
        ranking_score=segment.ranking_score,
    )
    slot, slot_reasons = _choose_time_slot(source_title=source.title, ranking_score=segment.ranking_score)

    confidence_base = (clip.authenticity_score or 0.0) / 100.0
    confidence = min(0.95, max(0.35, round(confidence_base * 0.7 + segment.ranking_score * 0.3, 2)))

    return SchedulingRecommendation(
        rendered_clip_id=rendered_clip_id,
        recommended_platform=platform,
        recommended_time_slot=slot,
        confidence=confidence,
        rationale=platform_reasons + slot_reasons,
    )