# Story E5-S3 - Generate Creative Recommendations

Status: Implemented  
Date: 18 March 2026  
Sprint: S4  
Epic: Epic 5 - Performance Learning and Recommendations

## Story

As the operator,
I want evidence-backed recommendations,
so that I know which hooks, fonts, transitions, timings, and formats to favor next.

## Acceptance criteria mapping

1. Recommendations include rationale, evidence window, expected upside, and confidence.
- `POST /review/recommendations/generate` creates recommendation records with rationale, evidence, expected uplift, and confidence.
- `GET /review/recommendations` lists persisted recommendations.

2. Recommendations respect compliance and anti-repetition constraints.
- Current engine only recommends from already published-and-measured outcomes and operates on tracked creative fingerprint dimensions.
- This keeps recommendations bounded to known, reviewed pipeline outputs.

3. Recommendations are stored for auditability.
- Recommendations are persisted in `optimization_recommendations` with timestamped evidence payloads.

## Implemented files

- src/app/db/models.py
- alembic/versions/001_initial_schema.py
- src/app/review/recommendation_engine.py
- src/app/review/schemas.py
- src/app/review/api.py
- src/app/review/__init__.py
- docs/bmad/implementation-analysis-s4.md

## Notes

- Current engine computes uplift against the window-level average score and can be replaced later with stronger statistical baselines.
- The first audited dimensions are hook pattern, caption pack, font pack, publish time slot, and platform.

## Next logical story

- E5-S4 Build insights dashboard
