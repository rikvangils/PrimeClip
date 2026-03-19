# Story E3-S4 - Score Authenticity and Route Clips

Status: Implemented  
Date: 18 March 2026  
Sprint: S2  
Epic: Epic 3 - Transformative Clip Generation

## Story

As the operator,
I want each clip scored for transformative quality,
so that low-quality or risky clips do not reach publish review unnoticed.

## Acceptance criteria mapping

1. Authenticity Score is computed per clip.
- Scoring service evaluates hook/caption/context/style metadata with weighted rules and retry penalties.
- Final score is persisted to `rendered_clips.authenticity_score`.

2. Thresholds route clips to review-ready, revise, or reject.
- Routing thresholds are implemented as:
  - `>= 70`: review_ready
  - `45-69`: revise
  - `< 45`: rejected
- Resulting state is persisted to `rendered_clips.review_status`.

3. Hard fails block clips with missing rights or insufficient transformation.
- Missing or non-approved rights status is hard-rejected.
- Missing transformation evidence (hook/caption/context metadata) is hard-rejected.

## Implemented files

- src/app/review/authenticity.py
- src/app/review/__init__.py

## Notes

- Routing includes reason text for explainability and operator triage.
- Hard-fail reasons are persisted in clip error fields for quick diagnosis in follow-up UI work.

## Next logical story

- E4-S1 Build review queue
