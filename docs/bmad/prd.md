# PRD - PeanutClip AutoFlow

Status: Draft  
Date: 17 March 2026  
Owner: Rik

## 1. Product vision

Build an automated fan-content system that monitors new YouTube uploads from theburntpeanut, finds the funniest moments, transforms them into original short-form clips, and schedules posts to TikTok and Instagram through free/native or self-hosted distribution flows.

The product must prioritize rights compliance and transformative authenticity, not simple reuploads.

## 2. Goals and outcomes

- Detect new uploads from theburntpeanut quickly and reliably.
- Produce publish-ready clips with clear creative transformation.
- Keep a stable posting cadence through scheduling automation.
- Reduce manual editing workload while keeping human review control.
- Continuously improve creative output using measured post-performance data.

## 3. Success metrics (MVP)

- Upload detection SLA: 95% of new uploads detected within 10 minutes.
- Time to first reviewable clips: <= 45 minutes after upload detection.
- Throughput: at least 5 reviewable clips per source long-form video.
- Authenticity quality: >= 95% of published clips with Authenticity Score >= 70.
- Repetition control: <= 10% duplicate template combinations in rolling 30 clips.
- Optimization lift: measurable improvement in median Performance Score over rolling 30 published clips.
- Learning freshness: 95% of published clips receive post-performance ingestion at 1h, 24h, and 48h windows where platform data is available.

## 4. Users and roles

- Primary user: fan-account operator (single admin).
- Secondary stakeholder: rights owner or creator manager (approval and policy expectations).

## 5. Scope

### In scope (MVP)

- Source monitoring of one creator only: theburntpeanut YouTube channel (channel ID whitelist).
- Ingest and analysis of new long-form videos/streams.
- Funny-moment detection with ranking and candidate clip generation.
- Transformative editing pipeline for 9:16 short videos.
- Trend-aware caption and transition presets.
- Human review queue (approve, revise, reject).
- Free/native or self-hosted scheduling/export flow to TikTok and Instagram fan account.
- Rights-first publish gate and provenance logging.
- Post-performance ingestion and learning loop for published clips.
- Optimization of titles/hooks, posting times, transitions, caption styles, fonts, and animation presets.

### Out of scope (MVP)

- Multi-creator support.
- Fully autonomous posting without review.
- Deepfake, voice cloning, or impersonation features.
- Auto-reply or engagement bot features.

## 6. Functional requirements

### FR-1 Source monitoring

- System must poll YouTube Data API for new uploads from a single whitelisted channel ID.
- System must ignore all channels except theburntpeanut whitelist.
- Duplicate ingest prevention must be enforced by source video ID uniqueness.

### FR-2 Ingest and preprocessing

- On new upload detection, system creates an ingest job.
- System stores source metadata (video ID, title, publish time, URL, duration).
- System extracts audio, scene boundaries, and transcript data for analysis.

### FR-3 Moment detection and ranking

- System scores candidate moments using configurable signals:
  - audio energy spikes
  - laughter/reaction cues
  - transcript punchline markers
  - scene switch density
- System outputs ranked candidate segments with timestamps.

### FR-4 Transformative clip generation

- Each generated clip must include a creative edit profile, not only a direct trim.
- Minimum transformation rules:
  - hook text in first 1-2 seconds
  - dynamic stylized captions
  - at least one active motion or transition effect
  - contextual or branding overlay layer
- System renders output in vertical format (9:16), platform-ready.

### FR-5 Trend preset management

- System must support versioned caption packs and transition packs.
- Admin can enable, disable, and rotate packs.
- System must track which pack versions were applied per clip.

### FR-6 Authenticity scoring gate

- Each clip must receive an Authenticity Score (0-100).
- Publish eligibility thresholds:
  - >= 70: review-ready
  - 55-69: revise queue
  - < 55: reject
- Hard fail if rights-check incomplete.

### FR-7 Human review workflow

- Review queue must show clip preview, score breakdown, and provenance metadata.
- Reviewer actions: approve, request revision, reject.
- No clip can be scheduled without approve status.

### FR-8 Scheduling and distribution

- Approved clips are sent to the configured distribution provider with platform-specific caption formatting.
- Default distribution provider must be free/open-source/self-hosted.
- System supports scheduling windows and posting cadence rules.
- System stores provider reference IDs or local export references and final publish status per platform.

### FR-9 Compliance and policy controls

- Rights-first gate required before scheduling.
- System must enforce fan-account transparency metadata.
- System must store audit trail for each publication decision.

### FR-10 Observability and operations

- System logs each pipeline stage and status.
- Failures must trigger retries with max retry policy and dead-letter queue.
- Daily summary report includes ingest count, generated clips, approved clips, and publish outcomes.

### FR-11 Performance learning loop

