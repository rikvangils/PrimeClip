from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import ObservationWindow, PackType, Platform, ReviewStatus, RightsStatus, TrendPackStatus
from app.db.session import get_db
from app.review.experiments import (
    clone_experiment,
    create_experiment,
    extend_experiment,
    get_experiments_workspace,
    get_exploration_budget_summary,
    get_or_create_default_exploration_policy,
    link_snapshot_to_experiment,
    list_experiments,
    promote_experiment,
    set_experiment_status,
    stop_experiment,
    upsert_exploration_policy,
)
from app.review.compliance import get_clip_compliance, set_clip_compliance
from app.review.insights import get_insights_dashboard
from app.integrations.tiktok_oauth import (
    TikTokOAuthError,
    build_tiktok_authorize_url,
    exchange_code_for_tokens,
    refresh_tiktok_access_token,
)
from app.review.performance import get_performance_snapshot_detail, ingest_performance_snapshot
from app.review.publishing import schedule_clip_for_distribution, sync_publication_job_status
from app.review.publication_views import list_publication_jobs, publication_calendar
from app.review.queue import apply_review_decision, list_review_queue
from app.review.recommendation_engine import generate_recommendations, list_recommendations
from app.review.recommendations import get_scheduling_recommendation
from app.review.schemas import (
    BufferScheduleRequest,
    BufferScheduleResponse,
    ExperimentCreateRequest,
    ExperimentActionResponse,
    ExperimentCloneRequest,
    ExperimentExtendRequest,
    ExperimentItem,
    ExperimentLinkSnapshotRequest,
    ExperimentListResponse,
    ExperimentsWorkspaceResponse,
    ExperimentWorkspaceItem,
    ExplorationBudgetSummaryResponse,
    ExplorationPolicyResponse,
    ExplorationPolicyUpsertRequest,
    InsightsDashboardResponse,
    PerformanceSnapshotDetailResponse,
    PerformanceSnapshotIngestRequest,
    PerformanceSnapshotIngestResponse,
    PublicationCalendarResponse,
    PublicationListResponse,
    PublicationStatusSyncResponse,
    RecommendationGenerateRequest,
    RecommendationItem,
    RecommendationListResponse,
    ComplianceAuditResponse,
    ComplianceSetRequest,
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    SchedulingRecommendationResponse,
    TrendPackCreateRequest,
    TrendPackItem,
    TrendPackListResponse,
    TrendPackStatusRequest,
    ReviewQueueResponse,
    TikTokOAuthStartResponse,
    TikTokOAuthTokenResponse,
    TikTokTokenRefreshRequest,
)
from app.db.models import ExperimentStatus, PublishStatus
from app.review.trend_packs import create_trend_pack, list_trend_packs, promote_trend_pack, set_trend_pack_status

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/integrations/tiktok/oauth/start", response_model=TikTokOAuthStartResponse)
def get_tiktok_oauth_start(
    state: str | None = Query(default=None),
) -> TikTokOAuthStartResponse:
    resolved_state = state or secrets.token_urlsafe(24)
    try:
        auth_url = build_tiktok_authorize_url(state=resolved_state)
    except TikTokOAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TikTokOAuthStartResponse(auth_url=auth_url, state=resolved_state)


@router.get("/integrations/tiktok/oauth/callback", response_model=TikTokOAuthTokenResponse)
def get_tiktok_oauth_callback(
    code: str = Query(..., min_length=1),
    state: str | None = Query(default=None),
) -> TikTokOAuthTokenResponse:
    _ = state
    try:
        bundle = exchange_code_for_tokens(code=code)
    except TikTokOAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TikTokOAuthTokenResponse(
        access_token=bundle.access_token,
        expires_in=bundle.expires_in,
        refresh_token=bundle.refresh_token,
        refresh_expires_in=bundle.refresh_expires_in,
        open_id=bundle.open_id,
        scope=bundle.scope,
        token_type=bundle.token_type,
    )


