# Implementation Analysis S6 - Creative Pack Application

Status: Draft  
Date: 18 March 2026

## Scope

This analysis covers the next BMAD implementation step after QA hardening:

- E3-S3 Apply transitions, fonts, and animation packs

## Current verified state

- `trend_packs` already supports pack types `font`, `transition`, and `animation`.
- `creative_fingerprints` already persists:
  - `font_pack_version`
  - `transition_pack_version`
  - `animation_pack_version`
- `apply_hook_caption_context_layers` currently always stores a fixed font pack and does not select transition or animation packs.
- Fatigue signals already exist on `trend_packs` through `fatigue_warning` and `fatigue_ratio_rolling_30`.

## Key decision

Implement E3-S3 first as a metadata and selection improvement, not as a full visual effects engine.

That means:

- choose creative pack versions during layer application
- store those versions on the clip fingerprint
- prefer non-fatigued active packs over fatigued ones
- fall back to deterministic defaults when no eligible packs exist

This lands the control and measurement part of the story immediately, while keeping FFmpeg complexity low.

## Why this is the right first slice

- It satisfies the measurable part of the story with minimal risk.
- It reuses the existing trend-pack lifecycle instead of creating a parallel pack system.
- It keeps authenticity, insights, and recommendations compatible with richer fingerprint metadata.
- It gives the next increment a stable base for later visual treatment packs.

## Implementation plan

1. Add pack selection helpers in `src/app/rendering/layers.py`.
2. Query active trend packs for `font`, `transition`, and `animation`.
3. Prefer pack versions in this order:
   - active and not fatigued and promoted
   - active and not fatigued
   - active and promoted
   - newest active
   - hardcoded default version
4. Persist all chosen pack versions in `CreativeFingerprint`.
5. Keep the FFmpeg filter behavior stable for now.
6. Add targeted tests for selection and fingerprint persistence.

## Risk controls

- No schema migration required.
- No API contract changes required.
- Visual render behavior remains backward compatible.
- Fatigue avoidance is advisory, not blocking.

## Success check

- Applying layers stores font, transition, and animation pack versions.
- Active non-fatigued packs are preferred over fatigued alternatives.
- Defaults are used when no active pack exists.

## Next action after this slice

- Extend pack-specific visual behavior so selected transition and animation packs influence the rendered output, not only the fingerprint metadata.