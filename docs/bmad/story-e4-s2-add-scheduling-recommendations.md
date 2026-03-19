# Story E4-S2 - Add Scheduling Recommendations

Status: Implemented  
Date: 18 March 2026  
Sprint: S3  
Epic: Epic 4 - Review, Scheduling, and Publishing

## Story

As the operator,
I want recommended platforms and posting windows,
so that approved clips can be scheduled with less guesswork.

## Acceptance criteria mapping

1. Scheduling form pre-fills recommended platform and time slot.
- `GET /review/clips/{id}/schedule-recommendation` returns `recommended_platform` and `recommended_time_slot`.

2. Operator can override defaults.
- Recommendation endpoint is advisory-only and does not mutate publication records.

3. Recommendation rationale is visible.
- Response includes rationale list and confidence score for explainability.

## Implemented files

- src/app/review/recommendations.py
- src/app/review/schemas.py
- src/app/review/api.py
- src/app/review/__init__.py

## Notes

- Current heuristics combine authenticity score, ranking score, and source-title context.
- Story E5/E6 can replace heuristics with evidence-backed recommendation models.

## Next logical story

- E4-S3 Integrate Buffer publishing
