# BMAD Execution Protocol - Analysis -> Build Loop

Status: Active  
Date: 17 March 2026

## Purpose

Define a strict operating protocol for this project:

- always research before each major implementation step
- analyze UX and trend relevance for virality and authenticity
- convert findings into concrete requirements immediately
- then execute development step

## Stage-gate loop (mandatory)

For every major step (PRD, UX, Architecture, Epics, Implementation):

1. Analysis gate
- Run targeted research for the upcoming step.
- Cover user experience signals, platform trends, and policy constraints.
- Produce a short analysis artifact in docs/bmad.

2. Requirement integration gate
- Translate findings into explicit acceptance criteria.
- Update current design docs (PRD/Architecture/etc.) with traceable changes.

3. Execution gate
- Implement only after analysis and integration are complete.
- Preserve links between decisions and supporting research.

4. Review gate
- Validate whether execution still aligns with latest trends and policy baseline.
- If not aligned, create delta-analysis and revise before moving forward.

## Required artifacts per stage

- Stage analysis note: docs/bmad/{stage}-analysis.md or update to market/domain research
- Decision log entry: changed requirements and rationale
- Updated target document: PRD, architecture, or story file

## Decision logging format

Use this block in updated docs:

- Decision ID
- Input research source(s)
- UX/trend insight
- Requirement change
- Expected impact on virality/authenticity/compliance

## Current step map for PeanutClip AutoFlow

Completed:
- Product Brief
- Domain Research (rights and reused-content context)
- Market/UX trend research
- PRD (initial)
- Architecture (initial)
- UX Design
- Epics and Stories
- Sprint Analysis and Sprint Plan

Next steps following this protocol:
1. Start Sprint 1 implementation from the approved sprint plan.
2. Before implementation, create implementation-step analysis for the selected story slice.
3. Execute the first closed loop through detection, review, publish, and measurement.

## Non-negotiables

- No major implementation step without preceding analysis artifact.
- No publish automation without rights-check and human review.
- No repetitive mass-output patterns that violate authenticity goals.
