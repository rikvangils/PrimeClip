from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import IngestJob, IngestStatus, JobStatus, SourceVideo
from app.ingest.schemas import IngestGateDecision, SourceVideoPayload


logger = logging.getLogger(__name__)


def _normalize_channel(value: str) -> str:
    return value.strip().lower()


def _is_channel_allowed(channel_id: str) -> bool:
    settings = get_settings()
    normalized = _normalize_channel(channel_id)
    allowed = {_normalize_channel(item) for item in settings.source_channel_whitelist}
    return normalized in allowed


def gate_source_for_ingest(db: Session, payload: SourceVideoPayload) -> IngestGateDecision:
    """Validate source channel before ingest and persist a rejection reason if blocked."""
    existing = db.scalar(select(SourceVideo).where(SourceVideo.source_video_id == payload.source_video_id))
    if existing:
        return IngestGateDecision(allowed=False, reason="duplicate_source_video_id")

    if _is_channel_allowed(payload.channel_id):
        source_video = SourceVideo(
            source_video_id=payload.source_video_id,
            channel_id=payload.channel_id,
            title=payload.title,
            url=payload.url,
            published_at=payload.published_at,
            ingest_status=IngestStatus.pending,
        )
        db.add(source_video)
        db.flush()

        ingest_job = IngestJob(
            source_video_fk=source_video.id,
            status=JobStatus.pending,
        )
        db.add(ingest_job)
        db.commit()
        return IngestGateDecision(allowed=True)

    reason = (
        "Source channel is not in whitelist. "
        f"channel_id={payload.channel_id} allowed={get_settings().source_channel_whitelist}"
    )
    logger.warning("ingest_rejected: %s", reason)

    source_video = SourceVideo(
        source_video_id=payload.source_video_id,
        channel_id=payload.channel_id,
        title=payload.title,
        url=payload.url,
        published_at=payload.published_at,
        ingest_status=IngestStatus.rejected,
    )
    db.add(source_video)
    db.flush()

    now = datetime.now(timezone.utc)
    ingest_job = IngestJob(
        source_video_fk=source_video.id,
        status=JobStatus.failed,
        started_at=now,
        finished_at=now,
        error_message=reason,
    )
    db.add(ingest_job)
    db.commit()

    return IngestGateDecision(allowed=False, reason=reason)