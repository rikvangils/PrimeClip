from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import IngestJob
from app.ingest.analysis import extract_media_analysis_signals
from app.ingest.gate import gate_source_for_ingest
from app.ingest.jobs import mark_ingest_job_completed, mark_ingest_job_failed, mark_ingest_job_running
from app.ingest.ranking import rank_candidate_moments
from app.ingest.schemas import SourceVideoPayload
from app.source_monitor.youtube_client import YouTubeClient


logger = logging.getLogger(__name__)


def poll_whitelisted_uploads(db: Session, youtube_client: YouTubeClient | None = None) -> dict[str, int]:
    """Poll YouTube uploads for whitelisted channels and gate them before ingest."""
    settings = get_settings()
    client = youtube_client or YouTubeClient()

    counters = {
        "detected": 0,
        "accepted": 0,
        "rejected": 0,
        "duplicates": 0,
    }

    for channel in settings.source_channel_whitelist:
        logger.info("source_poll_started channel=%s", channel)
        uploads = client.fetch_recent_uploads(channel_id_or_handle=channel)

        for upload in uploads:
            counters["detected"] += 1
            decision = gate_source_for_ingest(
                db,
                SourceVideoPayload(
                    source_video_id=upload.source_video_id,
                    channel_id=upload.channel_id,
                    title=upload.title,
                    url=upload.url,
                    published_at=upload.published_at,
                ),
            )

            if decision.allowed:
                counters["accepted"] += 1
                logger.info(
                    "source_detected accepted=true source_video_id=%s channel_id=%s",
                    upload.source_video_id,
                    upload.channel_id,
                )

                ingest_job = db.query(IngestJob).filter(IngestJob.source_video.has(source_video_id=upload.source_video_id)).order_by(IngestJob.created_at.desc()).first()
                if ingest_job:
                    try:
                        mark_ingest_job_running(db, ingest_job)
                        extract_media_analysis_signals(db, upload.source_video_id)
                        rank_candidate_moments(db, upload.source_video_id)
                        mark_ingest_job_completed(db, ingest_job)
                    except Exception as exc:
                        mark_ingest_job_failed(db, ingest_job, reason=str(exc))
                        logger.exception("ingest_processing_failed source_video_id=%s", upload.source_video_id)
                continue

            if decision.reason == "duplicate_source_video_id":
                counters["duplicates"] += 1
            else:
                counters["rejected"] += 1

            logger.info(
                "source_detected accepted=false source_video_id=%s channel_id=%s reason=%s",
                upload.source_video_id,
                upload.channel_id,
                decision.reason,
            )

    logger.info(
        "source_poll_completed detected=%s accepted=%s rejected=%s duplicates=%s",
        counters["detected"],
        counters["accepted"],
        counters["rejected"],
        counters["duplicates"],
    )
    return counters