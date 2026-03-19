# Story E2-S1 - Detect New Source Uploads

Status: Implemented  
Date: 18 March 2026  
Sprint: S1  
Epic: Epic 2 - Ingest and Candidate Discovery

## Story

As the system,
I want to poll YouTube for new uploads from the whitelisted channel,
so that newly published content enters the pipeline within SLA.

## Acceptance criteria mapping

1. New uploads are detected within the configured polling interval.
- A source monitor service now supports polling whitelisted sources through YouTube Data API.
- Polling cadence can be scheduled by later orchestration (cron/worker scheduler).

2. Duplicate ingest jobs are prevented.
- Detection flow uses ingest gate duplicate checks by `source_video_id`.
- Duplicate detections are counted and logged.

3. Detection events are logged.
- Poll start, per-video decision, and poll summary are logged with accepted/rejected/duplicate outcomes.

## Implemented files

- src/app/source_monitor/schemas.py
- src/app/source_monitor/youtube_client.py
- src/app/source_monitor/service.py
- src/app/ingest/gate.py (integration reuse)

## Notes

- This story provides the detection service layer; scheduling/execution cadence is handled in later infrastructure stories.
- The service intentionally routes all detected uploads through the whitelist gate for policy consistency.

## Next logical story

- E2-S2 Create ingest jobs and source metadata