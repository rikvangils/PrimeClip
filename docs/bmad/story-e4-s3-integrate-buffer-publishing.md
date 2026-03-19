# Story E4-S3 - Integrate Free-First Publishing

Status: Implemented  
Date: 18 March 2026  
Sprint: S3  
Epic: Epic 4 - Review, Scheduling, and Publishing

## Story

As the system,
I want approved clips scheduled via a free-first distribution provider,
so that TikTok and Instagram posting is automated without requiring paid tooling.

## Acceptance criteria mapping

1. Approved clips can be sent through the configured distribution provider.
- Endpoint `POST /review/clips/{id}/schedule` schedules an approved clip through the default manual/local export flow or optional Buffer adapter.
- Scheduling validates review approval state and render artifact availability.

2. Provider references and publish states are stored.
- Publication job row persists provider, scheduled time, `external_post_ref`, optional `buffer_post_id`, and `publish_status`.
- Endpoint `POST /review/publication-jobs/{id}/sync-status` refreshes status for adapters that support it.

3. Publish failures are surfaced in the operator UI.
- Provider failures set publication status to `failed` and propagate error context to clip diagnostics.
- Review queue payload now includes latest publication status and `publish_failed` risk flag.

## Implemented files

- src/app/integrations/buffer_client.py
- src/app/review/publishing.py
- src/app/review/api.py
- src/app/review/queue.py
- src/app/review/schemas.py
- src/app/review/__init__.py
- src/app/config.py
- .env.example

## Notes

- Manual/local export queue is now the default provider path.
- Buffer profile IDs remain optional for legacy compatibility only.

## Next logical story

- E4-S4 Build scheduled and published views
