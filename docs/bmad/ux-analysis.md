# UX Analysis - PeanutClip AutoFlow

Status: Draft  
Date: 18 March 2026

## Objective

Determine the most effective operator experience for a solo user managing an AI-assisted clip pipeline with review, scheduling, analytics, and self-learning optimization.

## Executive summary

The UX must optimize for fast judgment, low cognitive load, and explainable automation.

Key insights:

- The operator should not bounce between many views to answer one question.
- Performance dashboards must be actionable, not just informative.
- Recommendations need explanation, not only rankings.
- Alerts must be selective or the operator will ignore them.
- The system should feel like a creator tool, not a generic BI dashboard.

## 1. Core user jobs

The primary operator needs to do five jobs quickly:

1. Review newly generated clips.
2. Decide what gets posted, revised, or rejected.
3. Understand what creative patterns are winning.
4. Trust or override the system’s recommendations.
5. Monitor failures, rights risk, and trend decay.

## 2. UX signals from current research

### Insight A: Single-dashboard orientation matters

Observed pattern:
- Social analytics tools emphasize one understandable view across channels.
- Operators benefit from seeing post analytics, timing advice, and content-type performance in one place.

UX implication:
- Use a command-center homepage with status, queue, and top learnings.
- Do not split review and optimization into disconnected tools.

### Insight B: Easy-to-understand analytics win

Observed pattern:
- Buffer emphasizes learn-what-works, best-time-to-post, cross-channel views, and clear reports.

UX implication:
- Show concise metrics with short explanations.
- Highlight decisions the operator can take next, not raw metric dumps.

### Insight C: Reach and discovery metrics need context

Observed pattern:
- YouTube reach analytics frame performance around discovery source, CTR, views, watch time, and search terms.

UX implication:
- Show not just result metrics, but how content was found and where hooks/search language succeeded.
- Make discoverability an explicit part of performance review.

### Insight D: Alert fatigue is a real operational risk

Observed pattern:
- Operational tools become noisy if every failure, recommendation, and metric change is elevated equally.

UX implication:
- Use severity tiers and digest views.
- Only interrupt for publish blockers, rights issues, or severe performance anomalies.

## 3. UX principles for this product

1. Review first
- The most important workflow is approving or revising clips.

2. Explain the why
- Every recommendation needs a reason, evidence window, and confidence.

3. Keep the loop visible
- The operator must see how published results affect future clips.

4. Optimize without losing authorship
- Automation should feel assistive, not like it is taking over creative judgment.

5. Minimize mode switching
- Preview, evidence, recommendation, and override should exist in one flow.

## 4. Recommended information architecture

### Primary navigation

- Home
- Review Queue
- Scheduled & Published
- Insights
- Experiments
- Trend Packs
- Compliance
- Settings

### Why this structure

- Review Queue supports daily operational work.
- Insights and Experiments support weekly optimization work.
- Trend Packs support creative control.
- Compliance isolates rights and policy tasks from creative tasks.

## 5. Critical UX requirements

### Review Queue

Must show:
- clip preview
- source context
- authenticity score
- recommended platform(s)
- recommended posting slot
- top risk flags
- top reason to approve or revise

### Insights view

Must show:
- winning hooks
- winning title patterns
- winning transition/font/animation packs
- best posting windows by platform
- discoverability signals
- experiment outcomes

### Recommendation cards

Must show:
- recommendation
- confidence
- supporting window (for example last 30 clips)
- expected upside
- reason
- override action

### Alerts

Interruptive only for:
- rights/compliance block
- publish failure
- metrics ingestion failure over threshold
- major performance drop against baseline

Non-interruptive for:
- minor ranking shifts
- low-confidence experiments
- routine trend refresh suggestions

## 6. Operator cadence design

### Daily loop

- open Home
- triage Review Queue
- approve/revise/reject clips
- confirm schedule
- inspect blockers

### Weekly loop

- inspect Insights
- review recommendation changes
- promote or retire packs
- assess experiment winners/losers
- adjust exploration percentage if needed

## 7. Product decisions to carry into UX design

- Use a creator-style control room, not a spreadsheet-heavy admin.
- Give every metric a plain-language label and action.
- Tie recommendations to evidence and confidence.
- Separate urgent blockers from ambient optimization.
- Keep trend pack management and experiment control visible and editable.

## 8. Sources

- Buffer Analyze product UX and feature framing
- YouTube Reach analytics concepts
- Prior project market and optimization analyses
