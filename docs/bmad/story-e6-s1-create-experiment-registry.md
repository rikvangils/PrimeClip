# Story E6-S1 - Create Experiment Registry

Status: Implemented  
Date: 18 March 2026  
Sprint: S5  
Epic: Epic 6 - Experimentation and Trend Operations

## Story

As the system,
I want a way to register controlled tests,
so that changes to hooks, fonts, transitions, and animations are measurable.

## Acceptance criteria mapping

1. Experiments store hypothesis, changed variables, sample size, and status.
- Experiment registry stores name, hypothesis, changed variables, baseline reference, sample target/current, and lifecycle status.

2. Only limited variables can be changed in a single experiment.
- Create flow rejects experiments with more than 2 changed variables.

3. Experiment results link back to performance snapshots.
- Snapshot link endpoint stores explicit links from experiments to performance snapshots.
- Sample progress updates as snapshots are linked.

## Implemented files

- src/app/db/models.py
- alembic/versions/001_initial_schema.py
- src/app/review/experiments.py
- src/app/review/schemas.py
- src/app/review/api.py
- src/app/review/__init__.py
- docs/bmad/implementation-analysis-s5.md

## Notes

- Registry is internal, database-backed, and fully self-hosted.
- Status lifecycle supports `draft`, `active`, `paused`, `completed`, and `stopped`.

## Next logical story

- E6-S2 Allocate exploration budget
