# Free Tooling Analysis

Status: Active Constraint  
Date: 18 March 2026

## Objective

Capture the new hard product constraint that future implementation must rely on free, open-source, or self-hosted tooling by default.

## Constraint

- No new paid SaaS tool may be required for the core workflow.
- Existing Buffer work should be treated as optional legacy compatibility, not as the default path.
- Native platform APIs, manual export flows, and self-hosted orchestration take priority.

## Practical interpretation for this project

### Allowed by default

- Python/FastAPI/SQLAlchemy/Alembic/PostgreSQL
- ffmpeg
- local filesystem export queues
- native free API surfaces where account eligibility allows it
- self-hosted schedulers, workers, or cron-based orchestration

### Not allowed as hard dependency

- paid scheduling SaaS
- paid analytics SaaS
- hosted queue/orchestration products that require subscription for baseline operation

## Architecture impact

1. Distribution provider must be abstracted.
2. Default publish path should be manual/local export queue.
3. Analytics must prefer native platform signals and manual import fallbacks.
4. Recommendations and experiments must remain independent of paid tooling.

## Immediate implementation decisions

- Default publish provider set to `manual`.
- Manual publish queue writes export manifests locally.
- Buffer adapter remains optional for backward compatibility only.

## Next-step guidance

- Epic 6 should continue under the same constraint.
- Experiment registry and pack lifecycle should not assume paid dashboards or SaaS control planes.
