from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import (
    CandidateSegment,
    CreativeFingerprint,
    ObservationWindow,
    OptimizationRecommendation,
    Platform,
    PublicationJob,
    RecommendationDimension,
    RenderedClip,
    PerformanceSnapshot,
)


@dataclass(slots=True)
class RecommendationResult:
    recommendation_id: str
    dimension: str
    recommended_value: str
    platform: str | None
    observation_window: str
    expected_uplift: float | None
    confidence: float
    rationale: str
    evidence: dict | None
    created_at: object


def _candidate_dimensions(fingerprint: CreativeFingerprint | None, publication: PublicationJob) -> dict[RecommendationDimension, str | None]:
    return {
        RecommendationDimension.hook_pattern: fingerprint.hook_pattern if fingerprint else None,
        RecommendationDimension.caption_pack_version: fingerprint.caption_pack_version if fingerprint else None,
        RecommendationDimension.font_pack_version: fingerprint.font_pack_version if fingerprint else None,
        RecommendationDimension.publish_time_slot: fingerprint.publish_time_slot if fingerprint else None,
        RecommendationDimension.platform: publication.platform.value,
    }


def generate_recommendations(
    db: Session,
    observation_window: ObservationWindow,
    platform: Platform | None = None,
    minimum_samples: int = 1,
) -> list[RecommendationResult]:
    statement = (
        select(PerformanceSnapshot, PublicationJob, RenderedClip, CreativeFingerprint)
        .join(PublicationJob, PublicationJob.id == PerformanceSnapshot.publication_job_fk)
        .join(RenderedClip, RenderedClip.id == PublicationJob.rendered_clip_fk)
        .outerjoin(CreativeFingerprint, CreativeFingerprint.rendered_clip_fk == RenderedClip.id)
        .where(PerformanceSnapshot.observation_window == observation_window)
    )
    if platform is not None:
        statement = statement.where(PublicationJob.platform == platform)

    rows = db.execute(statement).all()
    if not rows:
        return []

    overall_scores: list[float] = []
    grouped: dict[tuple[RecommendationDimension, str, str | None], list[float]] = defaultdict(list)
    for snapshot, publication, _clip, fingerprint in rows:
        if snapshot.performance_score is None:
            continue

        score = float(snapshot.performance_score)
        overall_scores.append(score)
        values = _candidate_dimensions(fingerprint, publication)
        for dimension, value in values.items():
            if not value:
                continue
            grouped[(dimension, value, publication.platform.value)].append(score)

    if not overall_scores:
        return []

    overall_avg = sum(overall_scores) / len(overall_scores)

    if platform is not None:
        db.execute(
            delete(OptimizationRecommendation).where(
                OptimizationRecommendation.observation_window == observation_window,
                OptimizationRecommendation.platform == platform,
            )
        )
    else:
        db.execute(
            delete(OptimizationRecommendation).where(
                OptimizationRecommendation.observation_window == observation_window,
            )
        )
    db.commit()

    created: list[OptimizationRecommendation] = []
    for (dimension, value, recommendation_platform), scores in grouped.items():
        if len(scores) < minimum_samples:
            continue

        average_score = sum(scores) / len(scores)
        expected_uplift = round(average_score - overall_avg, 4)
        if expected_uplift <= 0:
            continue

        confidence = round(min(0.95, 0.4 + 0.1 * len(scores) + min(expected_uplift / 20.0, 0.25)), 2)
        rationale = (
            f"{dimension.value}={value} overperformed the baseline average by {expected_uplift:.2f} "
            f"points across {len(scores)} sample(s)."
        )
        record = OptimizationRecommendation(
            dimension=dimension,
            recommended_value=value,
            platform=Platform(recommendation_platform) if recommendation_platform else None,
            observation_window=observation_window,
            expected_uplift=expected_uplift,
            confidence=confidence,
            rationale=rationale,
            evidence={
                "sample_count": len(scores),
                "average_score": round(average_score, 4),
                "baseline_average": round(overall_avg, 4),
            },
        )
        db.add(record)
        created.append(record)

    db.commit()
    for record in created:
        db.refresh(record)

    return [
        RecommendationResult(
            recommendation_id=str(record.id),
            dimension=record.dimension.value,
            recommended_value=record.recommended_value,
            platform=record.platform.value if record.platform else None,
            observation_window=record.observation_window.value,
            expected_uplift=record.expected_uplift,
            confidence=record.confidence,
            rationale=record.rationale,
            evidence=record.evidence,
            created_at=record.created_at,
        )
        for record in created
    ]


def list_recommendations(
    db: Session,
    observation_window: ObservationWindow | None = None,
    platform: Platform | None = None,
    limit: int = 100,
) -> list[RecommendationResult]:
    statement = select(OptimizationRecommendation).order_by(
        OptimizationRecommendation.confidence.desc(),
        OptimizationRecommendation.expected_uplift.desc().nullslast(),
        OptimizationRecommendation.created_at.desc(),
    ).limit(limit)

    if observation_window is not None:
        statement = statement.where(OptimizationRecommendation.observation_window == observation_window)
    if platform is not None:
        statement = statement.where(OptimizationRecommendation.platform == platform)

    rows = db.scalars(statement).all()
    return [
        RecommendationResult(
            recommendation_id=str(record.id),
            dimension=record.dimension.value,
            recommended_value=record.recommended_value,
            platform=record.platform.value if record.platform else None,
            observation_window=record.observation_window.value,
            expected_uplift=record.expected_uplift,
            confidence=record.confidence,
            rationale=record.rationale,
            evidence=record.evidence,
            created_at=record.created_at,
        )
        for record in rows
    ]