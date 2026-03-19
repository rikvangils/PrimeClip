# Implementation Analysis - Sprint 1 Story Slice

Status: Draft  
Date: 18 March 2026

## Objective

Prepare the first implementation slice in a way that respects the BMAD analysis-first protocol and reduces ambiguity before development starts.

## Selected starting story

- Primary story: E1-S1 Create core data schema

## Why E1-S1 is the right first implementation step

- Every later workflow depends on a persistent and traceable schema.
- Rights, ingest, candidate ranking, rendering, publishing, and learning all need durable IDs and relationships.
- Starting with the schema creates a stable backbone for the rest of Sprint 1.

## Current repository reality

- This is a greenfield repo for implementation.
- The workspace currently contains planning documents and BMAD artifacts, but no application source tree yet.
- Therefore this story should not only define schema objects, but also establish the minimum backend structure needed to hold migrations and models.

## Recommended implementation approach

Use a backend-first foundation optimized for media workflows and later worker orchestration.

Recommended stack for first implementation slice:

- Backend language: Python
- API framework: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migration tool: Alembic
- Validation/config: Pydantic settings

## Why this stack fits the product

- Python aligns well with later media analysis, transcript tooling, and ffmpeg orchestration.
- PostgreSQL is a strong fit for relational traceability and analytics snapshots.
- Alembic gives versioned schema evolution required by the BMAD workflow.
- FastAPI keeps future operator/API endpoints straightforward.

## Scope boundaries for E1-S1

In scope:
- backend package scaffold
- database configuration shell
- first SQLAlchemy models or equivalent schema definitions
- first Alembic migration
- schema coverage for core entities required by PRD

Out of scope:
- YouTube polling logic
- Buffer integration
- UI implementation
- analytics ingestion
- business logic beyond persistence and relationships

## Core tables to include now

Minimum viable schema for Story E1-S1:

- source_videos
- ingest_jobs
- candidate_segments
- rendered_clips
- publication_jobs
- performance_snapshots
- creative_fingerprints
- compliance_audit

Can be deferred if necessary:
- optimization_recommendations
- experiment_registry
- template_packs
- template_usage_history

Reason for partial deferral:
- keep first migration focused and low-risk while still supporting the first closed loop.

## Key design decisions

### Decision ID: IA-S1-001
- Input sources: PRD, Architecture, Sprint Analysis
- Insight: the first closed loop needs durable traceability more than optimization complexity
- Decision: implement a minimal but forward-compatible schema in migration 001
- Expected impact: faster path to working ingest and publish pipeline without overbuilding

### Decision ID: IA-S1-002
- Input sources: Architecture, Product Brief
- Insight: media-heavy pipeline work will likely be Python-centric
- Decision: start backend scaffold in Python with FastAPI + SQLAlchemy + Alembic
- Expected impact: lowers later friction for workers and media tooling

### Decision ID: IA-S1-003
- Input sources: UX and compliance research
- Insight: rights and provenance are first-class requirements, not add-ons
- Decision: include compliance linkage and publication traceability in first schema cut
- Expected impact: prevents unsafe schema shortcuts that would break later auditability

## Risks

- Stack choice locks in later implementation direction.
- Overly broad first migration slows down Sprint 1.
- Under-scoped schema causes migration churn in Sprint 2.

## Mitigations

- Keep the first migration minimal but relationally sound.
- Prefer additive future migrations over speculative complexity.
- Put UUIDs, timestamps, status fields, and foreign keys in place from the start.

## Definition of ready for development

E1-S1 is ready to implement when:

- backend stack choice is accepted for this slice
- minimum entity list is fixed
- migration strategy is defined
- table naming and relationship strategy are clear

## Next step after this story

- E1-S2 Enforce source whitelisting
- E1-S4 Set up secrets and integration config

These can start immediately after the schema foundation is in place.
