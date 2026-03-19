from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import DistributionProvider, Platform, PublicationJob, PublishStatus, RenderedClip, ReviewStatus
from app.integrations.buffer_client import BufferApiError, BufferClient
from app.integrations.tiktok_client import TikTokApiError, TikTokClient
from app.integrations.tiktok_oauth import TikTokOAuthError, get_tiktok_access_token, refresh_tiktok_access_token
from app.review.compliance import assert_clip_compliant


def _derive_caption_parts(caption: str) -> tuple[str, str, list[str]]:
    hashtags = re.findall(r"#\w+", caption)
    description = re.sub(r"#\w+", "", caption).strip()
    title = (description or caption or "Untitled clip")[:80].strip() or "Untitled clip"
    return title, description, hashtags


def _resolve_buffer_profile_id(platform: Platform) -> str:
    settings = get_settings()
    if platform == Platform.instagram:
        return settings.buffer_profile_id_instagram or ""
    return settings.buffer_profile_id_tiktok or ""


def _to_publish_status(buffer_status: str) -> PublishStatus:
    normalized = buffer_status.lower()
    if normalized in {"sent", "published", "posted"}:
        return PublishStatus.published
    if normalized in {"failed", "error"}:
        return PublishStatus.failed
    if normalized in {"publish_complete", "completed", "success"}:
        return PublishStatus.published
    if normalized in {"publish_failed", "processing_failed", "failure"}:
        return PublishStatus.failed
    if normalized in {"pending", "buffer", "scheduled"}:
        return PublishStatus.scheduled
    if normalized in {"processing_upload", "processing", "in_review", "queued"}:
        return PublishStatus.scheduled
    return PublishStatus.scheduled


