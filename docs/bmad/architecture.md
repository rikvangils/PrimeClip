# Architecture - PeanutClip AutoFlow

Status: Draft  
Date: 17 March 2026  
Owner: Rik

## 1. Architecture goals

- Reliable detection of new uploads from one creator channel.
- Fast generation of transformative clip candidates.
- Safe publication workflow with rights and authenticity gates.
- Simple operations for a solo operator.

## 2. High-level system design

Core pattern: event-driven pipeline with worker services.

Components:

1. Source Monitor
- Polls YouTube Data API for new videos on whitelisted channel.
- Emits NewSourceVideo event.

2. Ingest Worker
- Resolves source media access and metadata.
- Creates preprocessing tasks.

3. Analysis Worker
- Runs transcript extraction, scene detection, and audio feature extraction.
- Produces ranked moment candidates.

4. Transform Renderer
- Applies hook, captions, transitions, overlays, and reframing.
- Produces vertical clips and metadata.

5. Authenticity Scorer
- Scores transformation quality and uniqueness.
- Routes to review-ready, revise, or reject.

6. Review Service
- Operator-facing queue for approve/revise/reject.
- Stores rationale and compliance confirmation.

7. Distribution Service
- Pushes approved clips to a provider abstraction: default manual/local queue, optional Buffer legacy adapter.
- Tracks publication status callbacks.

8. Metrics Collector
- Pulls post-performance data from native platform insights first, with optional legacy Buffer enrichment.
- Runs delayed fetch windows after publishing (for example 1h, 24h, 48h).

9. Optimization Engine
- Correlates creative fingerprints with post outcomes.
- Recommends best-performing hooks, fonts, transitions, animations, time slots, and clip durations.
- Preserves exploration budget for new experiments.

10. Metadata Store
- Stores source, candidate, clip, publication, and audit tables.

11. Object Storage
- Stores intermediate and final media assets.

12. Observability
- Central logs, metrics, alerting, and daily reports.

## 3. Deployment topology

Recommended MVP deployment:

- API + review UI: single web app service.
- Background jobs: queue workers (ingest, analysis, render, scoring, publish).
- Queue broker: managed queue.
- Database: managed PostgreSQL.
- Storage: S3-compatible object bucket.
- Scheduler: cron or cloud scheduler for source polling and trend refresh.
- Separate scheduled jobs: metrics refresh windows and optimization recompute.

## 4. Primary sequence flows

### Flow A: New upload to review queue

1. Source Monitor polls YouTube API.
2. New source video found and persisted.
3. Ingest Worker starts preprocessing.
4. Analysis Worker creates ranked candidate moments.
5. Transform Renderer generates clip variants.
6. Authenticity Scorer computes score and route.
7. Eligible clips appear in review queue.

### Flow B: Review to publishing

1. Operator approves clip.
2. Compliance gate confirms rights status and required metadata.
3. Distribution Service schedules post via free/native or local/manual provider.
4. Publication status is tracked and stored.

### Flow C: Post-performance learning

1. Metrics Collector retrieves platform performance after publish windows.
2. Performance metrics are normalized and stored.
3. Optimization Engine computes updated rankings and recommendations.
4. Trend/template subsystem consumes recommendations for future clip generation.

## 5. Authenticity scoring design

Formula:

AuthenticityScore = TransformDepth + VisualOriginality + NarrativeReframing + TemplateUniqueness + ComplianceConfidence

Weights:

- TransformDepth: 35
- VisualOriginality: 20
- NarrativeReframing: 20
- TemplateUniqueness: 15
- ComplianceConfidence: 10

Thresholds:

- >= 70 review-ready
- 55-69 revise
- < 55 reject

Hard-fail conditions:

- Missing rights status
- Missing transformation layers
- Repetition violation above policy limits

## 6. Trend and template subsystem

- Store caption packs and transition packs as versioned configuration.
- Associate each clip with applied pack versions and edit route.
- Rotate packs based on performance metrics and operator review.
- Enforce anti-repetition checks on rolling output window.
- Track font packs, animation packs, and hook packs as first-class creative variables.
- Apply exploration budget so a minority of posts intentionally test new combinations.

## 7. Data architecture

Relational schema (minimum):

- source_videos
- ingest_jobs
- candidate_segments
- rendered_clips
- review_decisions
- publication_jobs
- performance_snapshots
- creative_fingerprints
- optimization_recommendations
- experiment_registry
- compliance_audit
- template_packs
- template_usage_history

Indexing priorities:

- source_videos(source_video_id unique)
- rendered_clips(review_status, authenticity_score)
- publication_jobs(platform, publish_status)
- performance_snapshots(publication_id, observed_at)
- optimization_recommendations(platform, recommendation_type)
- template_usage_history(created_at)

## 8. Integrations

### YouTube Data API

- Purpose: channel upload detection and source metadata.
- Control: strict channel ID whitelist for theburntpeanut only.

### Distribution Providers

- Purpose: scheduled publishing orchestration.
- Output targets: TikTok and Instagram connected fan profiles.
- Control: only approved clips with compliance pass.
- Secondary use: analytics enrichment and best-time-to-post support where available.

### Instagram Insights API

- Purpose: post-level media insights for optimization loop.
- Control: use delayed fetch windows because metrics can lag.

### TikTok analytics adapter

- Purpose: ingest TikTok post-performance when an approved source is available.
- Control: keep adapter pluggable because posting docs do not guarantee equivalent analytics in the same API surface.

## 9. Security and secrets

- Store all API credentials in secret manager.
- Use role-based service credentials for workers.
- Encrypt media URLs and signed asset access.
- Keep immutable decision logs for auditability.

## 10. Compliance by design

- Rights-first publish gate enforced in backend.
- Fan-account disclosure metadata required in post template.
- No publish path bypassing review in MVP.
- Full provenance retained for dispute handling.

## 11. Reliability and error handling

- Retry transient failures with exponential backoff.
- Dead-letter queue for failed jobs.
- Idempotency keys for ingest and publish operations.
- Fallback path: mark clip as manual-action-required when external API unstable.

## 12. Observability

Key metrics:

- detection_latency_seconds
- ingest_success_rate
- candidate_count_per_source
- render_time_seconds
- authenticity_score_distribution
- approval_rate
- publish_success_rate
- performance_score_distribution
- experiment_win_rate
- recommendation_adoption_rate

Alerts:

- no-new-source-detected over expected window
- queue backlog threshold exceeded
- publish failure rate above threshold

## 13. Testing strategy

- Unit tests for scoring and anti-repetition logic.
- Integration tests for YouTube and distribution adapters.
- Integration tests for Instagram insights ingestion and analytics normalization.
- End-to-end test: source detection to scheduled post.
- Policy tests: rights gate and review gate cannot be bypassed.
- Optimization tests: recommendation engine cannot override authenticity and compliance constraints.

## 14. Implementation roadmap

1. Build Source Monitor + Ingest Worker + DB schema.
2. Add Analysis Worker and candidate ranking.
3. Implement Transform Renderer with initial packs.
4. Add Authenticity Scorer and review UI.
5. Integrate free-first scheduling and optional provider status tracking.
6. Add Metrics Collector and Optimization Engine.
7. Add observability dashboards and compliance exports.

## 15. Analysis-to-execution gates

Before executing each roadmap phase, perform:

1. UX and trend analysis refresh for that phase.
2. Requirement integration update in PRD and framework docs.
3. Architecture delta review to confirm design still matches latest insights.

Operational reference:

- docs/bmad/bmad-execution-protocol.md
- docs/bmad/ux-analysis.md
- docs/bmad/ux-design.md
