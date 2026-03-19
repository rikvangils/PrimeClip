from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ObservationWindow, PerformanceSnapshot, PerformanceSource, Platform, PublicationJob
from app.integrations.analytics import (
    AnalyticsAdapterError,
    fetch_buffer_metrics,
    fetch_instagram_metrics,
    fetch_tiktok_metrics,
)
from app.review.schemas import PerformanceSnapshotIngestRequest


@dataclass(slots=True)
class PerformanceIngestResult:
    snapshot_id: str
    publication_job_id: str
    source: str
    observation_window: str
    performance_score: float | None
    normalized_metrics: dict[str, float | None] | None
    score_components: dict[str, float | str | None] | None
    adapter_warning: str | None


@dataclass(slots=True)
class PerformanceSnapshotDetail:
    performance_snapshot_id: str
    publication_job_id: str
    source: str
    observation_window: str
    observed_at: datetime
    views: int | None
    likes: int | None
    comments: int | None
    shares: int | None
    saves: int | None
    follows_lift: int | None
    normalized_metrics: dict[str, float | None] | None
    score_components: dict[str, float | str | None] | None
    performance_score: float | None


WINDOW_BASELINE = {
    ObservationWindow.one_hour: 0.75,
    ObservationWindow.twenty_four_hours: 1.0,
    ObservationWindow.forty_eight_hours: 1.1,
}

PLATFORM_BASELINE = {
    Platform.instagram: 1.0,
    Platform.tiktok: 1.15,
}


def _time_slot_baseline(scheduled_at: datetime | None) -> tuple[str, float]:
    if scheduled_at is None:
        return "unknown", 1.0

    hour = scheduled_at.hour
    if 18 <= hour < 21:
        return "18:00-21:00", 1.1
    if 15 <= hour < 18:
        return "15:00-18:00", 1.05
    if 12 <= hour < 15:
        return "12:00-15:00", 1.0
    return "off_peak", 0.9


def _safe_ratio(numerator: float, denominator: float) -> float:
    return round(numerator / max(denominator, 1.0), 6)


def _normalize_metrics(
    metrics: dict[str, int | None],
    platform: Platform,
    observation_window: ObservationWindow,
    scheduled_at: datetime | None,
) -> tuple[dict[str, float | None], dict[str, float | str | None]]:
    views = float(metrics.get("views") or 0)
    likes = float(metrics.get("likes") or 0)
    comments = float(metrics.get("comments") or 0)
    shares = float(metrics.get("shares") or 0)
    saves = float(metrics.get("saves") or 0)
    follows_lift = float(metrics.get("follows_lift") or 0)

    platform_baseline = PLATFORM_BASELINE.get(platform, 1.0)
    window_baseline = WINDOW_BASELINE.get(observation_window, 1.0)
    time_slot_label, time_slot_baseline = _time_slot_baseline(scheduled_at)
    baseline_denominator = platform_baseline * window_baseline * time_slot_baseline

    normalized = {
        "view_velocity": round((_safe_ratio(views, 1000.0) / baseline_denominator), 4) if views else None,
        "engagement_rate": round((_safe_ratio(likes + comments, views) / baseline_denominator), 4) if views else None,
        "share_rate": round((_safe_ratio(shares, views) / baseline_denominator), 4) if views else None,
        "save_rate": round((_safe_ratio(saves, views) / baseline_denominator), 4) if views else None,
        "follow_lift": round((_safe_ratio(follows_lift, views) / baseline_denominator), 4) if views else None,
        "completion_proxy": round((_safe_ratio(comments + saves + shares, views) / baseline_denominator), 4)
        if views
        else None,
        "search_discovery_lift": round((_safe_ratio(shares + saves, views) / baseline_denominator), 4) if views else None,
    }

    components = {
        "platform_baseline": platform_baseline,
        "window_baseline": window_baseline,
        "time_slot_baseline": time_slot_baseline,
        "time_slot": time_slot_label,
        "baseline_denominator": round(baseline_denominator, 4),
    }
    return normalized, components