def _create_manual_export(publication: PublicationJob, clip: RenderedClip, caption: str) -> str:
    settings = get_settings()
    export_dir = Path(settings.manual_publish_export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    export_path = export_dir / f"{publication.id}.json"
    title, description, hashtags = _derive_caption_parts(caption)
    export_payload = {
        "publication_job_id": str(publication.id),
        "rendered_clip_id": str(clip.id),
        "platform": publication.platform.value,
        "scheduled_at": publication.scheduled_at.isoformat() if publication.scheduled_at else None,
        "caption": caption,
        "title": title,
        "description": description,
        "hashtags": hashtags,
        "render_path": clip.render_path,
        "distribution_provider": publication.distribution_provider.value,
    }
    export_path.write_text(json.dumps(export_payload, indent=2), encoding="utf-8")
    return str(export_path)


def _is_tiktok_auth_error(exc: TikTokApiError) -> bool:
    text = str(exc).lower()
    return (
        "access_token_invalid" in text
        or "invalid token" in text
        or "missing tiktok access token" in text
        or "(401)" in text
        or "unauthorized" in text
    )


def schedule_clip_via_buffer(
    db: Session,
    rendered_clip_id: str,
    platform: Platform,
    scheduled_at: datetime,
    caption: str,
) -> PublicationJob:
    clip = db.scalar(select(RenderedClip).where(RenderedClip.id == rendered_clip_id))
    if clip is None:
        raise ValueError(f"Rendered clip not found: {rendered_clip_id}")
    if clip.review_status != ReviewStatus.approved:
        raise ValueError("Only approved clips can be scheduled")
    if not clip.render_path:
        raise ValueError("Rendered clip has no render path")

    settings = get_settings()
    profile_id = _resolve_buffer_profile_id(platform)
    client = BufferClient(
        access_token=settings.buffer_access_token or "",
        base_url=settings.buffer_api_base_url,
    )

    publication = PublicationJob(
        rendered_clip_fk=clip.id,
        platform=platform,
        scheduled_at=scheduled_at,
        publish_status=PublishStatus.pending,
    )
    db.add(publication)
    db.commit()
    db.refresh(publication)

    try:
        buffer_post_id, buffer_status = client.schedule_post(
            profile_id=profile_id,
            text=caption,
            media_url=clip.render_path,
            scheduled_at=scheduled_at,
        )
        publication.buffer_post_id = buffer_post_id
        publication.publish_status = _to_publish_status(buffer_status)
        clip.last_error = None
        db.add(publication)
        db.add(clip)
        db.commit()
        db.refresh(publication)
        return publication
    except BufferApiError as exc:
        publication.publish_status = PublishStatus.failed
        clip.last_error = f"Publish failed: {str(exc)[:500]}"
        db.add(publication)
        db.add(clip)
        db.commit()
        db.refresh(publication)
        return publication


def schedule_clip_via_tiktok(
    db: Session,
    rendered_clip_id: str,
    platform: Platform,
    scheduled_at: datetime,
    caption: str,
) -> PublicationJob:
    if platform != Platform.tiktok:
        raise ValueError("TikTok provider only supports platform=tiktok")

    clip = db.scalar(select(RenderedClip).where(RenderedClip.id == rendered_clip_id))
    if clip is None:
        raise ValueError(f"Rendered clip not found: {rendered_clip_id}")
    if clip.review_status != ReviewStatus.approved:
        raise ValueError("Only approved clips can be scheduled")
    if not clip.render_path:
        raise ValueError("Rendered clip has no render path")

    settings = get_settings()
    client = TikTokClient(
        access_token=get_tiktok_access_token() or "",
        base_url=settings.tiktok_api_base_url,
    )

    publication = PublicationJob(
        rendered_clip_fk=clip.id,
        platform=platform,
        scheduled_at=scheduled_at,
        publish_status=PublishStatus.pending,
    )
    db.add(publication)
    db.commit()
    db.refresh(publication)

    try:
        tiktok_publish_id, tiktok_status = client.schedule_post(video_file_path=clip.render_path)
        publication.external_post_ref = tiktok_publish_id
        publication.publish_status = _to_publish_status(tiktok_status)
        clip.last_error = None
        db.add(publication)
        db.add(clip)
        db.commit()
        db.refresh(publication)
        return publication
    except TikTokApiError as exc:
        if _is_tiktok_auth_error(exc):
            try:
                refresh_tiktok_access_token()
                retried_client = TikTokClient(
                    access_token=get_tiktok_access_token() or "",
                    base_url=settings.tiktok_api_base_url,
                )
                tiktok_publish_id, tiktok_status = retried_client.schedule_post(video_file_path=clip.render_path)
                publication.external_post_ref = tiktok_publish_id
                publication.publish_status = _to_publish_status(tiktok_status)
                clip.last_error = None
                db.add(publication)
                db.add(clip)
                db.commit()
                db.refresh(publication)
                return publication
            except (TikTokApiError, TikTokOAuthError):
                pass
        publication.publish_status = PublishStatus.failed
        clip.last_error = f"TikTok publish failed: {str(exc)[:500]}"
        db.add(publication)
        db.add(clip)
        db.commit()
        db.refresh(publication)
        return publication


def schedule_clip_for_distribution(
    db: Session,
    rendered_clip_id: str,
    platform: Platform,
    scheduled_at: datetime,
    caption: str,
) -> PublicationJob:
    clip = db.scalar(select(RenderedClip).where(RenderedClip.id == rendered_clip_id))
    if clip is None:
        raise ValueError(f"Rendered clip not found: {rendered_clip_id}")
    if clip.review_status != ReviewStatus.approved:
        raise ValueError("Only approved clips can be scheduled")
    if not clip.render_path:
        raise ValueError("Rendered clip has no render path")
    assert_clip_compliant(db=db, rendered_clip_id=rendered_clip_id)

    settings = get_settings()
    if settings.publish_provider == "buffer":
        publication = schedule_clip_via_buffer(
            db=db,
            rendered_clip_id=rendered_clip_id,
            platform=platform,
            scheduled_at=scheduled_at,
            caption=caption,
        )
        publication.distribution_provider = DistributionProvider.buffer
        publication.external_post_ref = publication.buffer_post_id
        db.add(publication)
        db.commit()
        db.refresh(publication)
        return publication

    if settings.publish_provider == "tiktok":
        publication = schedule_clip_via_tiktok(
            db=db,
            rendered_clip_id=rendered_clip_id,
            platform=platform,
            scheduled_at=scheduled_at,
            caption=caption,
        )
        publication.distribution_provider = DistributionProvider.tiktok
        db.add(publication)
        db.commit()
        db.refresh(publication)
        return publication

    publication = PublicationJob(
        rendered_clip_fk=clip.id,
        distribution_provider=DistributionProvider.manual,
        platform=platform,
        scheduled_at=scheduled_at,
        publish_status=PublishStatus.scheduled,
    )
    db.add(publication)
    db.commit()
    db.refresh(publication)

    export_ref = _create_manual_export(publication=publication, clip=clip, caption=caption)
    publication.external_post_ref = export_ref
    clip.last_error = None
    db.add(publication)
    db.add(clip)
    db.commit()
    db.refresh(publication)
    return publication


def sync_publication_job_status(db: Session, publication_job_id: str) -> PublicationJob:
    publication = db.scalar(select(PublicationJob).where(PublicationJob.id == publication_job_id))
    if publication is None:
        raise ValueError(f"Publication job not found: {publication_job_id}")
    if publication.distribution_provider == DistributionProvider.manual:
        return publication

    if publication.distribution_provider == DistributionProvider.buffer:
        if not publication.buffer_post_id:
            raise ValueError("Publication job has no buffer_post_id")

        settings = get_settings()
        client = BufferClient(
            access_token=settings.buffer_access_token or "",
            base_url=settings.buffer_api_base_url,
        )

        try:
            status = client.fetch_update_status(publication.buffer_post_id)
            publication.publish_status = _to_publish_status(status)
        except BufferApiError as exc:
            publication.publish_status = PublishStatus.failed
            clip = db.scalar(select(RenderedClip).where(RenderedClip.id == publication.rendered_clip_fk))
            if clip is not None:
                clip.last_error = f"Publish status sync failed: {str(exc)[:500]}"
                db.add(clip)

        db.add(publication)
        db.commit()
        db.refresh(publication)
        return publication

    if publication.distribution_provider == DistributionProvider.tiktok:
        if not publication.external_post_ref:
            raise ValueError("Publication job has no TikTok publish reference")

        settings = get_settings()
        client = TikTokClient(
            access_token=get_tiktok_access_token() or "",
            base_url=settings.tiktok_api_base_url,
        )

        try:
            status = client.fetch_publish_status(publication.external_post_ref)
            publication.publish_status = _to_publish_status(status)
        except TikTokApiError as exc:
            if _is_tiktok_auth_error(exc):
                try:
                    refresh_tiktok_access_token()
                    retried_client = TikTokClient(
                        access_token=get_tiktok_access_token() or "",
                        base_url=settings.tiktok_api_base_url,
                    )
                    status = retried_client.fetch_publish_status(publication.external_post_ref)
                    publication.publish_status = _to_publish_status(status)
                except (TikTokApiError, TikTokOAuthError):
                    publication.publish_status = PublishStatus.failed
                    clip = db.scalar(select(RenderedClip).where(RenderedClip.id == publication.rendered_clip_fk))
                    if clip is not None:
                        clip.last_error = f"TikTok status sync failed: {str(exc)[:500]}"
                        db.add(clip)
            else:
                publication.publish_status = PublishStatus.failed
                clip = db.scalar(select(RenderedClip).where(RenderedClip.id == publication.rendered_clip_fk))
                if clip is not None:
                    clip.last_error = f"TikTok status sync failed: {str(exc)[:500]}"
                    db.add(clip)

        db.add(publication)
        db.commit()
        db.refresh(publication)
        return publication

    raise ValueError(f"Unsupported distribution provider: {publication.distribution_provider}")