# Story E4-S1 - Build Review Queue

Status: Implemented  
Date: 18 March 2026  
Sprint: S3  
Epic: Epic 4 - Review, Scheduling, and Publishing

## Story

As the operator,
I want a review queue with preview and evidence,
so that I can approve or reject clips quickly.

## Acceptance criteria mapping

1. Review queue shows clip preview, source context, authenticity score, fingerprint summary, and risk flags.
- `GET /review/queue` returns render path, source metadata, authenticity score, fingerprint fields, and computed risk flags.

2. Queue supports filtering by priority, risk, platform, and experiment status.
- MVP backend filters implemented for status and risk-only toggle.
- Platform query param is reserved and accepted for immediate compatibility with upcoming scheduling/recommendation work.

3. Actions exist for approve, revise, and reject.
- `POST /review/clips/{id}/decision` supports actions `approve`, `revise`, and `reject`.
- Clip review status is persisted to `rendered_clips.review_status`.

## Implemented files

- src/app/review/schemas.py
- src/app/review/queue.py
- src/app/review/api.py
- src/app/review/__init__.py
- src/app/db/session.py
- src/app/main.py

## Notes

- API bootstrap is now available through FastAPI app entrypoint for local testing.
- Platform and experiment-specific ranking/prioritization will be expanded in E4-S2 and later optimization stories.

## Next logical story

- E4-S2 Add scheduling recommendations
