# Epics and Stories - PeanutClip AutoFlow

Status: Draft  
Date: 18 March 2026

## Delivery order

1. Epic 1 - Foundations and Compliance
2. Epic 2 - Ingest and Candidate Discovery
3. Epic 3 - Transformative Clip Generation
4. Epic 4 - Review, Scheduling, and Publishing
5. Epic 5 - Performance Learning and Recommendations
6. Epic 6 - Experimentation and Trend Operations

## Epic 1 - Foundations and Compliance

Goal:
Establish the safe technical base, compliance controls, and core persistence model.

### Story E1-S1 - Create core data schema

As the system,
I want a persistent schema for sources, candidates, clips, publications, audits, and creative fingerprints,
so that all later pipeline stages are traceable.

Acceptance criteria:
- Database tables exist for the minimum logical model from the PRD.
- Primary keys, foreign keys, and uniqueness rules are defined.
- Source video IDs are unique.
- Publication, audit, and performance records can be linked back to a clip.

### Story E1-S2 - Enforce source whitelisting

As the operator,
I want the system to process only theburntpeanut source content,
so that no unrelated content enters the pipeline.

Acceptance criteria:
- Channel whitelist is configurable but initially contains only theburntpeanut.
- Non-whitelisted content is rejected before ingest.
- Rejection reason is logged.

### Story E1-S3 - Add rights and compliance gate

As the operator,
I want publish-blocking compliance checks,
so that clips cannot be scheduled without required rights and fan-account safeguards.

Acceptance criteria:
- Rights status exists per source/clip.
- Missing rights status blocks scheduling.
- Fan-account disclosure metadata is required before publish.
- Compliance decisions are auditable.

### Story E1-S4 - Set up secrets and integration config

As the system,
I want secure configuration for YouTube, free/native distribution providers, Instagram, and future analytics adapters,
so that credentials are safe and environment-specific.

Acceptance criteria:
- No credentials are hardcoded.
- Required integrations read config from secure environment variables or secret store.
- Invalid or missing config produces actionable errors.

## Epic 2 - Ingest and Candidate Discovery

Goal:
Detect new uploads quickly and generate ranked candidate moments for clipping.

### Story E2-S1 - Detect new source uploads

As the system,
I want to poll YouTube for new uploads from the whitelisted channel,
so that newly published content enters the pipeline within SLA.

Acceptance criteria:
- New uploads are detected within the configured polling interval.
- Duplicate ingest jobs are prevented.
- Detection events are logged.

### Story E2-S2 - Create ingest jobs and source metadata

As the system,
I want ingest jobs with normalized source metadata,
so that downstream workers have complete context.

Acceptance criteria:
- Source metadata includes video ID, title, URL, publish timestamp, and duration.
- Ingest job status lifecycle is tracked.
- Failed ingest jobs support retry logic.

### Story E2-S3 - Extract media analysis signals

As the system,
I want transcript, audio, and scene-level signals,
so that the moment ranking engine can score likely clip-worthy sections.

Acceptance criteria:
- Transcript extraction is stored per source.
- Audio and scene features are stored or derived for ranking.
- Processing failures are surfaced with clear job state.

### Story E2-S4 - Rank candidate moments

As the operator,
I want ranked candidate moments,
so that the pipeline focuses on the most promising funny segments.

Acceptance criteria:
- Candidate moments include start/end timestamps and ranking score.
- Ranking uses configurable weighted signals.
- At least 5 candidate segments can be produced for qualifying long-form content.

## Epic 3 - Transformative Clip Generation

Goal:
Generate platform-native clips that are authentically transformed rather than simple cuts.

### Story E3-S1 - Render vertical clip variants

As the system,
I want to render 9:16 clip variants from candidate moments,
so that each candidate can become a publishable short-form asset.

Acceptance criteria:
- Rendered clips are exported in platform-ready vertical format.
- Render jobs are linked to candidate segments.
- Failed renders can be retried without duplicating clip records.

### Story E3-S2 - Apply hook, caption, and context layers

As the system,
I want to apply hook text, stylized captions, and contextual overlays,
so that each clip has clear transformative layers.

Acceptance criteria:
- Each clip includes hook text in the opening seconds.
- Caption styling is applied from a versioned pack.
- A context or branding layer is present.

### Story E3-S3 - Apply transitions, fonts, and animation packs

As the system,
I want reusable creative packs,
so that clips can be varied while still controlled and measurable.

Acceptance criteria:
- Transition, font, and animation packs are versioned.
- Applied pack versions are stored on the clip fingerprint.
- Anti-repetition constraints are checked during generation.

### Story E3-S4 - Score authenticity and route clips

As the operator,
I want each clip scored for transformative quality,
so that low-quality or risky clips do not reach publish review unnoticed.

Acceptance criteria:
- Authenticity Score is computed per clip.
- Thresholds route clips to review-ready, revise, or reject.
- Hard fails block clips with missing rights or insufficient transformation.

## Epic 4 - Review, Scheduling, and Publishing

Goal:
Give the operator a fast, clear workflow to approve clips and schedule them safely.

### Story E4-S1 - Build review queue

As the operator,
I want a review queue with preview and evidence,
so that I can approve or reject clips quickly.

