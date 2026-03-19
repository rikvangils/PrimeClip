# Epics & Stories Creation Workflow
## ProjectFire: AI Virtual Creators Network

**Agent:** Product Manager (bmm-pm) + Solution Architect (bmm-architect)
**Module:** Business Modeling (BMM)
**Output:** `docs/epics-and-stories.md`
**Duration:** 60-90 minutes

---

## Workflow Objective

Break down the ProjectFire PRD into a structured set of epics and user stories that development can execute sprint by sprint.

---

## Phase 1: Load Context (5 min)

Before creating epics, read and internalize:
- `docs/prd.md` — functional requirements and epic structure
- `docs/architecture.md` — component structure and technical decisions
- `docs/ux-design.md` — user flows and screen inventory (if exists)

**Output:** Clear understanding of scope before writing stories

---

## Phase 2: Define Epics (20 min)

**Goal:** Group related functionality into deliverable epics

**Epic format:**
```markdown
## Epic E[N]: [Title]

**Business Value:** [Why this matters to users/business]
**Done When:** [Observable completion criteria]
**Dependencies:** [Other epics that must complete first]
**Estimated Stories:** [N stories]
```

**ProjectFire standard epics:**

```
E1: Core Data Schema & Source Whitelisting
    Value: Establish foundation for all pipeline operations
    Done when: Schema deployed, migrations running, source channels configurable

E2: Ingest Detection & Media Analysis
    Value: Detect new content and extract ranking signals automatically
    Done when: New uploads detected, ingest jobs created, signals extracted, candidates ranked

E3: Rendering & Creative Pack System
    Value: Transform raw clips into polished vertical content with brand identity
    Done when: Clips rendered, hook/caption layers applied, packs drive styling

E4: Review Queue & Publishing
    Value: Creators can review, approve, schedule, and publish clips
    Done when: Queue API complete, Buffer publishing live, scheduled posts tracked

E5: Performance Analytics & Learning
    Value: Understand what works and feed learnings back into ranking
    Done when: Snapshots ingested, insights dashboard complete, learning loop active

E6: Experiment Framework & Optimization
    Value: A/B test pack variants to optimize engagement
    Done when: Experiments create/run/conclude, pack promotions work, policy configurable
```

**Output:** Epic list with value statements and completion criteria

---

## Phase 3: Write Stories (40 min)

**Goal:** Break each epic into implementable stories

**Story format:**
```markdown
### E[N]-S[N]: [Story Title]

**As a** [persona]
**I want** [capability]
**So that** [outcome]

**Acceptance Criteria:**
- [ ] [Verifiable criterion 1]
- [ ] [Verifiable criterion 2]
- [ ] [Verifiable criterion 3]

**Technical Notes:**
- [Key implementation hint]
- [Schema/API reference]

**Dependencies:** [Story IDs this requires]
**Estimated effort:** XS / S / M / L / XL
```

**Story writing rules:**
1. Each story must be completable in ≤ 5 days
2. Each story must have ≥ 3 acceptance criteria
3. Acceptance criteria must be verifiable (testable)
4. Stories must be ordered by dependency
5. No story should span multiple epics
6. Technical notes must reference architecture components

**Story count targets per epic:**
- E1: 4-5 stories (schema, migrations, source config, secrets)
- E2: 4-5 stories (detection, job creation, signal extraction, ranking)
- E3: 4-5 stories (rendering, hook layer, caption layer, pack selection, scoring)
- E4: 4-5 stories (queue API, scheduling, Buffer integration, published view)
- E5: 4-5 stories (snapshot ingest, insights engine, dashboard, feedback loop)
- E6: 4-5 stories (experiment CRUD, linking, result tracking, policy config)

**Output:** Full story list per epic

---

## Phase 4: Dependency Mapping (10 min)

**Goal:** Verify story ordering and epic sequencing

**Validate:**
- [ ] E1 stories have no dependencies (they are the foundation)
- [ ] E2 stories depend only on E1 stories
- [ ] E3 stories depend on E1-E2
- [ ] E4 stories depend on E1-E3
- [ ] E5 stories depend on E4
- [ ] E6 stories depend on E5

**Cross-story dependency check:**
For each story, verify its named dependencies exist in the story list.

**Output:** Dependency graph or ordered story list

---

## Phase 5: Story File Creation (5 min)

**Goal:** Create stub story files for each story

For each story create `docs/bmad/story-e[N]-s[N]-[slug].md` with:
```markdown
# Story E[N]-S[N]: [Title]

**Status:** Draft
**Epic:** E[N] - [Epic title]
...
```

**Output:** Story file stubs created for all stories

---

## Quality Gates

- [ ] All 6 epics defined with value statements and completion criteria
- [ ] At least 4 stories per epic
- [ ] All stories are acceptance-testable
- [ ] No story exceeds XL effort estimate
- [ ] Dependency ordering is valid (no circular dependencies)
- [ ] Story stubs created in `docs/bmad/`
- [ ] Epics and stories saved to `docs/epics-and-stories.md`
