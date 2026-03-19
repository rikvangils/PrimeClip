# UX Design Workflow
## ProjectFire: AI Virtual Creators Network

**Agent:** UX Designer (bmm-ux-designer)
**Module:** Business Modeling (BMM)
**Output:** `docs/ux-design.md`
**Duration:** 60-90 minutes (collaborative design)

---

## Workflow Objective

Define the user experience patterns and design specifications for ProjectFire's human-facing interfaces, covering:

1. **User Flows** — How each persona navigates the system
2. **Screen Inventory** — What views/pages exist
3. **Interaction Patterns** — How users interact with key features
4. **Information Architecture** — How content is organized
5. **Design Principles** — Visual and interaction guidelines

---

## Phase 1: User Flow Mapping (20 min)

**Goal:** Map how each persona moves through the system

**Persona flows to document:**

### Flow 1: Content Creator — Review & Approve Clip
```
Source upload detected
  → Ingest job created
  → Media signals extracted
  → Candidate moment scored
  → Clip rendered with creative packs
  → Appears in review queue
  → Creator reviews clip preview
  → Creator approves / requests edit / rejects
  → Approved clip enters scheduling queue
```

### Flow 2: Creator — Schedule & Publish
```
Review queue → Scheduling view
  → See AI-recommended posting windows
  → Select time slot / accept recommendation
  → Post scheduled in Buffer
  → Published confirmation
  → Performance tracking begins
```

### Flow 3: Creator — Monitor Performance
```
Published posts view
  → Performance snapshot ingested
  → Insights dashboard updated
  → Trend pack recommendations surfaced
  → Creator experiments with pack settings
```

**Output:** Flow diagrams or step-by-step flow descriptions per persona

---

## Phase 2: Screen Inventory (15 min)

**Goal:** List all screens/views the system needs

**Screen list with priority:**

| Screen | Priority | Persona | Description |
|--------|----------|---------|-------------|
| Review Queue | Must | Creator | List of clips awaiting review |
| Clip Detail / Preview | Must | Creator | Full clip view with approve/reject |
| Scheduling View | Must | Creator | Calendar view + recommended slots |
| Published Posts | Must | Creator | List of published posts + status |
| Insights Dashboard | Should | Creator | Analytics + top performers |
| Trend Pack Workspace | Should | Creator | Experiment with pack settings |
| Source Management | Could | Admin | Manage whitelisted channels |
| Admin Dashboard | Could | Admin | System health and config |

**Output:** Prioritized screen inventory

---

## Phase 3: Key Interaction Patterns (20 min)

**Goal:** Define how the most important interactions work

### Pattern 1: Clip Review Card
- Shows: thumbnail, title, source channel, score, duration, caption preview
- Actions: Approve (✓), Reject (✗), Edit Caption (✏), Preview Full (▶)
- Feedback: Optimistic UI update, undo available for 5 seconds
- Edge case: What if clip render is still in progress? (loading state)

### Pattern 2: Scheduling Recommendation
- Shows: Recommended time slots highlighted on calendar
- Rationale displayed: "Best engagement for this audience on Wednesdays 18:00-20:00"
- Actions: Accept slot, Pick custom slot, Schedule for later
- Conflict handling: Slot already occupied → show alternatives

### Pattern 3: Insights Dashboard
- Shows: Top creative winners, best posting windows, trend pack performance
- Time range selector: 7d / 30d / 90d
- Drill-down: Click metric → see breakdown by platform/format

### Pattern 4: Experiment Toggle
- Shows: Current active pack versions vs candidate pack
- Toggle between A/B states with live preview
- Promote button to make candidate the default

**Output:** Interaction pattern definitions per key flow

---

## Phase 4: Information Architecture (10 min)

**Goal:** Define navigation and content hierarchy

**Primary navigation:**
```
ProjectFire
├── Review Queue          ← primary action area
├── Scheduled Posts       ← calendar view
├── Published Posts       ← performance tracking
├── Insights              ← analytics
├── Experiments           ← pack workspace
└── Settings
    ├── Source Channels
    ├── Publishing Accounts
    └── Creative Packs
```

**Content hierarchy per section:**
- Review Queue: sorted by score DESC, filtered by status (pending/approved/rejected)
- Scheduled: sorted by scheduled_at ASC, grouped by day
- Published: sorted by published_at DESC, paginated
- Insights: aggregated metrics with drill-down

**Output:** Navigation tree + content sorting/filtering rules

---

## Phase 5: Design Principles (5 min)

**Goal:** Establish guiding principles for all UI decisions

**ProjectFire UX principles:**
1. **Speed over polish** — Creators need to process queues quickly; minimize clicks
2. **AI as assistant, not authority** — Always show AI recommendations as suggestions, human has final say
3. **Signal-rich cards** — Every item shows enough context to decide without opening detail
4. **Reversible actions** — Approve/reject should be undoable within the same session
5. **Progressive disclosure** — Basic view first, advanced options (experiments, pack config) available on demand

**Output:** 5 design principles documented

---

## Quality Gates

- [ ] At least 3 user flows documented end-to-end
- [ ] All Must-priority screens inventoried
- [ ] Key interaction patterns defined for review, scheduling, and insights
- [ ] Navigation IA defined with sorting/filtering rules
- [ ] 5 design principles documented
- [ ] UX design saved to `docs/ux-design.md`
