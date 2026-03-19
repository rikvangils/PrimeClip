# Story E3-S1 - Render Vertical Clip Variants

Status: Implemented  
Date: 18 March 2026  
Sprint: S2  
Epic: Epic 3 - Transformative Clip Generation

## Story

As the system,
I want to render 9:16 clip variants from candidate moments,
so that each candidate can become a publishable short-form asset.

## Acceptance criteria mapping

1. Rendered clips are exported in platform-ready vertical format.
- Rendering service builds ffmpeg commands that crop/scale to 1080x1920 (9:16), encodes H.264/AAC, and writes mp4 outputs.

2. Render jobs are linked to candidate segments.
- `rendered_clips` records are created or reused via `(candidate_segment_fk, variant_name)` and tied directly to the source candidate.
- Render lifecycle is persisted with status fields (`pending`, `processing`, `completed`, `failed`).

3. Failed renders can be retried without duplicating clip records.
- Retry path reuses the same rendered clip row and variant key.
- Failures increment `retry_count` and store `last_error` for operator/debug visibility.

## Implemented files

- src/app/config.py
- src/app/db/models.py
- alembic/versions/001_initial_schema.py
- src/app/rendering/__init__.py
- src/app/rendering/schemas.py
- src/app/rendering/service.py

## Notes

- ffmpeg binary path and output directory are configurable via settings (`PEANUTCLIP_FFMPEG_BINARY`, `PEANUTCLIP_RENDER_OUTPUT_DIR`).
- Output file naming uses `candidate_id + variant_name` to keep render artifacts deterministic.

## Next logical story

- E3-S2 Apply hook, caption, and context layers
