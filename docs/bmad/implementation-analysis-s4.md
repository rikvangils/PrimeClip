# Implementation Analysis - Sprint 4 Performance Learning Baseline

Status: Draft  
Date: 18 March 2026

## Objective

Land the first reliable metrics ingestion slice so publication outcomes are measurable and persistable per observation window.

## Story in scope

- E5-S1 Ingest post-performance snapshots

## Additional story extension

- E5-S2 Normalize metrics and compute Performance Score
- E5-S3 Generate creative recommendations

Rationale for extension in same slice:

- Snapshot ingestion without normalized scoring leaves the learning loop incomparable across platforms and posting slots.
- Explainability needs to be stored at write time so later recommendations can reuse it directly.

## Inputs considered

- docs/bmad/optimization-learning-analysis.md
- docs/bmad/epics-and-stories.md
- docs/bmad/architecture.md

## Key insights

- First baseline should support both manual and adapter-driven ingestion to unblock end-to-end learning quickly.
- Analytics adapter failures must not break the pipeline; they should degrade gracefully and keep data model stable.
- Observation windows need explicit validation to preserve comparability across clips.

## Decisions

### Decision ID: IA-S4-001

- Insight: publication jobs are the stable anchor for post-outcome measurements.
- Decision: ingest snapshots by publication job id and persist one row per ingestion event.
- Expected impact: clear lineage from render to publish to measured outcome.

### Decision ID: IA-S4-002

- Insight: platform analytics APIs vary in reliability and permissions.
- Decision: support `buffer` and `instagram` adapters in MVP plus a pluggable `tiktok` adapter with failure-tolerant behavior.
- Expected impact: analytics expansion without blocking current learning loop.

### Decision ID: IA-S4-003

- Insight: operators may need immediate backfill or correction.
- Decision: endpoint accepts manual metric payload override path in addition to adapter pull mode.
- Expected impact: faster operational recovery and cleaner testing.

### Decision ID: IA-S4-004

- Insight: raw engagement counts are not comparable across platforms and time slots.
- Decision: normalize metrics using platform, observation-window, and posting-slot baselines before computing the score.
- Expected impact: more stable cross-platform comparisons.

### Decision ID: IA-S4-005

- Insight: recommendation logic later will need transparent score provenance.
- Decision: persist `normalized_metrics` and `score_components` with every snapshot.
- Expected impact: explainable downstream analytics and recommendation generation.

### Decision ID: IA-S4-006

- Insight: recommendation output must be auditable, not just computed ad hoc.
- Decision: persist recommendation records with rationale, evidence, confidence, and expected uplift.
- Expected impact: operator trust and later experiment governance.

### Decision ID: IA-S4-007

- Insight: recommendations should connect performance history back to creative variables.
- Decision: aggregate snapshot scores over fingerprint dimensions like hooks, caption packs, fonts, and publish slots.
- Expected impact: actionable creative guidance rather than generic analytics.

### Decision ID: IA-S4-008

- Insight: operators need an operational summary view, not just raw records and recommendation rows.
- Decision: expose an insights dashboard endpoint with winners, posting windows, platform comparisons, and suggested next actions.
- Expected impact: closes the Sprint 4 feedback loop for human decision-making.

## Definition of done

- Snapshot ingest endpoint persists metrics for windows 1h, 24h, and 48h.
- Buffer/Instagram sources can be ingested in pull mode.
- TikTok adapter path is pluggable and non-fatal on failure.
- Stored snapshots are linked to publication jobs and usable by later scoring stories.

## Next logical story

- E6-S1 Create experiment registry