def _compute_performance_score(
    normalized_metrics: dict[str, float | None],
    baseline_components: dict[str, float | str | None],
) -> tuple[float | None, dict[str, float | str | None]]:
    if normalized_metrics.get("view_velocity") is None:
        components = dict(baseline_components)
        components["reason"] = "views missing; normalized score unavailable"
        return None, components

    weighted = {
        "view_velocity": round((normalized_metrics.get("view_velocity") or 0.0) * 0.30, 4),
        "engagement_rate": round((normalized_metrics.get("engagement_rate") or 0.0) * 0.20, 4),
        "share_rate": round((normalized_metrics.get("share_rate") or 0.0) * 0.15, 4),
        "save_rate": round((normalized_metrics.get("save_rate") or 0.0) * 0.10, 4),
        "follow_lift": round((normalized_metrics.get("follow_lift") or 0.0) * 0.10, 4),
        "completion_proxy": round((normalized_metrics.get("completion_proxy") or 0.0) * 0.10, 4),
        "search_discovery_lift": round((normalized_metrics.get("search_discovery_lift") or 0.0) * 0.05, 4),
    }
    total = round(sum(weighted.values()) * 100.0, 4)
    components = dict(baseline_components)
    components.update(weighted)
    components["formula"] = "0.30*view_velocity + 0.20*engagement_rate + 0.15*share_rate + 0.10*save_rate + 0.10*follow_lift + 0.10*completion_proxy + 0.05*search_discovery_lift"
    return total, components

    views = float(metrics.get("views") or 0)
    likes = float(metrics.get("likes") or 0)
    comments = float(metrics.get("comments") or 0)
    shares = float(metrics.get("shares") or 0)
    saves = float(metrics.get("saves") or 0)
    follows_lift = float(metrics.get("follows_lift") or 0)

    # Baseline weighted engagement score for Sprint 4.
    raw = likes * 1.0 + comments * 1.8 + shares * 2.3 + saves * 1.2 + follows_lift * 3.0
    return round((raw / max(views, 1.0)) * 100.0, 4)


def _pull_metrics(source: PerformanceSource, publication: PublicationJob) -> tuple[dict[str, int | None], str | None]:
    buffer_post_id = publication.buffer_post_id or ""
    try:
        if source == PerformanceSource.buffer:
            return fetch_buffer_metrics(buffer_post_id), None
        if source == PerformanceSource.instagram:
            return fetch_instagram_metrics(buffer_post_id), None
        return fetch_tiktok_metrics(buffer_post_id), None
    except AnalyticsAdapterError as exc:
        # Failure-tolerant path for unavailable adapters.
        empty = {
            "views": None,
            "likes": None,
            "comments": None,
            "shares": None,
            "saves": None,
            "follows_lift": None,
        }
        return empty, str(exc)


def ingest_performance_snapshot(
    db: Session,
    publication_job_id: str,
    payload: PerformanceSnapshotIngestRequest,
) -> PerformanceIngestResult:
    publication = db.scalar(select(PublicationJob).where(PublicationJob.id == publication_job_id))
    if publication is None:
        raise ValueError(f"Publication job not found: {publication_job_id}")

    if payload.mode == "manual":
        metrics = {
            "views": payload.views,
            "likes": payload.likes,
            "comments": payload.comments,
            "shares": payload.shares,
            "saves": payload.saves,
            "follows_lift": payload.follows_lift,
        }
        warning = None
    else:
        metrics, warning = _pull_metrics(payload.source, publication)

    observed_at = payload.observed_at or datetime.now(timezone.utc)
    normalized_metrics, baseline_components = _normalize_metrics(
        metrics=metrics,
        platform=publication.platform,
        observation_window=payload.observation_window,
        scheduled_at=publication.scheduled_at,
    )
    performance_score, score_components = _compute_performance_score(normalized_metrics, baseline_components)

    snapshot = PerformanceSnapshot(
        publication_job_fk=publication.id,
        source=payload.source,
        observed_at=observed_at,
        observation_window=payload.observation_window,
        views=metrics.get("views"),
        likes=metrics.get("likes"),
        comments=metrics.get("comments"),
        shares=metrics.get("shares"),
        saves=metrics.get("saves"),
        follows_lift=metrics.get("follows_lift"),
        normalized_metrics=normalized_metrics,
        score_components=score_components,
        performance_score=performance_score,
        created_at=datetime.now(timezone.utc),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return PerformanceIngestResult(
        snapshot_id=str(snapshot.id),
        publication_job_id=publication_job_id,
        source=snapshot.source.value,
        observation_window=snapshot.observation_window.value,
        performance_score=float(snapshot.performance_score) if snapshot.performance_score is not None else None,
        normalized_metrics=snapshot.normalized_metrics,
        score_components=snapshot.score_components,
        adapter_warning=warning,
    )


def get_performance_snapshot_detail(db: Session, performance_snapshot_id: str) -> PerformanceSnapshotDetail:
    snapshot = db.scalar(select(PerformanceSnapshot).where(PerformanceSnapshot.id == performance_snapshot_id))
    if snapshot is None:
        raise ValueError(f"Performance snapshot not found: {performance_snapshot_id}")

    return PerformanceSnapshotDetail(
        performance_snapshot_id=str(snapshot.id),
        publication_job_id=str(snapshot.publication_job_fk),
        source=snapshot.source.value,
        observation_window=snapshot.observation_window.value,
        observed_at=snapshot.observed_at,
        views=snapshot.views,
        likes=snapshot.likes,
        comments=snapshot.comments,
        shares=snapshot.shares,
        saves=snapshot.saves,
        follows_lift=snapshot.follows_lift,
        normalized_metrics=snapshot.normalized_metrics,
        score_components=snapshot.score_components,
        performance_score=float(snapshot.performance_score) if snapshot.performance_score is not None else None,
    )