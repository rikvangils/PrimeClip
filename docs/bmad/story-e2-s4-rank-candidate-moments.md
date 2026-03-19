# Story E2-S4 - Rank Candidate Moments

Status: Implemented  
Date: 18 March 2026  
Sprint: S1  
Epic: Epic 2 - Ingest and Candidate Discovery

## Story

As the operator,
I want ranked candidate moments,
so that the pipeline focuses on the most promising funny segments.

## Acceptance criteria mapping

1. Candidate moments include start/end timestamps and ranking score.
- Ranking service creates `candidate_segments` with `start_ts`, `end_ts`, and `ranking_score`.

2. Ranking uses configurable weighted signals.
- Ranking currently combines transcript keyword bonus, nearby audio intensity, and scene-cut confidence with explicit weights.
- Scoring helper centralizes this logic for future tuning.

3. At least 5 candidate segments can be produced for qualifying long-form content.
- Service enforces minimum candidate count and inserts fallback segments if needed.

## Implemented files

- src/app/ingest/ranking.py
- src/app/source_monitor/service.py

## Notes

- Ranking is deterministic and transparent for Sprint 1 baseline.
- Future story work can replace heuristic weights with learned weights from performance feedback.

## Next logical story

- E3-S1 Render vertical clip variants
