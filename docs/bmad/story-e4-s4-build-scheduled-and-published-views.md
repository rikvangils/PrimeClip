# Story E4-S4 - Build Scheduled and Published Views

Status: Implemented  
Date: 18 March 2026  
Sprint: S3  
Epic: Epic 4 - Review, Scheduling, and Publishing

## Story

As the operator,
I want visibility into scheduled, published, and failed posts,
so that I can track the content lifecycle without leaving the product.

## Acceptance criteria mapping

1. Calendar and list views exist for scheduled/published items.
- `GET /review/publication-jobs` provides list-view data with status/platform filters.
- `GET /review/publication-calendar` groups items by scheduled day for calendar-style rendering.

2. Each item links to publish status and later performance snapshots.
- Each response item includes publication job ID, publish status, and performance snapshot summary fields.

3. Failed items are clearly distinguished from successful ones.
- Failed publish states are returned explicitly through `publish_status=failed`.

## Implemented files

- src/app/review/publication_views.py
- src/app/review/schemas.py
- src/app/review/api.py
- src/app/review/__init__.py

## Notes

- Calendar grouping currently keys by scheduled date and keeps unscheduled items under `unscheduled`.
- Snapshot linkage is represented through count and last-observed timestamp for lightweight UI rendering.

## Next logical story

- E5-S1 Ingest post-performance snapshots
