from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models import ObservationWindow, PackType, PerformanceSource, Platform, RecommendationDimension
from app.db.models import ExperimentStatus
from app.db.models import TrendPackStatus


class ReviewDecisionAction(str, enum.Enum):
    approve = "approve"
    revise = "revise"
    reject = "reject"


class ReviewQueueItem(BaseModel):
    rendered_clip_id: str
    review_status: str
    authenticity_score: float | None
    render_path: str | None
    source_video_id: str
    source_title: str
    source_url: str
    ranking_score: float
    start_ts: float
    end_ts: float
    hook_pattern: str | None = None
    caption_pack_version: str | None = None
    font_pack_version: str | None = None
    transition_pack_version: str | None = None
    animation_pack_version: str | None = None
    distribution_provider: str | None = None
    external_post_ref: str | None = None
    publish_status: str | None = None
    buffer_post_id: str | None = None
    risk_flags: list[str] = Field(default_factory=list)


class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItem]


class ReviewDecisionRequest(BaseModel):
    action: ReviewDecisionAction


class ReviewDecisionResponse(BaseModel):
    rendered_clip_id: str
    review_status: str


class SchedulingRecommendationResponse(BaseModel):
    rendered_clip_id: str
    recommended_platform: str
    recommended_time_slot: str
    confidence: float
    rationale: list[str]


class BufferScheduleRequest(BaseModel):
    platform: Platform
    scheduled_at: datetime
    caption: str = Field(min_length=3, max_length=2200)


class BufferScheduleResponse(BaseModel):
    publication_job_id: str
    rendered_clip_id: str
    distribution_provider: str
    platform: str
    publish_status: str
    external_post_ref: str | None
    buffer_post_id: str | None


class TikTokOAuthStartResponse(BaseModel):
    auth_url: str
    state: str


class TikTokTokenRefreshRequest(BaseModel):
    refresh_token: str | None = None


class TikTokOAuthTokenResponse(BaseModel):
    access_token: str
    expires_in: int | None = None
    refresh_token: str | None = None
    refresh_expires_in: int | None = None
    open_id: str | None = None
    scope: str | None = None
    token_type: str | None = None


class PublicationStatusSyncResponse(BaseModel):
    publication_job_id: str
    publish_status: str


class PublicationListItem(BaseModel):
    publication_job_id: str
    rendered_clip_id: str
    source_title: str
    distribution_provider: str
    platform: str
    publish_status: str
    scheduled_at: datetime | None
    external_post_ref: str | None
    buffer_post_id: str | None
    performance_snapshot_count: int
    last_snapshot_at: datetime | None


class PublicationListResponse(BaseModel):
    items: list[PublicationListItem]


class PublicationCalendarDay(BaseModel):
    date: str
    items: list[PublicationListItem]


class PublicationCalendarResponse(BaseModel):
    days: list[PublicationCalendarDay]


class PerformanceSnapshotIngestRequest(BaseModel):
    source: PerformanceSource
    observation_window: ObservationWindow
    mode: str = Field(default="pull", pattern="^(pull|manual)$")
    observed_at: datetime | None = None
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    saves: int | None = None
    follows_lift: int | None = None


class PerformanceSnapshotIngestResponse(BaseModel):
    performance_snapshot_id: str
    publication_job_id: str
    source: str
    observation_window: str
    performance_score: float | None
    normalized_metrics: dict[str, float | None] | None = None
    score_components: dict[str, float | str | None] | None = None
    adapter_warning: str | None = None


class PerformanceSnapshotDetailResponse(BaseModel):
    performance_snapshot_id: str
    publication_job_id: str
    source: str
    observation_window: str
    observed_at: datetime
    views: int | None
    likes: int | None
    comments: int | None
    shares: int | None
    saves: int | None
    follows_lift: int | None
    normalized_metrics: dict[str, float | None] | None = None
    score_components: dict[str, float | str | None] | None = None
    performance_score: float | None


class RecommendationGenerateRequest(BaseModel):
    observation_window: ObservationWindow = ObservationWindow.twenty_four_hours
    platform: Platform | None = None
    minimum_samples: int = Field(default=1, ge=1, le=100)


