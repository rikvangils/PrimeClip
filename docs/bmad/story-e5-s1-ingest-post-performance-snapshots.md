# Story E5-S1 - Ingest Post-Performance Snapshots

Status: Implemented  
Date: 18 March 2026  
Sprint: S4  
Epic: Epic 5 - Performance Learning and Recommendations

## Story

As the system,
I want to collect performance data after publishing,
so that each clip can be evaluated over time.

## Acceptance criteria mapping

1. Performance snapshots are stored for configured windows such as 1h, 24h, and 48h.
- Endpoint `POST /review/publication-jobs/{id}/performance-snapshots` stores snapshots with strict observation window enum values.

2. Instagram and optional provider sources are supported in MVP.
- Snapshot payload supports `source=buffer|instagram` in pull mode.
- Native/free sources remain preferred, while Buffer is optional legacy enrichment.

3. TikTok analytics adapter is pluggable and failure-tolerant.
- `source=tiktok` path is implemented as pluggable adapter with non-fatal fallback.
- Adapter failure still persists a snapshot record and returns warning metadata.

## Implemented files

- src/app/db/models.py
- alembic/versions/001_initial_schema.py
- src/app/integrations/analytics.py
- src/app/review/performance.py
- src/app/review/schemas.py
- src/app/review/api.py
- src/app/review/__init__.py
- docs/bmad/implementation-analysis-s4.md

## Notes

- Endpoint supports both `pull` and `manual` modes to enable API-driven as well as operator-supplied metric ingestion.
- Baseline performance score is included for immediate downstream use and can be replaced by normalized scoring in E5-S2.

## Next logical story

- E5-S2 Normalize metrics and compute Performance Score
