# Quick Spec Workflow
## ProjectFire: AI Virtual Creators Network

**Agent:** Developer (bmm-dev) + Product Manager (bmm-pm)
**Module:** Business Modeling (BMM)
**Output:** Quick tech spec document (inline or `docs/bmad/quick-spec-[slug].md`)
**Duration:** 15-30 minutes

---

## Workflow Objective

Rapidly create an implementation-ready technical specification for a small, well-scoped change or feature. Quick specs are for work that:
- Is too small for a full story (< 1 day effort)
- Has no epic dependency (standalone improvement or fix)
- Needs a written spec before implementation begins to avoid scope creep

---

## Phase 1: Scope Definition (5 min)

**Questions to answer:**
1. What exactly needs to change? (1-3 sentences maximum)
2. What triggers this change? (bug, performance issue, UX improvement, tech debt)
3. What explicitly does NOT change? (scope boundary)
4. Is this reversible if it goes wrong?

**Scope validation:** If you cannot answer these in < 5 minutes, this needs a full story instead.

**Output:** Scope statement with boundary

---

## Phase 2: Technical Investigation (10 min)

**Goal:** Identify the exact files, functions, and lines that change

**Investigation steps:**
1. Read the relevant source files in `src/app/`
2. Identify the specific function(s) to add/change
3. Identify breaking changes to existing interfaces
4. Identify which tests need updating
5. Check if a database migration is required

**Output:** File/function impact list

---

## Phase 3: Spec Writing (10 min)

**Quick spec format:**
```markdown
## Quick Spec: [Title]
**Date:** [date]
**Effort:** XS (< 2h) / S (< 4h) / M (< 1d)

### Change
[1-3 sentence description of what changes]

### Why
[Business or technical reason]

### Scope boundary
**In:** [what changes]
**Out:** [what does not change]

### Implementation
- File: `src/app/[module]/[file].py`
  - Function: `[function_name]`
  - Change: [description]
- Test: `tests/[test_file].py`
  - Add: `test_[scenario]()`

### Acceptance
- [ ] [Verifiable criterion 1]
- [ ] [Verifiable criterion 2]

### Risks
- [Risk if any, or "None identified"]
```

**Output:** Completed quick spec

---

## Quality Gates

- [ ] Scope can be described in ≤ 3 sentences
- [ ] Impact list identifies specific files/functions
- [ ] At least 2 acceptance criteria are verifiable
- [ ] Effort estimate is XS, S, or M (escalate to story if L or XL)
- [ ] Spec is ready to hand off for implementation
