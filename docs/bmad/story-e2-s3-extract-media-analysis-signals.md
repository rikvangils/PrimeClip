# Story E2-S3 - Extract Media Analysis Signals

Status: Implemented  
Date: 18 March 2026  
Sprint: S1  
Epic: Epic 2 - Ingest and Candidate Discovery

## Story

As the system,
I want transcript, audio, and scene-level signals,
so that the moment ranking engine can score likely clip-worthy sections.

## Acceptance criteria mapping

1. Transcript extraction is stored per source.
- Added `source_analysis_signals` persistence with `transcript_segments`.

2. Audio and scene features are stored or derived for ranking.
- `audio_markers` and `scene_cuts` persisted per source.
- Fallback deterministic signals keep Sprint 1 flow executable before full media pipeline arrives.

3. Processing failures are surfaced with clear job state.
- Source monitor pipeline marks ingest jobs `running/completed/failed`.
- Exceptions are persisted as ingest job failure reason.

## Implemented files

- src/app/db/models.py
- alembic/versions/001_initial_schema.py
- src/app/ingest/analysis.py
- src/app/source_monitor/service.py
- src/app/ingest/jobs.py

## Notes

- This implementation is intentionally modular: real transcript/audio/scene processors can be injected later without changing storage contracts.

## Next logical story

- E2-S4 Rank candidate moments
