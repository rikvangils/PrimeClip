# Story E3-S2 - Apply Hook, Caption, and Context Layers

Status: Implemented  
Date: 18 March 2026  
Sprint: S2  
Epic: Epic 3 - Transformative Clip Generation

## Story

As the system,
I want to apply hook text, stylized captions, and contextual overlays,
so that each clip has clear transformative layers.

## Acceptance criteria mapping

1. Each clip includes hook text in the opening seconds.
- Layering service applies a top-position hook drawtext overlay with opening-time gating.

2. Caption styling is applied from a versioned pack.
- Caption cues render with ffmpeg drawtext and style rules selected by `caption_pack_version`.
- Applied pack version is persisted into `creative_fingerprints.caption_pack_version`.

3. A context or branding layer is present.
- Layering service applies persistent context overlay near the lower third with background strip.
- Route metadata records `hook-caption-context` to confirm context-layer path.

## Implemented files

- src/app/rendering/layers.py
- src/app/rendering/__init__.py

## Notes

- Layering updates the existing clip artifact path to a deterministic `_layered` output.
- Failures increment render retry counters and preserve ffmpeg stderr for diagnostics.

## Next logical story

- E3-S4 Score authenticity and route clips
