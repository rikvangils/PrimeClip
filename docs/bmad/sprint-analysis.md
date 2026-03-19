# Sprint Analysis - PeanutClip AutoFlow

Status: Draft  
Date: 18 March 2026

## Objective

Translate the approved epics and stories into a practical sprint sequence that follows BMAD logic and preserves the smallest working closed loop.

## Executive summary

Sprint planning should optimize for learning velocity without creating uncontrolled platform or compliance risk.

That means:

- Sprint 1 should establish foundations and the first working ingest path.
- Sprint 2 should complete candidate discovery and first transformative renders.
- Sprint 3 should deliver review and publishing.
- Sprint 4 should add measurable performance ingestion.
- Later sprints should improve recommendations and experimentation.

## Planning assumptions

- Single operator / solo builder context.
- Priority is a working end-to-end loop over broad feature coverage.
- Human review remains mandatory.
- Analytics-driven optimization only becomes meaningful after real posts exist.

## Why this sprint order is correct

### Sprint 1: stabilize the base

- Without schema, whitelisting, rights gates, and source detection, all later work is unstable.
- This sprint creates the minimum trustworthy system boundary.

### Sprint 2: unlock actual clip creation

- Candidate analysis and first renders are the first proof that the product can generate usable creative assets.
- This is the earliest point where authenticity rules can be enforced against real output.

### Sprint 3: close the human-reviewed publishing loop

- Review and scheduling create the first real operator value.
- Buffer publishing turns the product from a lab pipeline into a usable system.

### Sprint 4: measure real outcomes

- Once posts exist, analytics ingestion can begin.
- This sprint creates the first evidence base for improvement.

### Sprint 5+: optimize and experiment

- Recommendations and experiment management only become high quality when there is enough baseline data.

## Sprint principles

1. Each sprint should end in a testable product capability.
2. No sprint should weaken rights or authenticity controls.
3. Each sprint should either complete a loop or prepare the next loop with low ambiguity.
4. UI work should land when the related workflow becomes usable, not much earlier.

## Recommended sprint sequence

### Sprint 1 - Foundations and First Detection

Target stories:
- E1-S1 Create core data schema
- E1-S2 Enforce source whitelisting
- E1-S3 Add rights and compliance gate
- E1-S4 Set up secrets and integration config
- E2-S1 Detect new source uploads
- E2-S2 Create ingest jobs and source metadata

Outcome:
- Trusted source detection and persistent ingest foundation.

### Sprint 2 - Candidate Discovery and First Transformative Render

Target stories:
- E2-S3 Extract media analysis signals
- E2-S4 Rank candidate moments
- E3-S1 Render vertical clip variants
- E3-S2 Apply hook, caption, and context layers
- E3-S4 Score authenticity and route clips

Outcome:
- Reviewable transformed clips exist, even if publishing is not yet complete.

### Sprint 3 - Review and Publishing Loop

Target stories:
- E4-S1 Build review queue
- E4-S2 Add scheduling recommendations
- E4-S3 Integrate Buffer publishing
- E4-S4 Build scheduled and published views

Outcome:
- First human-approved publishing loop is complete.

### Sprint 4 - Performance Learning Baseline

Target stories:
- E5-S1 Ingest post-performance snapshots
- E5-S2 Normalize metrics and compute Performance Score
- E5-S4 Build insights dashboard

Outcome:
- First measurable optimization baseline exists.

### Sprint 5 - Recommendations and Controlled Experimentation

Target stories:
- E5-S3 Generate creative recommendations
- E6-S1 Create experiment registry
- E6-S2 Allocate exploration budget

Outcome:
- Closed-loop learning starts influencing future outputs.

### Sprint 6 - Trend Operations and Experiment Workspace

Target stories:
- E3-S3 Apply transitions, fonts, and animation packs
- E6-S3 Manage trend packs lifecycle
- E6-S4 Build experiments workspace

Outcome:
- System reaches mature creative operations mode.

## Primary risks during sprint execution

- External API setup friction delays source detection or publishing.
- Clip-quality variance may expose gaps in ranking and authenticity heuristics.
- Analytics gaps, especially TikTok-side, may delay optimization depth.

## Mitigations

- Prioritize adapters and mocks for early development.
- Keep review and revise workflows strong in early sprints.
- Use Instagram + Buffer as initial learning baseline while TikTok analytics remains pluggable.

## Traceability

Based on:
- docs/bmad/epics-analysis.md
- docs/bmad/epics-and-stories.md
- docs/bmad/prd.md
- docs/bmad/architecture.md
- docs/bmad/ux-design.md