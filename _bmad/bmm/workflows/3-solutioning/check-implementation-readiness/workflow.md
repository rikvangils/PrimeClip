# Implementation Readiness Check
## ProjectFire: AI Virtual Creators Network

**Agent:** Solution Architect (bmm-architect) + Product Manager (bmm-pm)
**Module:** Business Modeling (BMM)
**Input:** `docs/prd.md`, `docs/ux-design.md`, `docs/architecture.md`, `docs/epics-and-stories.md`
**Output:** Readiness decision (Go / No-Go with issues list)
**Duration:** 30-45 minutes

---

## Workflow Objective

Verify that all planning documents are complete, consistent, and sufficient to begin implementation. This is the final gate before development sprints start.

---

## Check 1: PRD Readiness

Read `docs/prd.md` and verify:

- [ ] Product vision is stated (1-2 sentences)
- [ ] Scope in/out explicitly defined
- [ ] All functional requirements are numbered (REQ-XXX)
- [ ] Every requirement has a priority (Must/Should/Could/Won't)
- [ ] Every requirement has ≥1 acceptance criterion
- [ ] NFRs have measurable thresholds
- [ ] All 6 epics referenced

**Score:** ___/7 checks passed

---

## Check 2: Architecture Readiness

Read `docs/architecture.md` and verify:

- [ ] System context has all external integrations named
- [ ] All components listed with responsibilities
- [ ] Database entities described (≥7 entities)
- [ ] API resource structure documented
- [ ] Technology stack decisions recorded with rationale
- [ ] Security standards defined
- [ ] Observability standards defined

**Score:** ___/7 checks passed

---

## Check 3: UX Design Readiness

Read `docs/ux-design.md` (if exists) and verify:

- [ ] At least 3 user flows documented
- [ ] Screen inventory created with priorities
- [ ] Interaction patterns for Review Queue, Scheduling, Insights
- [ ] Navigation IA defined
- [ ] Design principles listed

**Score:** ___/5 checks passed  
*(If ux-design.md does not exist, score this section 0 and flag as blocking)*

---

## Check 4: Epics & Stories Readiness

Read `docs/epics-and-stories.md` and verify:

- [ ] All 6 epics defined
- [ ] Every epic has a business value statement
- [ ] Every epic has a "Done when" criterion
- [ ] At least 4 stories per epic
- [ ] Every story has acceptance criteria
- [ ] Story dependencies are listed
- [ ] No story spans multiple epics
- [ ] Story files exist in `docs/bmad/story-e*.md`

**Score:** ___/8 checks passed

---

## Check 5: Cross-Document Consistency

Verify alignment between documents:

- [ ] PRD epics match epics-and-stories.md epics
- [ ] Architecture components align with story technical notes
- [ ] UX flows align with PRD functional requirements
- [ ] Persona references are consistent across all docs
- [ ] No contradictory decisions between architecture and PRD

**Score:** ___/5 checks passed

---

## Readiness Scoring

| Check | Max Score | Actual Score | Pass Threshold |
|-------|-----------|--------------|----------------|
| PRD Readiness | 7 | | ≥6 |
| Architecture | 7 | | ≥6 |
| UX Design | 5 | | ≥4 |
| Epics & Stories | 8 | | ≥7 |
| Consistency | 5 | | ≥4 |
| **Total** | **32** | | **≥27** |

---

## Decision

### GO criteria (all must be true):
- Total score ≥ 27/32
- No check with score of 0
- No blocking issues in consistency check

### NO-GO criteria (any one blocks):
- Total score < 27
- UX Design missing entirely
- More than 3 unchecked items in Epics & Stories
- Any direct contradiction between PRD and Architecture

---

## Issue Log

For each failed check, record:
```
ISSUE: [Check - Item]
Severity: Blocking / Major / Minor
Description: [What is missing or inconsistent]
Owner: [PM / Architect / UX]
Resolution: [Required action before re-check]
```

---

## Quality Gates

- [ ] All 5 checks completed
- [ ] Scoring table filled
- [ ] All blocking issues logged
- [ ] GO/NO-GO decision documented
- [ ] If NO-GO: issue owners assigned and re-check scheduled
