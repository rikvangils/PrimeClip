# Optimization Learning Analysis - PeanutClip AutoFlow

Status: Draft  
Date: 18 March 2026

## Objective

Define how the system should learn from each automated post and continuously improve clip quality, discoverability, and reach.

## Executive summary

A self-learning loop is strategically valid for this project, but it must be built around metrics that are actually retrievable and attributable.

Key conclusions:

- Instagram supports media insights that can feed a learning loop.
- Buffer Analyze can support cross-channel performance comparison and timing optimization.
- TikTok posting APIs confirm publishing permissions and creator constraints, but this research did not confirm equivalent official post-performance signals in the same API surface.
- Therefore the learning system should use a source-priority model: native platform insights first, Buffer analytics second, fallback manual/connector ingestion where platform APIs are incomplete.

## 1. What the system should learn from

### Outcome metrics

The optimization engine should score each published clip against:

- views
- likes
- comments
- shares
- saves
- profile actions
- follows/subscriber lift after post
- watch retention proxies when available

### Creative input variables

Each clip should persist the creative variables that may explain performance:

- title / hook text
- caption pack version
- transition pack version
- font family and caption style
- animation pack version
- edit route
- clip duration
- posting time
- posting day
- source content category
- series format

## 2. Official signal availability

### Instagram

Confirmed from official docs:

- Media insights are available per media object.
- Metrics availability can be delayed up to 48 hours.
- Views are available for feed, story, and reels media product types.
- Data is organic only.

Implication:
- Build delayed-ingestion windows for 1h, 24h, and 48h after publish.
- Treat Instagram as a first-class training source.

### Buffer

Observed capability:

- Post-level analytics across channels.
- Best-time-to-post recommendations.
- Audience insights and content-type comparisons.

Implication:
- Use Buffer as aggregation and scheduling optimization layer.
- Use Buffer analytics as fallback or enrichment source, not sole truth source.

### TikTok

Confirmed from official posting docs retrieved:

- Content Posting API supports publishing and creator capability checks.
- Retrieved docs did not confirm post-performance metrics in that same posting API surface.

Implication:
- Architect TikTok analytics as pluggable adapter.
- Do not assume all performance features are available through the same posting integration.
- If native analytics access is limited, support manual export or secondary connector strategy.

## 3. Recommended learning loop

### Loop cadence

For every published clip:

1. Store creative fingerprint at publish time.
2. Fetch platform metrics after 1 hour, 24 hours, and 48 hours.
3. Normalize results per platform.
4. Compute Performance Score and Learning Signals.
5. Update pack, timing, and style rankings.
6. Feed next generation of clips with winning patterns and controlled exploration.

### Why delayed windows matter

- Early metrics indicate hook strength.
- 24-hour metrics indicate distribution success.
- 48-hour metrics capture slower compounding and reduce noise.

## 4. Proposed scoring model

### Performance Score

A normalized score per platform, for example:

PerformanceScore =
0.30 * ViewVelocity +
0.20 * EngagementRate +
0.15 * ShareRate +
0.10 * SaveRate +
0.10 * FollowLift +
0.10 * CompletionProxy +
0.05 * SearchDiscoveryLift

Notes:

- FollowLift and CompletionProxy may require platform-specific fallback definitions.
- Score must be normalized by account baseline and posting slot.

### Exploration vs exploitation

The system should not only repeat winners.

Rule:
- 70-80% of scheduled clips use top-ranked creative packs.
- 20-30% reserved for experiments in hooks, transitions, fonts, and animations.

This avoids local maxima and creative stagnation.

## 5. What the system should optimize

The learning engine should tune:

- best posting windows per platform
- hook/title patterns
- caption styles and fonts
- transition packs
- animation packs
- clip length ranges
- series formats
- source-moment selection weights

## 6. Hard constraints

The optimization engine must not optimize only for views if it damages authenticity or compliance.

Guardrails:

- never disable rights and review gates
- never optimize toward repetitive slop patterns
- preserve anti-repetition limits
- preserve fan-account transparency
- keep authenticity score as parallel quality objective

## 7. Architecture implications

Add these components:

- Metrics Collector
- Performance Warehouse
- Feature Store for creative fingerprints
- Optimization Engine
- Experiment Registry
- Recommendation Service for next clip batch

## 8. Immediate product implications

1. Extend PRD with post-performance learning requirements.
2. Extend architecture with metrics ingestion and recommendation loop.
3. Extend transformative framework with experiment tracking for fonts, transitions, and animations.
4. Add operator dashboard showing what variables are winning and losing.

## 9. Sources

- Meta Instagram Media Insights docs
- Meta Instagram Content Publishing docs
- TikTok Content Posting API docs
- Buffer Analyze product page