@router.post("/integrations/tiktok/token/refresh", response_model=TikTokOAuthTokenResponse)
def post_tiktok_refresh_token(
    payload: TikTokTokenRefreshRequest,
) -> TikTokOAuthTokenResponse:
    try:
        bundle = refresh_tiktok_access_token(refresh_token=payload.refresh_token)
    except TikTokOAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TikTokOAuthTokenResponse(
        access_token=bundle.access_token,
        expires_in=bundle.expires_in,
        refresh_token=bundle.refresh_token,
        refresh_expires_in=bundle.refresh_expires_in,
        open_id=bundle.open_id,
        scope=bundle.scope,
        token_type=bundle.token_type,
    )


@router.get("/queue", response_model=ReviewQueueResponse)
def get_review_queue(
    status: ReviewStatus | None = Query(default=None),
    risk_only: bool = Query(default=False),
    platform: Platform | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> ReviewQueueResponse:
    items = list_review_queue(db=db, status=status, risk_only=risk_only, platform=platform, limit=limit)
    return ReviewQueueResponse(items=items)


@router.post("/clips/{rendered_clip_id}/decision", response_model=ReviewDecisionResponse)
def post_review_decision(
    rendered_clip_id: str,
    payload: ReviewDecisionRequest,
    db: Session = Depends(get_db),
) -> ReviewDecisionResponse:
    try:
        clip = apply_review_decision(db=db, rendered_clip_id=rendered_clip_id, action=payload.action)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ReviewDecisionResponse(rendered_clip_id=str(clip.id), review_status=clip.review_status.value)


@router.get("/clips/{rendered_clip_id}/schedule-recommendation", response_model=SchedulingRecommendationResponse)
def get_clip_schedule_recommendation(
    rendered_clip_id: str,
    db: Session = Depends(get_db),
) -> SchedulingRecommendationResponse:
    try:
        recommendation = get_scheduling_recommendation(db=db, rendered_clip_id=rendered_clip_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return SchedulingRecommendationResponse(
        rendered_clip_id=recommendation.rendered_clip_id,
        recommended_platform=recommendation.recommended_platform.value,
        recommended_time_slot=recommendation.recommended_time_slot,
        confidence=recommendation.confidence,
        rationale=recommendation.rationale,
    )


@router.post("/clips/{rendered_clip_id}/schedule", response_model=BufferScheduleResponse)
def schedule_clip(
    rendered_clip_id: str,
    payload: BufferScheduleRequest,
    db: Session = Depends(get_db),
) -> BufferScheduleResponse:
    try:
        publication = schedule_clip_for_distribution(
            db=db,
            rendered_clip_id=rendered_clip_id,
            platform=payload.platform,
            scheduled_at=payload.scheduled_at,
            caption=payload.caption,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return BufferScheduleResponse(
        publication_job_id=str(publication.id),
        rendered_clip_id=rendered_clip_id,
        distribution_provider=publication.distribution_provider.value,
        platform=publication.platform.value,
        publish_status=publication.publish_status.value,
        external_post_ref=publication.external_post_ref,
        buffer_post_id=publication.buffer_post_id,
    )


@router.post("/publication-jobs/{publication_job_id}/sync-status", response_model=PublicationStatusSyncResponse)
def sync_publication_status(
    publication_job_id: str,
    db: Session = Depends(get_db),
) -> PublicationStatusSyncResponse:
    try:
        publication = sync_publication_job_status(db=db, publication_job_id=publication_job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PublicationStatusSyncResponse(
        publication_job_id=str(publication.id),
        publish_status=publication.publish_status.value,
    )


@router.get("/publication-jobs", response_model=PublicationListResponse)
def get_publication_jobs(
    status: PublishStatus | None = Query(default=None),
    platform: Platform | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    db: Session = Depends(get_db),
) -> PublicationListResponse:
    items = list_publication_jobs(db=db, status=status, platform=platform, limit=limit)
    return PublicationListResponse(items=items)


@router.get("/publication-calendar", response_model=PublicationCalendarResponse)
def get_publication_calendar(
    status: PublishStatus | None = Query(default=None),
    platform: Platform | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
) -> PublicationCalendarResponse:
    days = publication_calendar(db=db, status=status, platform=platform, limit=limit)
    return PublicationCalendarResponse(days=days)


@router.post(
    "/publication-jobs/{publication_job_id}/performance-snapshots",
    response_model=PerformanceSnapshotIngestResponse,
)
def post_performance_snapshot(
    publication_job_id: str,
    payload: PerformanceSnapshotIngestRequest,
    db: Session = Depends(get_db),
) -> PerformanceSnapshotIngestResponse:
    try:
        result = ingest_performance_snapshot(db=db, publication_job_id=publication_job_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return PerformanceSnapshotIngestResponse(
        performance_snapshot_id=result.snapshot_id,
        publication_job_id=result.publication_job_id,
        source=result.source,
        observation_window=result.observation_window,
        performance_score=result.performance_score,
        normalized_metrics=result.normalized_metrics,
        score_components=result.score_components,
        adapter_warning=result.adapter_warning,
    )


@router.get(
    "/performance-snapshots/{performance_snapshot_id}",
    response_model=PerformanceSnapshotDetailResponse,
)
def get_performance_snapshot(
    performance_snapshot_id: str,
    db: Session = Depends(get_db),
) -> PerformanceSnapshotDetailResponse:
    try:
        result = get_performance_snapshot_detail(db=db, performance_snapshot_id=performance_snapshot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return PerformanceSnapshotDetailResponse(
        performance_snapshot_id=result.performance_snapshot_id,
        publication_job_id=result.publication_job_id,
        source=result.source,
        observation_window=result.observation_window,
        observed_at=result.observed_at,
        views=result.views,
        likes=result.likes,
        comments=result.comments,
        shares=result.shares,
        saves=result.saves,
        follows_lift=result.follows_lift,
        normalized_metrics=result.normalized_metrics,
        score_components=result.score_components,
        performance_score=result.performance_score,
    )


@router.post("/recommendations/generate", response_model=RecommendationListResponse)
def post_generate_recommendations(
    payload: RecommendationGenerateRequest,
    db: Session = Depends(get_db),
) -> RecommendationListResponse:
    results = generate_recommendations(
        db=db,
        observation_window=payload.observation_window,
        platform=payload.platform,
        minimum_samples=payload.minimum_samples,
    )
    return RecommendationListResponse(
        items=[
            RecommendationItem(
                recommendation_id=result.recommendation_id,
                dimension=result.dimension,
                recommended_value=result.recommended_value,
                platform=result.platform,
                observation_window=result.observation_window,
                expected_uplift=result.expected_uplift,
                confidence=result.confidence,
                rationale=result.rationale,
                evidence=result.evidence,
                created_at=result.created_at,
            )
            for result in results
        ]
    )


@router.get("/recommendations", response_model=RecommendationListResponse)
def get_recommendations(
    observation_window: ObservationWindow | None = Query(default=None),
    platform: Platform | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    db: Session = Depends(get_db),
) -> RecommendationListResponse:
    results = list_recommendations(db=db, observation_window=observation_window, platform=platform, limit=limit)
    return RecommendationListResponse(
        items=[
            RecommendationItem(
                recommendation_id=result.recommendation_id,
                dimension=result.dimension,
                recommended_value=result.recommended_value,
                platform=result.platform,
                observation_window=result.observation_window,
                expected_uplift=result.expected_uplift,
                confidence=result.confidence,
                rationale=result.rationale,
                evidence=result.evidence,
                created_at=result.created_at,
            )
            for result in results
        ]
    )


@router.get("/insights", response_model=InsightsDashboardResponse)
def get_insights(
    observation_window: ObservationWindow = Query(default=ObservationWindow.twenty_four_hours),
    db: Session = Depends(get_db),
) -> InsightsDashboardResponse:
    result = get_insights_dashboard(db=db, observation_window=observation_window)
    return InsightsDashboardResponse(
        observation_window=result.observation_window,
        top_creative_winners=result.top_creative_winners,
        best_posting_windows=result.best_posting_windows,
        platform_comparison=result.platform_comparison,
        suggested_next_actions=result.suggested_next_actions,
    )


@router.post("/experiments", response_model=ExperimentItem)
def post_create_experiment(
    payload: ExperimentCreateRequest,
    db: Session = Depends(get_db),
) -> ExperimentItem:
    try:
        result = create_experiment(
            db=db,
            name=payload.name,
            hypothesis=payload.hypothesis,
            changed_variables=payload.changed_variables,
            baseline_reference=payload.baseline_reference,
            sample_size_target=payload.sample_size_target,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ExperimentItem(**result.__dict__)


@router.get("/experiments", response_model=ExperimentListResponse)
def get_experiments(
    status: ExperimentStatus | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    db: Session = Depends(get_db),
) -> ExperimentListResponse:
    results = list_experiments(db=db, status=status, limit=limit)
    return ExperimentListResponse(items=[ExperimentItem(**result.__dict__) for result in results])


@router.post("/experiments/{experiment_id}/snapshots", response_model=ExperimentItem)
def post_link_snapshot_to_experiment(
    experiment_id: str,
    payload: ExperimentLinkSnapshotRequest,
    db: Session = Depends(get_db),
) -> ExperimentItem:
    try:
        result = link_snapshot_to_experiment(
            db=db,
            experiment_id=experiment_id,
            performance_snapshot_id=payload.performance_snapshot_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ExperimentItem(**result.__dict__)


@router.post("/experiments/{experiment_id}/status", response_model=ExperimentItem)
def post_set_experiment_status(
    experiment_id: str,
    status: ExperimentStatus = Query(...),
    db: Session = Depends(get_db),
) -> ExperimentItem:
    try:
        result = set_experiment_status(db=db, experiment_id=experiment_id, status=status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ExperimentItem(**result.__dict__)


@router.put("/exploration-policy", response_model=ExplorationPolicyResponse)
def put_exploration_policy(
    payload: ExplorationPolicyUpsertRequest,
    db: Session = Depends(get_db),
) -> ExplorationPolicyResponse:
    try:
        result = upsert_exploration_policy(
            db=db,
            name=payload.name,
            target_exploration_ratio=payload.target_exploration_ratio,
            min_exploration_ratio=payload.min_exploration_ratio,
            max_exploration_ratio=payload.max_exploration_ratio,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ExplorationPolicyResponse(**result.__dict__)


@router.get("/exploration-policy", response_model=ExplorationPolicyResponse)
def get_exploration_policy(db: Session = Depends(get_db)) -> ExplorationPolicyResponse:
    result = get_or_create_default_exploration_policy(db=db)
    return ExplorationPolicyResponse(**result.__dict__)


@router.get("/exploration-budget", response_model=ExplorationBudgetSummaryResponse)
def get_exploration_budget(db: Session = Depends(get_db)) -> ExplorationBudgetSummaryResponse:
    result = get_exploration_budget_summary(db=db)
    return ExplorationBudgetSummaryResponse(
        policy=ExplorationPolicyResponse(**result.policy.__dict__),
        experiment_publication_count=result.experiment_publication_count,
        total_publication_count=result.total_publication_count,
        current_exploration_ratio=result.current_exploration_ratio,
        within_target_band=result.within_target_band,
    )


@router.get("/experiments/workspace", response_model=ExperimentsWorkspaceResponse)
def get_experiment_workspace(
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
) -> ExperimentsWorkspaceResponse:
    active, completed = get_experiments_workspace(db=db, limit=limit)
    return ExperimentsWorkspaceResponse(
        active=[ExperimentWorkspaceItem(**row.__dict__) for row in active],
        completed=[ExperimentWorkspaceItem(**row.__dict__) for row in completed],
    )


@router.post("/experiments/{experiment_id}/extend", response_model=ExperimentActionResponse)
def post_extend_experiment(
    experiment_id: str,
    payload: ExperimentExtendRequest,
    db: Session = Depends(get_db),
) -> ExperimentActionResponse:
    try:
        result = extend_experiment(db=db, experiment_id=experiment_id, additional_samples=payload.additional_samples)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExperimentActionResponse(experiment=ExperimentItem(**result.__dict__), action="extend")


@router.post("/experiments/{experiment_id}/clone", response_model=ExperimentActionResponse)
def post_clone_experiment(
    experiment_id: str,
    payload: ExperimentCloneRequest,
    db: Session = Depends(get_db),
) -> ExperimentActionResponse:
    try:
        result = clone_experiment(db=db, experiment_id=experiment_id, name=payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExperimentActionResponse(experiment=ExperimentItem(**result.__dict__), action="clone")


@router.post("/experiments/{experiment_id}/stop", response_model=ExperimentActionResponse)
def post_stop_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
) -> ExperimentActionResponse:
    try:
        result = stop_experiment(db=db, experiment_id=experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExperimentActionResponse(experiment=ExperimentItem(**result.__dict__), action="stop")


@router.post("/experiments/{experiment_id}/promote", response_model=ExperimentActionResponse)
def post_promote_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
) -> ExperimentActionResponse:
    try:
        result = promote_experiment(db=db, experiment_id=experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExperimentActionResponse(experiment=ExperimentItem(**result.__dict__), action="promote")


@router.get("/clips/{rendered_clip_id}/compliance", response_model=ComplianceAuditResponse)
def get_clip_compliance_record(
    rendered_clip_id: str,
    db: Session = Depends(get_db),
) -> ComplianceAuditResponse:
    audit = get_clip_compliance(db=db, rendered_clip_id=rendered_clip_id)
    if audit is None:
        raise HTTPException(status_code=404, detail="No compliance record found for this clip.")
    return ComplianceAuditResponse(
        compliance_audit_id=str(audit.id),
        rendered_clip_id=str(audit.rendered_clip_fk),
        rights_status=audit.rights_status.value,
        decision_reason=audit.decision_reason,
        reviewer_id=audit.reviewer_id,
        fan_account_disclosed=audit.fan_account_disclosed,
        created_at=audit.created_at,
    )


@router.post("/clips/{rendered_clip_id}/compliance", response_model=ComplianceAuditResponse)
def set_clip_compliance_record(
    rendered_clip_id: str,
    payload: ComplianceSetRequest,
    db: Session = Depends(get_db),
) -> ComplianceAuditResponse:
    try:
        rights_status = RightsStatus(payload.rights_status)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid rights_status: {payload.rights_status!r}")
    try:
        audit = set_clip_compliance(
            db=db,
            rendered_clip_id=rendered_clip_id,
            rights_status=rights_status,
            decision_reason=payload.decision_reason,
            reviewer_id=payload.reviewer_id,
            fan_account_disclosed=payload.fan_account_disclosed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ComplianceAuditResponse(
        compliance_audit_id=str(audit.id),
        rendered_clip_id=str(audit.rendered_clip_fk),
        rights_status=audit.rights_status.value,
        decision_reason=audit.decision_reason,
        reviewer_id=audit.reviewer_id,
        fan_account_disclosed=audit.fan_account_disclosed,
        created_at=audit.created_at,
    )


@router.post("/trend-packs", response_model=TrendPackItem)
def post_trend_pack(
    payload: TrendPackCreateRequest,
    db: Session = Depends(get_db),
) -> TrendPackItem:
    try:
        result = create_trend_pack(
            db=db,
            pack_type=payload.pack_type,
            name=payload.name,
            version=payload.version,
            status=payload.status,
            pack_config=payload.pack_config,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return TrendPackItem(**result.__dict__)


@router.get("/trend-packs", response_model=TrendPackListResponse)
def get_trend_packs(
    pack_type: PackType | None = Query(default=None),
    status: TrendPackStatus | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
) -> TrendPackListResponse:
    results = list_trend_packs(db=db, pack_type=pack_type, status=status, limit=limit)
    return TrendPackListResponse(items=[TrendPackItem(**result.__dict__) for result in results])


@router.post("/trend-packs/{trend_pack_id}/status", response_model=TrendPackItem)
def post_trend_pack_status(
    trend_pack_id: str,
    payload: TrendPackStatusRequest,
    db: Session = Depends(get_db),
) -> TrendPackItem:
    try:
        result = set_trend_pack_status(
            db=db,
            trend_pack_id=trend_pack_id,
            status=payload.status,
            retired_reason=payload.retired_reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return TrendPackItem(**result.__dict__)


@router.post("/trend-packs/{trend_pack_id}/promote", response_model=TrendPackItem)
def post_promote_trend_pack(
    trend_pack_id: str,
    db: Session = Depends(get_db),
) -> TrendPackItem:
    try:
        result = promote_trend_pack(db=db, trend_pack_id=trend_pack_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return TrendPackItem(**result.__dict__)