- System must store a creative fingerprint for each published clip, including hook/title, caption pack, font, transition pack, animation pack, edit route, duration, and publish slot.
- System must ingest post-performance data after publication in delayed windows such as 1 hour, 24 hours, and 48 hours where available.
- System must compute a normalized Performance Score per platform.
- System must update ranking weights for creative packs and posting slots based on observed outcomes.

### FR-12 Recommendation and experimentation engine

- System must recommend future creative settings based on historical performance.
- System must support controlled experimentation so that not all future clips use the current best-performing settings.
- System must reserve a configurable percentage of scheduled clips for experiments in hooks, fonts, transitions, animations, and clip length.
- System must prevent optimization changes from bypassing authenticity, rights, or anti-repetition constraints.

## 7. Non-functional requirements

- Reliability: 99% successful job orchestration excluding external API outages.
- Performance: first candidate generation <= 20 minutes for typical source duration <= 2 hours.
- Security: API keys in secret manager, never hardcoded.
- Maintainability: modular pipeline with isolated workers.
- Traceability: full provenance record per clip and per publish action.
- Auditability: every optimization decision must be traceable back to source metrics and creative variables.

## 8. Compliance requirements

- Explicit permission or licensing required before enabling auto-publish.
- Respect YouTube, TikTok, and Instagram Terms of Service.
- Paid SaaS tooling must not be required for the core workflow.
- No impersonation of official creator identity.
- Fair use assumptions must not be used as sole operational safeguard.

## 9. Data model (logical)

- sources
  - source_video_id (unique)
  - channel_id
  - title
  - url
  - published_at
  - ingest_status
- clip_candidates
  - candidate_id
  - source_video_id
  - start_ts
  - end_ts
  - ranking_score
- clips
  - clip_id
  - candidate_id
  - render_path
  - authenticity_score
  - caption_pack_version
  - transition_pack_version
  - edit_route
  - review_status
- publications
  - publication_id
  - clip_id
  - platform
  - external_post_ref
  - buffer_post_id (optional legacy field)
  - scheduled_at
  - publish_status
- performance_snapshots
  - snapshot_id
  - publication_id
  - observed_at
  - observation_window
  - views
  - likes
  - comments
  - shares
  - saves
  - follows_lift
  - performance_score
- creative_fingerprints
  - fingerprint_id
  - clip_id
  - hook_pattern
  - title_variant
  - caption_pack_version
  - font_pack_version
  - transition_pack_version
  - animation_pack_version
  - edit_route
  - duration_bucket
  - publish_time_slot
- optimization_recommendations
  - recommendation_id
  - platform
  - recommendation_type
  - recommended_value
  - confidence_score
  - based_on_window
- compliance_audit
  - audit_id
  - clip_id
  - rights_status
  - reviewer_id
  - decision_reason
  - created_at

## 10. MVP milestones

1. Milestone A: ingest + detection + candidate ranking.
2. Milestone B: transformative renderer + authenticity scoring.
3. Milestone C: review queue + free/native distribution integration.
4. Milestone D: operations dashboard + compliance audit export.

## 11. Risks and mitigations

- Rights risk: unresolved permission status.
  - Mitigation: rights-first hard gate and manual override lock.
- Platform API changes.
  - Mitigation: adapter layer and health checks.
- Low-quality auto selection.
  - Mitigation: adjustable ranking weights and human review feedback loop.
- Repetitive creative output.
  - Mitigation: anti-repetition constraints and trend pack rotation.
- False optimization from noisy metrics.
  - Mitigation: use delayed observation windows, normalization by platform and slot, and protected experiment budget.

## 12. Acceptance criteria

- New source upload appears in system and starts ingest within SLA.
- At least 5 candidate clips generated for a qualifying source video.
- Approved clip includes all required transformative layers.
- Default provider schedules or exports approved posts without requiring paid tooling.
- Audit record exists for each published clip with rights and review metadata.

## 13. Analysis-first governance

For all major product changes, this project follows a mandatory analysis-before-build cycle.

Required before each major step:

- UX and trend analysis artifact created or updated.
- Findings translated into explicit requirement deltas.
- Decision rationale captured with source references.

Decision linkage:

- See docs/bmad/market-research.md for current virality and UX signals.
- See docs/bmad/domain-research-youtube-clip-rights.md for rights and policy constraints.
- See docs/bmad/optimization-learning-analysis.md for self-learning and metrics-ingestion design.
- See docs/bmad/ux-analysis.md and docs/bmad/ux-design.md for operator workflow, recommendation explainability, and dashboard behavior.
- See docs/bmad/epics-analysis.md and docs/bmad/epics-and-stories.md for implementation sequencing and delivery breakdown.
- See docs/bmad/bmad-execution-protocol.md for stage-gate process.
