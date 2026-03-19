# Generate Project Context Workflow
## ProjectFire: AI Virtual Creators Network

**Agent:** Developer (bmm-dev) + Solution Architect (bmm-architect)
**Module:** Business Modeling (BMM)
**Output:** `project-context.md` (root of project)
**Duration:** 20-30 minutes

---

## Workflow Objective

Create or refresh `project-context.md` — the master AI context file that every agent reads at the start of a session. This file tells AI assistants:
- What ProjectFire is
- The technical stack and conventions
- Current project status
- Where to find key documentation
- Rules for working in this codebase

---

## Phase 1: Gather Current State (10 min)

**Read the following to get up-to-date context:**
- `docs/bmad/prd.md` — product scope and requirements
- `docs/bmad/architecture.md` — technical decisions
- `docs/bmad/sprint-status.yaml` — current sprint state
- `README.md` — existing project overview
- `requirements.txt` — current dependencies
- `src/app/` directory listing — module structure

**Output:** Current state notes

---

## Phase 2: Write Project Context (15 min)

**project-context.md structure:**

```markdown
# ProjectFire: AI Virtual Creators Network
## Project Context for AI Assistants

### What is ProjectFire?
[2-paragraph description of what the system does]

### Current Status
- Sprint: [sprint name/phase]
- Active story: [current story]
- Next BMAD step: [next action]
- Test suite: [N tests, X% coverage]

### Technical Stack
| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Web framework | FastAPI |
| ORM | SQLModel + SQLAlchemy |
| Database | PostgreSQL (JSONB) |
| Migrations | Alembic |
| Testing | pytest + pytest-cov |
| CI | GitHub Actions |
| Video rendering | FFmpeg |
| Publishing | Buffer API |

### Project Structure
src/app/
  db/models.py        — All SQLModel entities
  config.py           — Settings (pydantic-settings)
  review/             — Core business logic + API
    api.py            — FastAPI routes
    service.py        — Queue and scheduling logic
    insights.py       — Analytics aggregation
    experiments.py    — A/B experiment framework
    publishing.py     — Buffer integration
    ...
  rendering/
    layers.py         — FFmpeg clip rendering + pack selection

tests/                — All pytest test files
docs/bmad/            — BMAD planning documents

### Key Conventions
1. Service layer handles business logic — API layer only routes
2. All DB queries use SQLModel Session — no raw SQL
3. Tests use monkeypatch for external dependencies
4. Coverage must remain at 100% (--cov-fail-under=100)
5. Story files: docs/bmad/story-e[N]-s[N]-[slug].md
6. BMAD workflows: _bmad/bmm/workflows/

### BMAD Workflow Reference
- Analysis: _bmad/bmm/workflows/1-analysis/
- Planning: _bmad/bmm/workflows/2-plan-workflows/
- Solutioning: _bmad/bmm/workflows/3-solutioning/
- Implementation: _bmad/bmm/workflows/4-implementation/
- Quick flow: _bmad/bmm/workflows/bmad-quick-flow/
- Testing: _bmad/tea/workflows/testarch/

### Rules for AI Assistants
1. Always read the relevant story file before implementing
2. Always run python -m pytest -q after any code change
3. Never commit secrets or hardcoded credentials
4. Keep changes scoped to the story/spec — no scope creep
5. Update sprint-status.yaml when a story status changes
```

**Output:** project-context.md written

---

## Phase 3: Validate Context File (5 min)

- [ ] All sections are filled (no placeholder text remaining)
- [ ] Technical stack matches current requirements.txt
- [ ] Current status reflects sprint-status.yaml
- [ ] Rules section covers the most common AI assistant mistakes
- [ ] File is readable without running any code

---

## Quality Gates

- [ ] project-context.md created/updated in project root
- [ ] Status section reflects current sprint-status.yaml
- [ ] Technical stack is accurate with current requirements.txt
- [ ] All 6 BMAD workflow paths are correct
- [ ] AI rules section has at least 5 rules
