# Implementation Analysis - Sprint 2 Transformative Slice

Status: Draft  
Date: 18 March 2026

## Objective

Define a low-risk implementation path for the first transformative generation slice after candidate ranking is already in place.

## Stories in scope

- E3-S2 Apply hook, caption, and context layers
- E3-S4 Score authenticity and route clips

## Inputs considered

- docs/bmad/market-research.md
- docs/bmad/optimization-learning-analysis.md
- docs/bmad/ux-design.md
- docs/bmad/transformative-content-framework.md
- docs/bmad/epics-and-stories.md

## Key insights

- Transformation must be observable in metadata, not only visible in pixels.
- The system needs deterministic defaults so output quality is stable in MVP.
- Authenticity routing must hard-stop unsafe outputs before review/publish flow.

## Decisions

### Decision ID: IA-S2-001

- Insight: E3-S1 already creates stable vertical render artifacts.
- Decision: E3-S2 should operate as a second pass over rendered clips, producing layered output via ffmpeg and updating the same clip record.
- Expected impact: clear separation between base render and transformation pass.

### Decision ID: IA-S2-002

- Insight: Future optimization requires durable creative metadata.
- Decision: Persist caption pack version and route metadata in creative fingerprints during layering.
- Expected impact: enables later recommendation and experiment analysis without reprocessing media.

### Decision ID: IA-S2-003

- Insight: Compliance and authenticity failures must be explainable.
- Decision: E3-S4 uses weighted scoring with explicit reason strings and review status routing.
- Expected impact: operator trust and easier tuning.

## Scoring baseline for E3-S4

Initial weighted dimensions:

- hook presence (30)
- caption pack presence (25)
- context layer presence (20)
- style variety signals (15)
- render health penalty (-10 if retry-heavy)

Thresholds:

- score >= 70: `review_ready`
- 45 <= score < 70: `revise`
- score < 45: `rejected`

Hard-fail rules:

- missing/negative rights status => `rejected`
- insufficient transformation evidence (missing hook or missing captions or missing context) => `rejected`

## Risks

- ffmpeg filter complexity can fail on edge text input.
- Overly strict defaults may reject too many clips in early runs.

## Mitigations

- sanitize overlay text before ffmpeg invocation.
- keep threshold values centralized for rapid tuning.
- persist failure reasons in clip records and routing output.

## Definition of done for this slice

- Layered render pass applies hook/caption/context overlays.
- Creative fingerprint captures pack/version metadata for the clip.
- Authenticity score and routing status are persisted on the clip.
- Hard fails prevent risky clips from entering review-ready path.

## Next logical story

- E3-S3 Apply transitions, fonts, and animation packs
