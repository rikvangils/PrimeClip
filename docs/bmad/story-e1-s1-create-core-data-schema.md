# Story E1-S1 - Create Core Data Schema

Status: Implemented  
Date: 18 March 2026  
Sprint: S1  
Epic: Epic 1 - Foundations and Compliance

## Story

As the system,
I want a persistent schema for sources, candidates, clips, publications, audits, and creative fingerprints,
so that all later pipeline stages are traceable.

## Why this story matters

This is the persistence backbone for the entire product.
Without a stable schema, ingest, clip generation, review, publishing, compliance, and learning cannot be implemented safely.

## Inputs and traceability

Based on:
- docs/bmad/prd.md
- docs/bmad/architecture.md
- docs/bmad/epics-and-stories.md
- docs/bmad/sprint-analysis.md
- docs/bmad/implementation-analysis-s1.md

## Technical assumptions for this story

- Backend stack for initial implementation: Python + FastAPI + SQLAlchemy + Alembic
- Database target: PostgreSQL
- IDs should be UUID-based where practical
- Timestamps should be stored in UTC

## In scope

- Create initial backend source tree for persistence layer
- Add database configuration foundation
- Define core relational models
- Create first migration
- Ensure tables map to first closed-loop needs

## Out of scope

- Source polling logic
- Media downloading or analysis
- Rendering pipeline
- Buffer integration
- Operator UI

## Required entities in this story

Must include:
- source_videos
- ingest_jobs
- candidate_segments
- rendered_clips
- publication_jobs
- creative_fingerprints
- compliance_audit

Should include if low-risk in same migration:
- performance_snapshots

May defer to later migration:
- optimization_recommendations
- experiment_registry
- template_packs
- template_usage_history

## Acceptance criteria

1. A backend application folder exists with a database module and migration configuration.
2. Initial ORM models or equivalent schema definitions exist for the required entities.
3. Alembic migration 001 creates the required tables.
4. Foreign key relationships support traceability from source video to clip to publication and compliance records.
5. Unique constraints prevent duplicate source videos.
6. Status fields and created_at / updated_at timestamps exist where operationally relevant.
7. The migration can be applied cleanly on an empty database.

## Suggested file targets

Suggested initial files:
- src/app/__init__.py
- src/app/config.py
- src/app/db/base.py
- src/app/db/session.py
- src/app/db/models.py
- alembic.ini
- alembic/env.py
- alembic/versions/001_initial_schema.py
- requirements.txt or pyproject.toml

## Implementation tasks

1. Scaffold backend package structure.
2. Add configuration object for database URL.
3. Set up SQLAlchemy base and session utilities.
4. Define initial ORM models for required tables.
5. Add enums or constrained status fields where appropriate.
6. Configure Alembic for the project.
7. Create the initial migration.
8. Validate migration generation and schema coherence.

## Data model guidance

### source_videos
- id
- source_video_id
- channel_id
- title
- url
- published_at
- ingest_status
- created_at
- updated_at

### ingest_jobs
- id
- source_video_id_fk
- status
- started_at
- finished_at
- error_message
- created_at
- updated_at

### candidate_segments
- id
- source_video_fk
- start_ts
- end_ts
- ranking_score
- created_at

### rendered_clips
- id
- candidate_segment_fk
- render_path
- authenticity_score
- review_status
- created_at
- updated_at

### publication_jobs
- id
- rendered_clip_fk
- platform
- buffer_post_id
- scheduled_at
- publish_status
- created_at
- updated_at

### creative_fingerprints
- id
- rendered_clip_fk
- hook_pattern
- title_variant
- caption_pack_version
- font_pack_version
- transition_pack_version
- animation_pack_version
- edit_route
- duration_bucket
- publish_time_slot
- created_at

### compliance_audit
- id
- rendered_clip_fk
- rights_status
- decision_reason
- reviewer_id_nullable
- created_at

### performance_snapshots
- id
- publication_job_fk
- observed_at
- observation_window
- views
- likes
- comments
- shares
- saves
- follows_lift
- performance_score
- created_at

## Testing expectations

- Migration applies successfully to a fresh database.
- ORM metadata matches the created schema.
- Duplicate source_video_id insertion is rejected.
- Foreign key chains support trace queries.

## Definition of done

This story is done when a fresh environment can initialize the project database and produce the first core schema required for Sprint 1 and the first closed loop.

## Handoff note for next story

After this story, proceed with:
- E1-S2 Enforce source whitelisting
- E1-S4 Set up secrets and integration config

Those stories should build on the schema rather than redefining it.
