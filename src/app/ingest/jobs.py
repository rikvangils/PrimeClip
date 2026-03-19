from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import IngestJob, JobStatus


def mark_ingest_job_running(db: Session, ingest_job: IngestJob) -> IngestJob:
    ingest_job.status = JobStatus.running
    ingest_job.started_at = datetime.now(timezone.utc)
    ingest_job.error_message = None
    db.add(ingest_job)
    db.commit()
    db.refresh(ingest_job)
    return ingest_job


def mark_ingest_job_completed(db: Session, ingest_job: IngestJob) -> IngestJob:
    ingest_job.status = JobStatus.completed
    ingest_job.finished_at = datetime.now(timezone.utc)
    db.add(ingest_job)
    db.commit()
    db.refresh(ingest_job)
    return ingest_job


def mark_ingest_job_failed(db: Session, ingest_job: IngestJob, reason: str) -> IngestJob:
    ingest_job.status = JobStatus.failed
    ingest_job.finished_at = datetime.now(timezone.utc)
    ingest_job.error_message = reason
    db.add(ingest_job)
    db.commit()
    db.refresh(ingest_job)
    return ingest_job


def request_ingest_retry(db: Session, ingest_job: IngestJob, max_retries: int = 3) -> IngestJob:
    """Move a failed ingest job back to pending if retry budget remains."""
    if ingest_job.retry_count >= max_retries:
        return ingest_job

    ingest_job.retry_count += 1
    ingest_job.status = JobStatus.pending
    ingest_job.started_at = None
    ingest_job.finished_at = None
    db.add(ingest_job)
    db.commit()
    db.refresh(ingest_job)
    return ingest_job