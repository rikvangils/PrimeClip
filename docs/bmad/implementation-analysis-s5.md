# Implementation Analysis - Sprint 5 Experimentation Baseline

Status: Draft  
Date: 18 March 2026

## Objective

Introduce controlled experimentation without creating creative chaos or breaking the free-first architecture.

## Stories in scope

- E6-S1 Create experiment registry
- E6-S2 Allocate exploration budget
- E6-S3 Manage trend packs lifecycle
- E6-S4 Build experiments workspace

## Inputs considered

- docs/bmad/transformative-content-framework.md
- docs/bmad/free-tooling-analysis.md
- docs/bmad/epics-and-stories.md
- docs/bmad/optimization-learning-analysis.md

## Key insights

- Experimentation only works if changed variables are tightly bounded.
- Registry data must be durable and auditable, not inferred from ad hoc notes.
- Exploration budget must be explicit and enforceable so proven winners still dominate output.
- This layer must remain fully self-hostable and independent of paid experimentation platforms.

## Decisions

### Decision ID: IA-S5-001

- Insight: causal interpretation collapses when too many variables change at once.
- Decision: cap experiments at 2 changed variables.
- Expected impact: cleaner attribution in later recommendation logic.

### Decision ID: IA-S5-002

- Insight: experiments need measurable evidence linkage.
- Decision: add explicit links from experiments to performance snapshots.
- Expected impact: direct traceability from hypothesis to observed results.

### Decision ID: IA-S5-003

- Insight: exploration share should be policy-driven, not hardcoded in scattered services.
- Decision: store a central exploration budget policy with default target in the 20-30% range.
- Expected impact: consistent operator control and predictable scheduling behavior.

### Decision ID: IA-S5-004

- Insight: free-first architecture must continue into experimentation.
- Decision: implement registry and policy as database-backed internal services only.
- Expected impact: no paid experimentation tooling required.

### Decision ID: IA-S5-005

- Insight: creative operations need explicit pack lifecycle controls to avoid drift and stagnation.
- Decision: add trend-pack registry with statuses (`experiment`, `active`, `paused`, `retired`) and promotion flow.
- Expected impact: structured control over creative assets across runs.

### Decision ID: IA-S5-006

- Insight: anti-repetition rules require measurable overuse signals.
- Decision: compute rolling fatigue ratio per pack over latest publication window and expose warning flags.
- Expected impact: operator can rotate packs before audience fatigue escalates.

### Decision ID: IA-S5-007

- Insight: operators need experiment decisions in one consolidated workspace.
- Decision: add workspace endpoint that groups active/completed experiments with confidence and uplift.
- Expected impact: faster decision cycles and reduced context switching.

### Decision ID: IA-S5-008

- Insight: experiment workflow requires direct intervention controls.
- Decision: expose explicit promote/extend/stop/clone action endpoints.
- Expected impact: experimentation process becomes operationally manageable.

## Definition of done

- Experiment records store hypothesis, changed variables, sample target, and status.
- Variable-count guard rejects experiments that exceed the allowed limit.
- Performance snapshots can be linked to experiments.
- Exploration budget is configurable and queryable.
- Budget summary exposes current experiment share versus target share.

## Next logical story

- Epic 6 QA hardening and integration tests
