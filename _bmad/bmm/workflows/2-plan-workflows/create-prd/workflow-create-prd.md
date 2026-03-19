# PRD Creation Workflow
## ProjectFire: AI Virtual Creators Network

**Agent:** Product Manager (bmm-pm)
**Module:** Business Modeling (BMM)
**Output:** `docs/prd.md`
**Duration:** 90-120 minutes (collaborative definition)

---

## Workflow Objective

Create a comprehensive Product Requirements Document (PRD) for ProjectFire that captures:

1. **Product Vision & Goals** — What we're building and why
2. **User Personas & Jobs-to-be-Done** — Who uses it and what they need
3. **Functional Requirements** — What the system must do
4. **Non-Functional Requirements** — Performance, security, scalability
5. **Epic & Story Structure** — How work is broken down
6. **Success Metrics** — How we measure achievement

---

## Phase 1: Product Vision (15 min)

**Goal:** Establish a clear, shared product vision

Key inputs:
- `docs/product-brief.md` — Core vision and opportunity
- `docs/market-research.md` — Market context
- `docs/domain-research-*.md` — Technical domain knowledge

Questions to answer:
- What is the one-sentence product description?
- What is the primary value proposition for each user type?
- What is NOT in scope (deliberate exclusions)?
- What is the 6-month success definition?

**Output:** Vision statement + scope boundary

---

## Phase 2: User Personas (20 min)

**Goal:** Define who uses ProjectFire and what they need

**Primary personas to define:**
1. **Content Creator / Channel Manager** — uploads source material, reviews clips
2. **Brand Partner** — buys sponsored clips, tracks performance
3. **Platform Admin** — manages packs, experiments, publishing rules

**Per persona document:**
- Role & context
- Primary goals
- Pain points with current solutions
- Key workflows they perform
- Success criteria (what does "done" look like for them)

**Output:** 3 persona cards added to PRD

---

## Phase 3: Functional Requirements (30 min)

**Goal:** Enumerate what the system must do

**Requirement categories:**
1. **Ingest & Detection** — Source upload monitoring, job creation, metadata extraction
2. **Ranking & Selection** — Moment scoring, candidate ranking, clip candidate creation
3. **Rendering** — Vertical clip rendering, caption/hook layers, pack-based styling
4. **Review & Approval** — Review queue, scheduling recommendations, human approval
5. **Publishing** — Buffer integration, scheduled publishing, performance tracking
6. **Analytics & Learning** — Snapshot ingest, insights dashboard, experiment framework

**Per requirement format:**
```
REQ-XXX: [Short title]
Priority: Must / Should / Could / Won't
As a [persona], I need [capability] so that [outcome]
Acceptance: [measurable criteria]
```

**Output:** Numbered requirements list in PRD

---

## Phase 4: Non-Functional Requirements (15 min)

**Goal:** Define system quality attributes

**NFR categories:**
- **Performance:** Clip rendering < 30s, API response < 200ms p95
- **Reliability:** Ingest pipeline uptime > 99.5%
- **Security:** No public endpoints without auth, no credentials in code
- **Scalability:** Handle 100 concurrent rendering jobs
- **Observability:** All pipeline stages logged, errors alerted
- **Testability:** Minimum 90% unit test coverage on business logic

**Output:** NFR table in PRD

---

## Phase 5: Epic Structure (20 min)

**Goal:** Break down product into deliverable epics

**Reference:** `docs/epics-and-stories.md` (if exists)

**Epic format:**
```
Epic E[N]: [Title]
Business value: [Why this matters]
Stories: E[N]-S1, E[N]-S2, ...
Dependencies: [Prior epics required]
Done when: [Observable completion criteria]
```

**Standard ProjectFire epics:**
- E1: Core Data Schema & Source Whitelisting
- E2: Ingest Detection & Media Analysis
- E3: Rendering & Creative Pack System
- E4: Review Queue & Publishing
- E5: Performance Analytics & Learning
- E6: Experiment Framework & Optimization

**Output:** Epic list with story count estimates

---

## Phase 6: Success Metrics (10 min)

**Goal:** Define measurable success indicators

**Metric categories:**
- **Product:** clips published/week, creator approval rate, brand CTR
- **Technical:** pipeline success rate, rendering error rate, API uptime
- **Business:** brand partner revenue, creator retention, content output volume

**Output:** Metrics table added to PRD

---

## Quality Gates

- [ ] Vision and scope are clearly stated
- [ ] All 3 primary personas documented
- [ ] Functional requirements are numbered and acceptance-testable
- [ ] NFRs include measurable thresholds
- [ ] All 6 epics have titles, value statements, and story counts
- [ ] Success metrics are quantified
- [ ] PRD saved to `docs/prd.md`
