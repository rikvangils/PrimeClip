# Story E6-S2 - Allocate Exploration Budget

Status: Implemented  
Date: 18 March 2026  
Sprint: S5  
Epic: Epic 6 - Experimentation and Trend Operations

## Story

As the operator,
I want the system to reserve a safe portion of output for experiments,
so that learning continues without destabilizing the feed.

## Acceptance criteria mapping

1. Exploration budget is configurable.
- Policy endpoint stores configurable target/min/max exploration ratios.

2. Default range supports the PRD exploration strategy.
- Default policy auto-creates with target `0.25` and allowed band `0.20-0.30`.

3. Proven winners can still dominate the majority of scheduled content.
- Budget summary exposes current experiment ratio versus target band so operators can keep experiment share bounded.

## Implemented files

- src/app/db/models.py
- alembic/versions/001_initial_schema.py
- src/app/review/experiments.py
- src/app/review/schemas.py
- src/app/review/api.py
- src/app/review/__init__.py
- docs/bmad/implementation-analysis-s5.md

## Notes

- Current ratio summary uses publication jobs linked back through experiment-linked performance snapshots.
- Policy implementation is free-first and requires no external experimentation platform.

## Next logical story

- E6-S3 Manage trend packs lifecycle
