from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CreativeFingerprint, ObservationWindow, PublicationJob, RenderedClip, PerformanceSnapshot
from app.review.recommendation_engine import list_recommendations


@dataclass(slots=True)
class InsightWinner:
    label: str
    average_score: float
    sample_count: int


@dataclass(slots=True)
class PlatformComparison:
    platform: str
    average_score: float
    sample_count: int


@dataclass(slots=True)
class InsightsDashboard:
    observation_window: str
    top_creative_winners: list[InsightWinner]
    best_posting_windows: list[InsightWinner]
    platform_comparison: list[PlatformComparison]
    suggested_next_actions: list[str]


def _top_grouped_scores(grouped: dict[str, list[float]], limit: int = 5) -> list[InsightWinner]:
    items: list[InsightWinner] = []
    for label, scores in grouped.items():
        if not scores:
            continue
        items.append(
            InsightWinner(
                label=label,
                average_score=round(sum(scores) / len(scores), 4),
                sample_count=len(scores),
            )
        )
    items.sort(key=lambda item: (item.average_score, item.sample_count), reverse=True)
    return items[:limit]


def get_insights_dashboard(
    db: Session,
    observation_window: ObservationWindow = ObservationWindow.twenty_four_hours,
) -> InsightsDashboard:
    rows = db.execute(
        select(PerformanceSnapshot, PublicationJob, RenderedClip, CreativeFingerprint)
        .join(PublicationJob, PublicationJob.id == PerformanceSnapshot.publication_job_fk)
        .join(RenderedClip, RenderedClip.id == PublicationJob.rendered_clip_fk)
        .outerjoin(CreativeFingerprint, CreativeFingerprint.rendered_clip_fk == RenderedClip.id)
        .where(PerformanceSnapshot.observation_window == observation_window)
    ).all()

    creative_scores: dict[str, list[float]] = defaultdict(list)
    slot_scores: dict[str, list[float]] = defaultdict(list)
    platform_scores: dict[str, list[float]] = defaultdict(list)

    for snapshot, publication, _clip, fingerprint in rows:
        if snapshot.performance_score is None:
            continue

        score = float(snapshot.performance_score)
        platform_scores[publication.platform.value].append(score)

        if fingerprint and fingerprint.hook_pattern:
            creative_scores[f"hook:{fingerprint.hook_pattern}"].append(score)
        if fingerprint and fingerprint.caption_pack_version:
            creative_scores[f"caption:{fingerprint.caption_pack_version}"] .append(score)
        if fingerprint and fingerprint.font_pack_version:
            creative_scores[f"font:{fingerprint.font_pack_version}"] .append(score)
        if fingerprint and fingerprint.publish_time_slot:
            slot_scores[fingerprint.publish_time_slot].append(score)
        elif publication.scheduled_at is not None:
            hour = publication.scheduled_at.hour
            if 18 <= hour < 21:
                slot_scores["18:00-21:00"].append(score)
            elif 15 <= hour < 18:
                slot_scores["15:00-18:00"].append(score)
            elif 12 <= hour < 15:
                slot_scores["12:00-15:00"].append(score)
            else:
                slot_scores["off_peak"].append(score)

    top_winners = _top_grouped_scores(creative_scores)
    best_windows = _top_grouped_scores(slot_scores, limit=3)
    platform_comparison = [
        PlatformComparison(
            platform=platform,
            average_score=round(sum(scores) / len(scores), 4),
            sample_count=len(scores),
        )
        for platform, scores in sorted(platform_scores.items())
        if scores
    ]
    platform_comparison.sort(key=lambda item: item.average_score, reverse=True)

    recommendations = list_recommendations(db=db, observation_window=observation_window, limit=5)
    next_actions: list[str] = []
    for recommendation in recommendations[:3]:
        next_actions.append(
            f"Promote {recommendation.dimension}={recommendation.recommended_value} for {recommendation.observation_window} runs"
        )

    if not next_actions and top_winners:
        next_actions.append(f"Test more variants around current winner {top_winners[0].label}")
    if not next_actions and not rows:
        next_actions.append("Collect more performance snapshots before generating recommendations")

    return InsightsDashboard(
        observation_window=observation_window.value,
        top_creative_winners=top_winners,
        best_posting_windows=best_windows,
        platform_comparison=platform_comparison,
        suggested_next_actions=next_actions,
    )