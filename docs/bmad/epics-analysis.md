# Epics Analysis - PeanutClip AutoFlow

Status: Draft  
Date: 18 March 2026

## Objective

Define the most effective implementation order for PeanutClip AutoFlow based on product risk, virality impact, compliance requirements, and learning-loop value.

## Executive summary

The build should not start with the self-learning layer.
It should start with safe ingestion, candidate generation, and a reliable human-reviewed publishing loop.
Only after stable publishing and measurable outputs exist should the optimization engine become central.

Recommended order:

1. Foundations and compliance guardrails
2. Source ingest and candidate analysis
3. Transformative rendering and authenticity gating
4. Review queue and scheduling workflow
5. Performance ingestion and optimization engine
6. Experiment management and trend-pack operations

## Prioritization logic

### Why compliance and foundations come first

- Rights-first gating is non-negotiable.
- Channel whitelisting and provenance are root safety controls.
- Without these, later automation creates platform and legal risk.

### Why source ingest and clip analysis come second

- No downstream flow works without dependable source detection and candidate generation.
- Fast source-to-candidate latency is one of the core product KPIs.

### Why transformative rendering comes before scheduling

- The product’s differentiation depends on clips being authentic and platform-native.
- Review and publish should only operate on clips that already meet transformative standards.

### Why review and scheduling come before self-learning

- The system needs real published outputs to learn from.
- Human review ensures early quality and creates labeled data for later optimization.

### Why optimization comes before advanced experimentation

- Recommendations need enough baseline performance data to be meaningful.
- Formal experimentation is stronger once the system already tracks post-performance and creative fingerprints.

## Delivery principles

1. Build the smallest closed loop first
- detect -> analyze -> transform -> review -> schedule -> measure

2. Preserve explainability
- every recommendation and experiment should be attributable to metrics and creative variables

3. Protect quality while increasing automation
- each later epic may reduce manual effort, but must not weaken compliance or authenticity

## Epic recommendations

### Epic 1: Foundations and Compliance

Purpose:
- establish source control, secrets, auditability, rights gating, and core data model

Why now:
- everything else depends on it

### Epic 2: Ingest and Candidate Discovery

Purpose:
- detect uploads, preprocess media, and rank candidate moments

Why now:
- this unlocks actual clip production

### Epic 3: Transformative Clip Generation

Purpose:
- render platform-ready vertical clips with hook/caption/transition packs and authenticity scoring

Why now:
- this is the product’s creative moat and reused-content defense

### Epic 4: Review, Scheduling, and Publishing

Purpose:
- let operator approve/revise/reject and schedule through Buffer with audit trails

Why now:
- creates the first stable publish pipeline and measurable content outputs

### Epic 5: Performance Learning and Recommendations

Purpose:
- ingest analytics, compute performance score, and generate ranked recommendations

Why now:
- now there is enough published content for the system to learn from

### Epic 6: Experimentation and Trend Operations

Purpose:
- run controlled experiments and manage pack lifecycle with fatigue detection and rollout controls

Why now:
- this amplifies optimization once the recommendation engine already exists

## Story sizing guidance

- Small: one backend component, one UI panel, or one isolated integration behavior
- Medium: full vertical slice across backend + storage + UI
- Large: cross-cutting platform feature; should be split into multiple stories

## Definition of ready for implementation

A story is ready only if:

- scope is limited and testable
- dependencies are explicit
- acceptance criteria are measurable
- rights/authenticity impact is understood
- UX destination screen is identified where relevant

## Traceability

Based on:
- docs/bmad/prd.md
- docs/bmad/architecture.md
- docs/bmad/ux-design.md
- docs/bmad/market-research.md
- docs/bmad/optimization-learning-analysis.md
