# Architecture Workflow
## ProjectFire: AI Virtual Creators Network

**Agent:** Solution Architect (bmm-architect)
**Module:** Business Modeling (BMM)
**Output:** `docs/architecture.md`
**Duration:** 60-90 minutes (design session)

---

## Workflow Objective

Design the technical architecture for ProjectFire covering:

1. **System Context** — What ProjectFire does and its external integrations
2. **Component Design** — Core modules, their responsibilities and interfaces
3. **Data Architecture** — Schema design and data flow
4. **API Design** — Endpoint structure and contracts
5. **Infrastructure Decisions** — Technology choices with rationale
6. **Cross-Cutting Concerns** — Security, observability, error handling

---

## Phase 1: System Context (10 min)

**Goal:** Define system boundaries and external dependencies

**External systems:**
- **YouTube / Content Sources** — Video uploads detected via webhooks or polling
- **Buffer** — Social media scheduling and publishing API
- **FFmpeg** — Local video/image rendering engine (not a service, embedded)
- **PostgreSQL** — Primary data store
- **File storage** — Rendered clips and thumbnails

**Context diagram (text form):**
```
[YouTube Channel] → [Ingest Pipeline] → [Rendering Engine] → [Review Queue API]
                                                                      ↓
[Buffer API] ← [Publishing Service] ← [Scheduling Service] ← [Creator Review UI]
                                                                      ↓
[Performance Analytics] → [Insights Engine] → [Experiment Framework]
```

**Output:** System context description + external integrations list

---

## Phase 2: Component Design (20 min)

**Goal:** Define internal modules, their responsibilities and interfaces

**Core components:**

| Component | Module path | Responsibility |
|-----------|-------------|----------------|
| Ingest Pipeline | `src/app/ingest/` | Detect uploads, create jobs, extract signals |
| Rendering Engine | `src/app/rendering/` | Render clips, apply creative packs |
| Review API | `src/app/review/api.py` | REST API for queue, approval, scheduling |
| Review Services | `src/app/review/service.py` | Business logic for queue operations |
| Insights Engine | `src/app/review/insights.py` | Aggregate performance data |
| Experiment Framework | `src/app/review/experiments.py` | A/B pack testing logic |
| Publishing Service | `src/app/review/publishing.py` | Buffer integration, post tracking |
| DB Models | `src/app/db/models.py` | SQLModel ORM definitions |
| Config | `src/app/config.py` | Settings via pydantic-settings |

**Component interaction rules:**
- API layer calls service layer only (never models directly)
- Service layer calls models and external integrations
- Rendering engine is invoked by ingest pipeline, not by API
- Experiments framework reads/writes via shared DB models

**Output:** Component table + interaction rules

---

## Phase 3: Data Architecture (20 min)

**Goal:** Define key entities and their relationships

**Core entities:**
```
SourceChannel
  └── IngestJob (one per upload)
       └── ClipCandidate (N per job, ranked)
            └── ClipRender (one per approved candidate)
                 └── CreativeFingerprint (one per render)

PublicationPost
  └── PerformanceSnapshot (N over time)

TrendPack (font/transition/animation/hook/caption/series_format)
  └── Referenced by CreativeFingerprint

ExperimentConfig
  └── ExperimentResult
```

**Key architectural decisions:**
- JSONB columns for flexible metadata (pack_config, signal_data, experiment_payload)
- Alembic for schema migrations
- No soft-delete — use status enums instead (active/retired/paused)
- Created_at/updated_at on all tables

**Output:** Entity relationship summary + key decisions documented

---

## Phase 4: API Design (15 min)

**Goal:** Define REST API structure and key contracts

**API resource structure:**
```
/review/
  GET  /queue                    → paginated clip candidates
  GET  /queue/{id}               → clip candidate detail
  POST /queue/{id}/approve       → approve clip
  POST /queue/{id}/reject        → reject clip

  GET  /schedule                 → scheduling recommendations
  POST /schedule/{id}/confirm    → confirm scheduled slot

  GET  /published                → published posts view
  GET  /sync-status              → pipeline health

  GET  /performance-snapshots    → recent snapshots
  POST /performance-snapshots    → ingest new snapshot
  GET  /performance-snapshots/{id} → snapshot detail

  GET  /insights                 → insights dashboard
  GET  /insights/{id}            → clip insights detail

  GET  /experiments              → experiment list
  POST /experiments              → create experiment
  ...

  GET  /trend-packs              → pack list
  POST /trend-packs              → create pack
  ...

  GET  /exploration-policy       → current policy
  PUT  /exploration-policy       → update policy
```

**API conventions:**
- JSON request/response bodies
- HTTP 422 for validation errors (FastAPI default)
- HTTP 404 for missing resources
- HTTP 500 for unexpected service failures
- Pagination via `limit` + `offset` query params

**Output:** API resource list + conventions documented

---

## Phase 5: Infrastructure Decisions (10 min)

**Goal:** Document technology choices with rationale

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python 3.11+ | Team familiarity, rich ML/media ecosystem |
| Web framework | FastAPI | Async, OpenAPI auto-docs, type safety |
| ORM | SQLModel | Pydantic + SQLAlchemy integration |
| Database | PostgreSQL | JSONB support, mature, reliable |
| Migrations | Alembic | Standard SQLAlchemy migration tool |
| Video rendering | FFmpeg | Industry-standard, no API cost |
| Publishing | Buffer API | Existing integration, multi-platform |
| Testing | pytest + pytest-cov | Industry standard, coverage reporting |
| CI | GitHub Actions | Free for public repos, matrix testing |

**Output:** Decision table with rationale

---

## Phase 6: Cross-Cutting Concerns (5 min)

**Goal:** Define standards for security, observability, errors

**Security:**
- All secrets via environment variables (never committed)
- API endpoints authenticated (auth mechanism TBD per story)
- SQL injection prevention via SQLModel parameterized queries
- No SSRF — validate all external URLs against whitelist

**Observability:**
- Structured logging with log level per environment
- Key pipeline events logged: job created, render complete, approval, publish
- Error details logged with context (job_id, clip_id, etc.)

**Error handling:**
- Service layer raises specific exceptions
- API layer catches and maps to HTTP status codes
- Rendering failures logged and job marked as failed (no crash)
- Retry logic for transient external API failures (Buffer, YouTube)

**Output:** Standards documented per concern

---

## Quality Gates

- [ ] System context diagram with all external integrations
- [ ] All 9 core components listed with responsibilities
- [ ] Entity relationship summary covers all 8+ entities
- [ ] API resource list aligns with existing implementation
- [ ] Infrastructure decisions table is complete
- [ ] Security and observability standards documented
- [ ] Architecture saved to `docs/architecture.md`
