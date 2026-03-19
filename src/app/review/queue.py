from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import (
    CandidateSegment,
    CreativeFingerprint,
    Platform,
    PublicationJob,
    PublishStatus,
    RenderedClip,
    ReviewStatus,
    SourceVideo,
)
from app.review.schemas import ReviewDecisionAction, ReviewQueueItem


def _apply_filters(
    statement: Select,
    status: ReviewStatus | None,
    risk_only: bool,
    platform: Platform | None,
) -> Select:
    if status is not None:
        statement = statement.where(RenderedClip.review_status == status)

    if risk_only:
        statement = statement.where(
            (RenderedClip.last_error.is_not(None)) | (RenderedClip.authenticity_score.is_(None))
        )

    # Platform-specific filtering will be tightened once publication prefill data exists (E4-S2).
    if platform is not None:
        _ = platform

    return statement


def _risk_flags(clip: RenderedClip) -> list[str]:
    flags: list[str] = []
    if clip.authenticity_score is None:
        flags.append("missing_authenticity_score")
    elif clip.authenticity_score < 70:
        flags.append("low_authenticity_score")

    if clip.last_error:
        flags.append("processing_error")

    if clip.retry_count > 1:
        flags.append("high_retry_count")

    return flags


def _latest_publication_job(db: Session, rendered_clip_id: str) -> PublicationJob | None:
    return db.scalar(
        select(PublicationJob)
        .where(PublicationJob.rendered_clip_fk == rendered_clip_id)
        .order_by(PublicationJob.created_at.desc())
        .limit(1)
    )


def list_review_queue(
    db: Session,
    status: ReviewStatus | None = None,
    risk_only: bool = False,
    platform: Platform | None = None,
    limit: int = 50,
) -> list[ReviewQueueItem]:
    statement = (
        select(RenderedClip, CandidateSegment, SourceVideo, CreativeFingerprint)
        .join(CandidateSegment, CandidateSegment.id == RenderedClip.candidate_segment_fk)
        .join(SourceVideo, SourceVideo.id == CandidateSegment.source_video_fk)
        .outerjoin(CreativeFingerprint, CreativeFingerprint.rendered_clip_fk == RenderedClip.id)
        .order_by(RenderedClip.created_at.desc())
        .limit(limit)
    )

    statement = _apply_filters(statement, status=status, risk_only=risk_only, platform=platform)
    rows = db.execute(statement).all()

    items: list[ReviewQueueItem] = []
    for clip, segment, source, fingerprint in rows:
        publication = _latest_publication_job(db, str(clip.id))
        flags = _risk_flags(clip)
        if publication and publication.publish_status == PublishStatus.failed:
            flags.append("publish_failed")

        item = ReviewQueueItem(
            rendered_clip_id=str(clip.id),
            review_status=clip.review_status.value,
            authenticity_score=clip.authenticity_score,
            render_path=clip.render_path,
            source_video_id=source.source_video_id,
            source_title=source.title,
            source_url=source.url,
            ranking_score=segment.ranking_score,
            start_ts=segment.start_ts,
            end_ts=segment.end_ts,
            hook_pattern=fingerprint.hook_pattern if fingerprint else None,
            caption_pack_version=fingerprint.caption_pack_version if fingerprint else None,
            font_pack_version=fingerprint.font_pack_version if fingerprint else None,
            transition_pack_version=fingerprint.transition_pack_version if fingerprint else None,
            animation_pack_version=fingerprint.animation_pack_version if fingerprint else None,
            distribution_provider=publication.distribution_provider.value if publication else None,
            external_post_ref=publication.external_post_ref if publication else None,
            publish_status=publication.publish_status.value if publication else None,
            buffer_post_id=publication.buffer_post_id if publication else None,
            risk_flags=flags,
        )
        items.append(item)

    return items


def apply_review_decision(db: Session, rendered_clip_id: str, action: ReviewDecisionAction) -> RenderedClip:
    clip = db.scalar(select(RenderedClip).where(RenderedClip.id == rendered_clip_id))
    if clip is None:
        raise ValueError(f"Rendered clip not found: {rendered_clip_id}")

    if action == ReviewDecisionAction.approve:
        clip.review_status = ReviewStatus.approved
        clip.last_error = None
    elif action == ReviewDecisionAction.revise:
        clip.review_status = ReviewStatus.revise
        clip.last_error = "Operator requested revision"
    else:
        clip.review_status = ReviewStatus.rejected
        clip.last_error = "Operator rejected clip"

    db.add(clip)
    db.commit()
    db.refresh(clip)
    return clip