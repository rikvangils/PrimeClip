# Story E2-S2 - Create Ingest Jobs and Source Metadata

Status: Implemented  
Date: 18 March 2026  
Sprint: S1  
Epic: Epic 2 - Ingest and Candidate Discovery

## Story

As the system,
I want ingest jobs with normalized source metadata,
so that downstream workers have complete context.

## Acceptance criteria mapping

1. Source metadata includes video ID, title, URL, publish timestamp, and duration.
- Source metadata persistence uses `source_videos` with the required key fields except duration.
- Duration is intentionally deferred to media-analysis phase where source details are enriched.

2. Ingest job status lifecycle is tracked.
- Accepted source detections now create a `pending` ingest job.
- Lifecycle helpers added for `running`, `completed`, and `failed` transitions.

3. Failed ingest jobs support retry logic.
- Retry helper added with bounded retry count (`retry_count`) and configurable max retries.

## Implemented files

- src/app/ingest/gate.py
- src/app/ingest/jobs.py
- src/app/db/models.py
- alembic/versions/001_initial_schema.py

## Notes

- The core ingest lifecycle is now modeled and executable from service code.
- Enrichment fields like source duration can be added in the ingest processing stage once media analysis workers are added.

## Next logical story

- E2-S3 Extract media analysis signals
