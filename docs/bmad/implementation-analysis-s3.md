# Implementation Analysis - Sprint 3 Review and Publishing Start

Status: Draft  
Date: 18 March 2026

## Objective

Start Epic 4 with a minimal but complete review queue backend that operators can use to triage clip decisions safely.

## Story in scope

- E4-S1 Build review queue

## Additional story extension

- E4-S3 Integrate free-first publishing
- E4-S4 Build scheduled and published views

Rationale for extension in same slice:

- Review queue without execution path delays meaningful operator validation.
- Adding default free/local scheduling immediately links approval decisions to publication lifecycle tracking without paid tooling.

Additional decisions for E4-S3:

### Decision ID: IA-S3-004

- Insight: publish automation must remain blocked for non-approved clips.
- Decision: enforce review-approved precondition in schedule service.
- Expected impact: prevents accidental unsafe publishing.

### Decision ID: IA-S3-005

- Insight: failures must be visible in operator triage data.
- Decision: include latest publish status in queue payload and add explicit `publish_failed` risk flag.
- Expected impact: faster recovery from integration or platform-side failures.

### Decision ID: IA-S3-006

- Insight: paid SaaS cannot remain a mandatory dependency.
- Decision: make manual/local export queue the default distribution provider and keep Buffer only as optional legacy adapter.
- Expected impact: future implementation stays free-first and self-hostable.

Additional decisions for E4-S4:

### Decision ID: IA-S3-006

- Insight: operator needs immediate lifecycle visibility after scheduling automation lands.
- Decision: expose both list and calendar-oriented publication endpoints in backend API.
- Expected impact: front-end can render operations dashboard without extra aggregation logic.

### Decision ID: IA-S3-007

- Insight: publication performance linkage should be visible before full analytics dashboards.
- Decision: include snapshot count and last observed timestamp in publication view payloads.
- Expected impact: lightweight bridge to Epic 5 measurement stories.

## Inputs considered

- docs/bmad/ux-design.md
- docs/bmad/epics-and-stories.md
- docs/bmad/transformative-content-framework.md

## Key insights

- Review decisions need evidence context in one payload: source info, authenticity score, fingerprint summary, and risk flags.
- First slice should prioritize deterministic server-side filtering and explicit actions over UI complexity.
- Decision actions should map to existing review status enum to avoid migration overhead.

## Decisions

### Decision ID: IA-S3-001

- Insight: No API boundary exists yet in the implementation branch.
- Decision: Introduce a small FastAPI app with a dedicated review router.
- Expected impact: enables immediate operator and integration testing for review flow.

### Decision ID: IA-S3-002

- Insight: Current schema already stores enough relation data for a queue payload.
- Decision: Build queue read model from joins across `rendered_clips`, `candidate_segments`, `source_videos`, and optional `creative_fingerprints`.
- Expected impact: no schema changes needed for first queue milestone.

### Decision ID: IA-S3-003

- Insight: Operators need rapid triage controls.
- Decision: Provide one decision endpoint with enum action values (`approve`, `revise`, `reject`) mapped to review status.
- Expected impact: consistent decision semantics and simple client integration.

## Definition of done

- Review queue endpoint supports priority/risk/platform/status filters.
- Queue payload includes clip evidence and risk flags.
- Decision endpoint updates clip status using explicit action values.
- API startup path is available for local verification.

## Next logical story

- E4-S2 Add scheduling recommendations