Acceptance criteria:
- Review queue shows clip preview, source context, authenticity score, fingerprint summary, and risk flags.
- Queue supports filtering by priority, risk, platform, and experiment status.
- Actions exist for approve, revise, and reject.

### Story E4-S2 - Add scheduling recommendations

As the operator,
I want recommended platforms and posting windows,
so that approved clips can be scheduled with less guesswork.

Acceptance criteria:
- Scheduling form pre-fills recommended platform and time slot.
- Operator can override defaults.
- Recommendation rationale is visible.

### Story E4-S3 - Integrate free-first publishing

As the system,
I want approved clips scheduled via a free-first distribution provider,
so that TikTok and Instagram posting is automated.

Acceptance criteria:
- Approved clips can be sent to the configured free-first distribution provider.
- Provider reference IDs or local export references and publish states are stored.
- Publish failures are surfaced in the operator UI.

### Story E4-S4 - Build scheduled and published views

As the operator,
I want visibility into scheduled, published, and failed posts,
so that I can track the content lifecycle without leaving the product.

Acceptance criteria:
- Calendar and list views exist for scheduled/published items.
- Each item links to publish status and later performance snapshots.
- Failed items are clearly distinguished from successful ones.

## Epic 5 - Performance Learning and Recommendations

Goal:
Turn post outcomes into recommendations that improve future clips.

### Story E5-S1 - Ingest post-performance snapshots

As the system,
I want to collect performance data after publishing,
so that each clip can be evaluated over time.

Acceptance criteria:
- Performance snapshots are stored for configured windows such as 1h, 24h, and 48h.
- Instagram and free/optional provider sources are supported in MVP.
- TikTok analytics adapter is pluggable and failure-tolerant.

### Story E5-S2 - Normalize metrics and compute Performance Score

As the system,
I want a normalized score per platform,
so that clips can be compared fairly across time slots and channels.

Acceptance criteria:
- Raw metrics are normalized by platform and baseline rules.
- Performance Score is stored with snapshot history.
- Score inputs are explainable.

### Story E5-S3 - Generate creative recommendations

As the operator,
I want evidence-backed recommendations,
so that I know which hooks, fonts, transitions, timings, and formats to favor next.

Acceptance criteria:
- Recommendations include rationale, evidence window, expected upside, and confidence.
- Recommendations respect compliance and anti-repetition constraints.
- Recommendations are stored for auditability.

### Story E5-S4 - Build insights dashboard

As the operator,
I want a clear insights view,
so that I can understand what is driving reach, engagement, and follows.

Acceptance criteria:
- Insights view shows top creative winners, best posting windows, and platform comparisons.
- Discoverability signals are visible where available.
- Charts include suggested next actions, not only raw values.

## Epic 6 - Experimentation and Trend Operations

Goal:
Add controlled experimentation and pack lifecycle management so the system improves without stagnating.

### Story E6-S1 - Create experiment registry

As the system,
I want a way to register controlled tests,
so that changes to hooks, fonts, transitions, and animations are measurable.

Acceptance criteria:
- Experiments store hypothesis, changed variables, sample size, and status.
- Only limited variables can be changed in a single experiment.
- Experiment results link back to performance snapshots.

### Story E6-S2 - Allocate exploration budget

As the operator,
I want the system to reserve a safe portion of output for experiments,
so that learning continues without destabilizing the feed.

Acceptance criteria:
- Exploration budget is configurable.
- Default range supports the PRD exploration strategy.
- Proven winners can still dominate the majority of scheduled content.

### Story E6-S3 - Manage trend packs lifecycle

As the operator,
I want to enable, pause, retire, and promote packs,
so that creative assets remain fresh and controllable.

Acceptance criteria:
- Trend pack management exists for hooks, captions, fonts, transitions, animations, and series formats.
- Fatigue warnings appear when packs are overused.
- Winning packs can be promoted from experiment status to default.

### Story E6-S4 - Build experiments workspace

As the operator,
I want a dedicated experiments screen,
so that I can review winners, losers, and rollout decisions in one place.

Acceptance criteria:
- Active and completed experiments are visible.
- Confidence and uplift are shown clearly.
- Operator can promote, extend, stop, or clone an experiment.

## Dependency map

- Epic 1 is prerequisite for all other epics.
- Epic 2 depends on Epic 1.
- Epic 3 depends on Epic 2 and Epic 1.
- Epic 4 depends on Epic 3 and Epic 1.
- Epic 5 depends on Epic 4 and Epic 1.
- Epic 6 depends on Epic 5 and Epic 3.

## Suggested first implementation slice

If starting with the smallest meaningful slice, build in this order:

1. E1-S1
2. E1-S2
3. E2-S1
4. E2-S2
5. E2-S3
6. E2-S4
7. E3-S1
8. E3-S2
9. E3-S4
10. E4-S1
11. E4-S3
12. E5-S1

This yields the first measurable closed loop:
source detection -> candidate ranking -> clip generation -> review -> publish -> measure

## Traceability

See:
- docs/bmad/epics-analysis.md
- docs/bmad/prd.md
- docs/bmad/architecture.md
- docs/bmad/ux-design.md
