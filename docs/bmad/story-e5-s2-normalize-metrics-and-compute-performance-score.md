# Story E5-S2 - Normalize Metrics and Compute Performance Score

Status: Implemented  
Date: 18 March 2026  
Sprint: S4  
Epic: Epic 5 - Performance Learning and Recommendations

## Story

As the system,
I want a normalized score per platform,
so that clips can be compared fairly across time slots and channels.

## Acceptance criteria mapping

1. Raw metrics are normalized by platform and baseline rules.
- Performance ingest now applies platform, observation-window, and time-slot baselines before score calculation.
- Normalized outputs are stored in `performance_snapshots.normalized_metrics`.

2. Performance Score is stored with snapshot history.
- Each snapshot persists `performance_score` together with the normalized input context.

3. Score inputs are explainable.
- Weighted score components and formula context are stored in `performance_snapshots.score_components`.
- `GET /review/performance-snapshots/{id}` returns raw inputs, normalized metrics, score components, and final score.

## Implemented files

- src/app/db/models.py
- alembic/versions/001_initial_schema.py
- src/app/review/performance.py
- src/app/review/schemas.py
- src/app/review/api.py
- src/app/review/__init__.py
- docs/bmad/implementation-analysis-s4.md

## Notes

- Baseline normalization currently uses deterministic heuristics for platform, window, and posting slot.
- Later stories can replace these heuristics with learned baselines derived from accumulated snapshot history.

## Next logical story

- E5-S3 Generate creative recommendations
