# UX Design - PeanutClip AutoFlow

Status: Draft  
Date: 18 March 2026

## 1. UX goal

Design an operator experience that lets one person manage clip review, scheduling, and self-learning optimization with speed, clarity, and trust.

## 2. Primary user

- Solo fan-account operator managing TheBurntPeanut clipping workflow.

## 3. Experience principles

- Fast judgment over deep navigation
- Explainability over black-box automation
- Actionable analytics over vanity reporting
- Controlled experimentation over blind automation
- Human approval remains central

## 4. Core screens

### Screen A: Home / Control Room

Purpose:
- Daily starting point and system status overview.

Modules:
- New clips awaiting review
- Posts scheduled for today
- Publish failures or compliance blockers
- Top winning creative patterns this week
- Recommendation changes since yesterday
- Trend decay warnings

Primary actions:
- Review next clip
- Open blocked item
- Accept recommendation bundle
- Open experiment results

### Screen B: Review Queue

Purpose:
- Approve, revise, or reject generated clips quickly.

Layout:
- Left column: queue filters and priorities
- Center: large clip preview player
- Right column: evidence and actions

Right column content:
- clip metadata
- source timestamps
- authenticity score breakdown
- creative fingerprint summary
- recommended platforms and times
- recommendation rationale
- risk flags
- actions: Approve, Revise, Reject

Queue filters:
- Highest predicted upside
- Needs review now
- Compliance risk
- Low authenticity
- Experimental clip
- Platform-specific

### Screen C: Scheduled & Published

Purpose:
- See lifecycle from scheduled to published to measured.

Views:
- calendar view
- list view
- per-platform status view

Item details:
- scheduled time
- platform
- publish status
- linked performance snapshots
- buffer/native IDs

### Screen D: Insights

Purpose:
- Understand what drives growth and discoverability.

Sections:
- Performance Overview
- Discovery & Search
- Creative Winners
- Time & Slot Performance
- Series Performance
- Platform Comparison

Key charts:
- performance score trend
- top hooks by score uplift
- top caption/font combinations
- transition and animation win rates
- best posting windows heatmap
- follow-lift by series format

Each chart must include:
- metric definition
- comparison baseline
- suggested next action

### Screen E: Experiments

Purpose:
- Manage controlled tests for creative variables.

Modules:
- Active experiments
- Winners and losers
- Confidence level
- Variables under test
- Rollout recommendations

Experiment card fields:
- experiment name
- hypothesis
- changed variables
- sample size
- current score delta
- confidence
- operator action

Actions:
- promote winner
- extend test
- stop test
- clone test

### Screen F: Trend Packs

Purpose:
- Manage creative presets used by the system.

Tabs:
- Hook Packs
- Caption Packs
- Font Packs
- Transition Packs
- Animation Packs
- Series Formats

Per-pack fields:
- current status
- usage frequency
- performance score
- fatigue / repetition warning
- last edited

Actions:
- enable
- pause
- retire
- duplicate
- set experiment budget

### Screen G: Compliance

Purpose:
- Keep publish safety and rights controls visible.

Modules:
- rights status per source
- clips blocked by compliance
- audit trail
- fan-account disclosure status

## 5. Key UX flows

### Flow 1: Review and approve a clip

1. Operator opens Home.
2. Clicks highest-priority review item.
3. Watches clip with source context and authenticity breakdown.
4. Sees recommendation rationale and risk flags.
5. Approves, revises, or rejects.
6. If approved, scheduling recommendation is prefilled.

### Flow 2: Learn from published results

1. Operator opens Insights.
2. Sees which hooks, fonts, transitions, and times outperformed baseline.
3. Opens explanation panel for top recommendation.
4. Accepts recommendation bundle or overrides specific variables.
5. System logs decision and applies to next eligible batch.

### Flow 3: Manage experiments

1. Operator opens Experiments.
2. Reviews active tests and confidence levels.
3. Promotes winner or stops weak experiment.
4. Result updates Trend Packs and Recommendation Engine.

## 6. Explainability requirements

Every automated recommendation must include:

- what is being recommended
- why it is recommended
- evidence window
- confidence score
- expected upside
- what constraint still applies

Example:
- Recommend Font Pack B for Instagram Reels.
- Why: +18% normalized Performance Score across last 22 comparable clips.
- Confidence: medium.
- Constraint: cannot exceed repetition cap in current 30-clip window.

## 7. Notification model

### High priority

- rights block
- failed publish
- failed metrics ingestion above threshold
- sudden severe performance regression

### Medium priority

- recommendation bundle changed materially
- experiment reached confidence threshold
- trend pack fatigue warning

### Low priority

- routine daily digest
- minor ranking changes
- low-confidence exploratory outcomes

## 8. Visual direction

The interface should feel like a creator operations cockpit:

- bold but controlled
- video-first
- clear hierarchy
- compact data summaries
- low clutter

Design cues:
- strong preview surfaces
- side panels for evidence and controls
- heatmaps for timing
- card-based experiments and recommendations
- status colors reserved for real urgency

## 9. Content and labeling rules

Avoid vague labels like:
- score
- performance
- status

Prefer explicit labels like:
- 24h Performance Score
- Authenticity Risk
- Best Posting Window
- Top Winning Hook Pattern
- Experiment Confidence

## 10. Acceptance criteria

- Operator can approve or reject a clip in one focused screen.
- Operator can understand why the system recommends a creative change.
- Operator can identify top creative winners in under 2 minutes.
- Operator can distinguish urgent blockers from routine optimization.
- Operator can manage experiments without leaving the product.

## 11. Traceability

This design is based on:
- docs/bmad/market-research.md
- docs/bmad/optimization-learning-analysis.md
- docs/bmad/transformative-content-framework.md
- docs/bmad/ux-analysis.md
- docs/bmad/bmad-execution-protocol.md