class RecommendationItem(BaseModel):
    recommendation_id: str
    dimension: str
    recommended_value: str
    platform: str | None
    observation_window: str
    expected_uplift: float | None
    confidence: float
    rationale: str
    evidence: dict[str, float | int | str | None] | None = None
    created_at: datetime


class RecommendationListResponse(BaseModel):
    items: list[RecommendationItem]


class InsightWinnerItem(BaseModel):
    label: str
    average_score: float
    sample_count: int


class PlatformComparisonItem(BaseModel):
    platform: str
    average_score: float
    sample_count: int


class InsightsDashboardResponse(BaseModel):
    observation_window: str
    top_creative_winners: list[InsightWinnerItem]
    best_posting_windows: list[InsightWinnerItem]
    platform_comparison: list[PlatformComparisonItem]
    suggested_next_actions: list[str]


class ExperimentCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    hypothesis: str = Field(min_length=10)
    changed_variables: list[str] = Field(min_length=1, max_length=2)
    baseline_reference: str | None = None
    sample_size_target: int = Field(ge=1, le=500)


class ExperimentLinkSnapshotRequest(BaseModel):
    performance_snapshot_id: str


class ExperimentItem(BaseModel):
    experiment_id: str
    name: str
    hypothesis: str
    changed_variables: list[str]
    baseline_reference: str | None
    sample_size_target: int
    sample_size_current: int
    status: str
    linked_snapshot_count: int
    created_at: datetime


class ExperimentListResponse(BaseModel):
    items: list[ExperimentItem]


class ExplorationPolicyUpsertRequest(BaseModel):
    name: str = Field(default="default")
    target_exploration_ratio: float = Field(ge=0.0, le=1.0)
    min_exploration_ratio: float = Field(ge=0.0, le=1.0)
    max_exploration_ratio: float = Field(ge=0.0, le=1.0)


class ExplorationPolicyResponse(BaseModel):
    policy_id: str
    name: str
    target_exploration_ratio: float
    min_exploration_ratio: float
    max_exploration_ratio: float
    active: bool


class ExplorationBudgetSummaryResponse(BaseModel):
    policy: ExplorationPolicyResponse
    experiment_publication_count: int
    total_publication_count: int
    current_exploration_ratio: float
    within_target_band: bool


class TrendPackCreateRequest(BaseModel):
    pack_type: PackType
    name: str = Field(min_length=3, max_length=255)
    version: str = Field(min_length=2, max_length=64)
    status: TrendPackStatus = TrendPackStatus.experiment
    pack_config: dict | None = None


class TrendPackStatusRequest(BaseModel):
    status: TrendPackStatus
    retired_reason: str | None = None


class TrendPackItem(BaseModel):
    trend_pack_id: str
    pack_type: str
    name: str
    version: str
    status: str
    promoted_to_default: bool
    retired_reason: str | None
    pack_config: dict | None
    performance_score: float | None
    fatigue_warning: bool
    fatigue_ratio_rolling_30: float
    created_at: datetime


class TrendPackListResponse(BaseModel):
    items: list[TrendPackItem]


class ExperimentWorkspaceItem(BaseModel):
    experiment_id: str
    name: str
    status: str
    changed_variables: list[str]
    sample_size_target: int
    sample_size_current: int
    confidence: float
    uplift: float | None


class ExperimentsWorkspaceResponse(BaseModel):
    active: list[ExperimentWorkspaceItem]
    completed: list[ExperimentWorkspaceItem]


class ExperimentExtendRequest(BaseModel):
    additional_samples: int = Field(ge=1, le=1000)


class ExperimentCloneRequest(BaseModel):
    name: str = Field(min_length=3, max_length=255)


class ExperimentActionResponse(BaseModel):
    experiment: ExperimentItem
    action: str


class ComplianceSetRequest(BaseModel):
    rights_status: str
    decision_reason: str | None = None
    reviewer_id: str | None = None
    fan_account_disclosed: bool = False


class ComplianceAuditResponse(BaseModel):
    compliance_audit_id: str
    rendered_clip_id: str
    rights_status: str
    decision_reason: str | None
    reviewer_id: str | None
    fan_account_disclosed: bool
    created_at: datetime