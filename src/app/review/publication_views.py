from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    CandidateSegment,
    PerformanceSnapshot,
    Platform,
    PublicationJob,
    PublishStatus,
    RenderedClip,
    SourceVideo,
)
from app.review.schemas import PublicationCalendarDay, PublicationListItem


def _snapshot_summary(db: Session, publication_job_id: str) -> tuple[int, datetime | None]:
    row = db.execute(
        select(func.count(PerformanceSnapshot.id), func.max(PerformanceSnapshot.observed_at)).where(
            PerformanceSnapshot.publication_job_fk == publication_job_id
        )
    ).first()
    if not row:
        return 0, None
    count, latest = row
    return int(count or 0), latest


def list_publication_jobs(
    db: Session,
    status: PublishStatus | None = None,
    platform: Platform | None = None,
    limit: int = 100,
) -> list[PublicationListItem]:
    statement = (
        select(PublicationJob, RenderedClip, CandidateSegment, SourceVideo)
        .join(RenderedClip, RenderedClip.id == PublicationJob.rendered_clip_fk)
        .join(CandidateSegment, CandidateSegment.id == RenderedClip.candidate_segment_fk)
        .join(SourceVideo, SourceVideo.id == CandidateSegment.source_video_fk)
        .order_by(PublicationJob.scheduled_at.desc().nullslast(), PublicationJob.created_at.desc())
        .limit(limit)
    )

    if status is not None:
        statement = statement.where(PublicationJob.publish_status == status)
    if platform is not None:
        statement = statement.where(PublicationJob.platform == platform)

    rows = db.execute(statement).all()
    items: list[PublicationListItem] = []
    for publication, clip, _segment, source in rows:
        snapshot_count, last_snapshot_at = _snapshot_summary(db, str(publication.id))
        items.append(
            PublicationListItem(
                publication_job_id=str(publication.id),
                rendered_clip_id=str(clip.id),
                source_title=source.title,
                distribution_provider=publication.distribution_provider.value,
                platform=publication.platform.value,
                publish_status=publication.publish_status.value,
                scheduled_at=publication.scheduled_at,
                external_post_ref=publication.external_post_ref,
                buffer_post_id=publication.buffer_post_id,
                performance_snapshot_count=snapshot_count,
                last_snapshot_at=last_snapshot_at,
            )
        )

    return items


def publication_calendar(
    db: Session,
    status: PublishStatus | None = None,
    platform: Platform | None = None,
    limit: int = 200,
) -> list[PublicationCalendarDay]:
    items = list_publication_jobs(db=db, status=status, platform=platform, limit=limit)
    grouped: dict[str, list[PublicationListItem]] = defaultdict(list)

    for item in items:
        if item.scheduled_at is None:
            day_key = "unscheduled"
        else:
            day_key = item.scheduled_at.date().isoformat()
        grouped[day_key].append(item)

    days: list[PublicationCalendarDay] = []
    for key in sorted(grouped.keys()):
        days.append(PublicationCalendarDay(date=key, items=grouped[key]))
    return days