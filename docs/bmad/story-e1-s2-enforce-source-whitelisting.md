# Story E1-S2 - Enforce Source Whitelisting

Status: Implemented  
Date: 18 March 2026  
Sprint: S1  
Epic: Epic 1 - Foundations and Compliance

## Story

As the operator,
I want the system to process only theburntpeanut source content,
so that no unrelated content enters the pipeline.

## Acceptance criteria mapping

1. Channel whitelist is configurable but initially contains only theburntpeanut.
- Implemented in settings as `source_channel_whitelist` with default `theburntpeanut`.
- Supports comma-separated environment overrides.

2. Non-whitelisted content is rejected before ingest.
- Implemented via `gate_source_for_ingest` service.
- Gate checks whitelist before creating ingest-ready records.

3. Rejection reason is logged.
- Rejection writes warning logs.
- Rejection reason is persisted in `ingest_jobs.error_message` with failed job state.

## Implemented files

- src/app/config.py
- src/app/ingest/schemas.py
- src/app/ingest/gate.py
- src/app/db/models.py
- alembic/versions/001_initial_schema.py

## Notes

- Ingest status now includes `rejected` to explicitly represent pre-ingest policy rejections.
- Duplicate source video IDs are handled as non-allowed gate outcomes.

## Next logical stories

- E1-S4 Set up secrets and integration config
- E2-S1 Detect new source uploads
