# Market Research - PeanutClip AutoFlow

Status: Draft  
Date: 17 March 2026

## Executive summary

This research validates that short-form clipping can perform, but only if it is transformed into platform-native, human-feeling content with clear series structure and rapid iteration.

Direct implications for this project:

- Virality is increasingly interest-led, not follower-led.
- AI-assisted workflows are accepted, low-effort output is rejected.
- Search/discovery optimization in captions and on-screen text now matters.
- Serialized, recognizable creative formats outperform random one-offs.
- Community resonance and identity beats trend-chasing without context.

## 1. User experience signals that drive short-form performance

### Signal A: Hook-speed and attention hold

Observed trend:
- First 1-3 seconds are critical for hover-time and rewatch behavior.

Product implication:
- Enforce mandatory hook generator in clip pipeline.
- Reject clips without early hook text or visual action.

### Signal B: Human-led authenticity

Observed trend:
- Audiences accept AI tooling but reject repetitive, uncurated, robotic output.

Product implication:
- Keep manual review as required gate.
- Add anti-repetition policies and authenticity scoring.

### Signal C: Serialized formats and recurring patterns

Observed trend:
- Episodic formats and recurring creative concepts improve return viewing.

Product implication:
- Introduce reusable episode formats for TheBurntPeanut clips (e.g. "Peanut Chaos #N", "Best reaction this stream").
- Track format performance as a first-class metric.

### Signal D: Social search behavior

Observed trend:
- Users increasingly discover through social search and search-like behaviors.

Product implication:
- Add keyword-aware captions and metadata templates.
- Include subtitle quality as ranking factor for publish readiness.

## 2. Trend synthesis relevant to your use case

### Trend 1: Interest-graph distribution

- Platform feeds reward micro-behavior (watch time, rewatches, pauses).
- Relevance and retention patterns matter more than follower count.

System requirement:
- Optimize clip opening and pacing for retention, not only for raw volume.

### Trend 2: Fast experimentation with quality control

- Rapid test loops are rewarded.
- Over-rushed content often underperforms.

System requirement:
- Use batch generation with quality gates instead of blind mass posting.

### Trend 3: Human tone over synthetic polish

- Imperfection and personality can increase trust.
- Over-produced AI-feel can trigger audience rejection.

System requirement:
- Caption style presets should include conversational variants.
- Encourage creator-style framing over sterile templates.

### Trend 4: Serialized clipping is mainstream

- Clipping campaigns and micro-series are now common growth tactics.

System requirement:
- Build series metadata and episode logic into clip scheduler.

## 3. Competitive and policy implications

- Transformative editing is strategic and compliance-critical.
- Channels that only repost raw cuts are higher risk for reused-content or audience fatigue.
- Rights-first gating remains non-negotiable for fan-account workflows.

## 4. Recommendations integrated into build

1. Keep the Authenticity Score gate in MVP and tune weekly.
2. Add a Series Engine in v1.1:
- recurring formats
- episode numbering
- platform-specific hooks
3. Add a Trend Pack refresh ritual every 7 days.
4. Add a Search Optimization checklist to review flow.
5. Enforce anti-repetition window across last 30 clips.

## 5. Metrics to track from day one

- 3-second hold rate
- average watch duration
- rewatch rate
- completion rate
- save/share ratio
- comment-to-view ratio
- format-level performance (series A/B/C)
- authenticity score distribution

## 6. Sources reviewed

- TikTok What's Next 2025 Trend Report (newsroom.tiktok.com)
- Hootsuite 2026 Social Media Trends (blog.hootsuite.com)
- Sprout Social 2026 Social Media Trends (sproutsocial.com)
