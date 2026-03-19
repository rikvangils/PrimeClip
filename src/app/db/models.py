from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class IngestStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    rejected = "rejected"


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ReviewStatus(str, enum.Enum):
    review_ready = "review_ready"
    revise = "revise"
    rejected = "rejected"
    approved = "approved"


class RenderStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Platform(str, enum.Enum):
    instagram = "instagram"
    tiktok = "tiktok"


class DistributionProvider(str, enum.Enum):
    manual = "manual"
    buffer = "buffer"
    tiktok = "tiktok"


class PublishStatus(str, enum.Enum):
    pending = "pending"
    scheduled = "scheduled"
    published = "published"
    failed = "failed"


class RightsStatus(str, enum.Enum):
    unknown = "unknown"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ObservationWindow(str, enum.Enum):
    one_hour = "1h"
    twenty_four_hours = "24h"
    forty_eight_hours = "48h"


class PerformanceSource(str, enum.Enum):
    buffer = "buffer"
    instagram = "instagram"
    tiktok = "tiktok"


class RecommendationDimension(str, enum.Enum):
    hook_pattern = "hook_pattern"
    caption_pack_version = "caption_pack_version"
    font_pack_version = "font_pack_version"
    publish_time_slot = "publish_time_slot"
    platform = "platform"


class ExperimentStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    completed = "completed"
    stopped = "stopped"


class PackType(str, enum.Enum):
    hook = "hook"
    caption = "caption"
    font = "font"
    transition = "transition"
    animation = "animation"
    series_format = "series_format"


class TrendPackStatus(str, enum.Enum):
    experiment = "experiment"
    active = "active"
    paused = "paused"
    retired = "retired"


class SourceVideo(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_videos"

    source_video_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    channel_id: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingest_status: Mapped[IngestStatus] = mapped_column(
        Enum(IngestStatus, name="ingest_status_enum"), nullable=False, default=IngestStatus.pending
    )

    ingest_jobs: Mapped[list[IngestJob]] = relationship(back_populates="source_video")
    candidate_segments: Mapped[list[CandidateSegment]] = relationship(back_populates="source_video")
    analysis_signal: Mapped[SourceAnalysisSignal | None] = relationship(back_populates="source_video")


class SourceAnalysisSignal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_analysis_signals"
    __table_args__ = (UniqueConstraint("source_video_fk", name="uq_source_analysis_signals_source_video_fk"),)

    source_video_fk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_videos.id", ondelete="CASCADE"), nullable=False
    )
    transcript_segments: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    audio_markers: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    scene_cuts: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)

    source_video: Mapped[SourceVideo] = relationship(back_populates="analysis_signal")


class IngestJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ingest_jobs"

    source_video_fk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_videos.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum"), nullable=False, default=JobStatus.pending
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text())

    source_video: Mapped[SourceVideo] = relationship(back_populates="ingest_jobs")


class CandidateSegment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "candidate_segments"

    source_video_fk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_videos.id", ondelete="CASCADE"), nullable=False
    )
    start_ts: Mapped[float] = mapped_column(Float, nullable=False)
    end_ts: Mapped[float] = mapped_column(Float, nullable=False)
    ranking_score: Mapped[float] = mapped_column(Float, nullable=False)

    source_video: Mapped[SourceVideo] = relationship(back_populates="candidate_segments")
    rendered_clips: Mapped[list[RenderedClip]] = relationship(back_populates="candidate_segment")


class RenderedClip(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "rendered_clips"
    __table_args__ = (
        UniqueConstraint("candidate_segment_fk", "variant_name", name="uq_rendered_clips_candidate_segment_variant"),
    )

    candidate_segment_fk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_segments.id", ondelete="CASCADE"), nullable=False
    )
    variant_name: Mapped[str] = mapped_column(String(64), nullable=False, default="default")
    render_status: Mapped[RenderStatus] = mapped_column(
        Enum(RenderStatus, name="render_status_enum"), nullable=False, default=RenderStatus.pending
    )
    render_path: Mapped[str | None] = mapped_column(String(1024))
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text())
    authenticity_score: Mapped[float | None] = mapped_column(Float)
    review_status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="review_status_enum"), nullable=False, default=ReviewStatus.review_ready
    )

    candidate_segment: Mapped[CandidateSegment] = relationship(back_populates="rendered_clips")
    publication_jobs: Mapped[list[PublicationJob]] = relationship(back_populates="rendered_clip")
    creative_fingerprint: Mapped[CreativeFingerprint | None] = relationship(back_populates="rendered_clip")
    compliance_audit: Mapped[list[ComplianceAudit]] = relationship(back_populates="rendered_clip")


class PublicationJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "publication_jobs"

    rendered_clip_fk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rendered_clips.id", ondelete="CASCADE"), nullable=False
    )
    distribution_provider: Mapped[DistributionProvider] = mapped_column(
        Enum(DistributionProvider, name="distribution_provider_enum"), nullable=False, default=DistributionProvider.manual
    )
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)
    external_post_ref: Mapped[str | None] = mapped_column(String(1024))
    buffer_post_id: Mapped[str | None] = mapped_column(String(255))
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    publish_status: Mapped[PublishStatus] = mapped_column(
        Enum(PublishStatus, name="publish_status_enum"), nullable=False, default=PublishStatus.pending
    )

    rendered_clip: Mapped[RenderedClip] = relationship(back_populates="publication_jobs")
    performance_snapshots: Mapped[list[PerformanceSnapshot]] = relationship(back_populates="publication_job")


class CreativeFingerprint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "creative_fingerprints"
    __table_args__ = (UniqueConstraint("rendered_clip_fk", name="uq_creative_fingerprints_rendered_clip_fk"),)

    rendered_clip_fk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rendered_clips.id", ondelete="CASCADE"), nullable=False
    )
    hook_pattern: Mapped[str | None] = mapped_column(String(255))
    title_variant: Mapped[str | None] = mapped_column(String(255))
    caption_pack_version: Mapped[str | None] = mapped_column(String(64))
    font_pack_version: Mapped[str | None] = mapped_column(String(64))
    transition_pack_version: Mapped[str | None] = mapped_column(String(64))
    animation_pack_version: Mapped[str | None] = mapped_column(String(64))
    edit_route: Mapped[str | None] = mapped_column(String(64))
    duration_bucket: Mapped[str | None] = mapped_column(String(64))
    publish_time_slot: Mapped[str | None] = mapped_column(String(64))

    rendered_clip: Mapped[RenderedClip] = relationship(back_populates="creative_fingerprint")


class ComplianceAudit(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "compliance_audit"

    rendered_clip_fk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rendered_clips.id", ondelete="CASCADE"), nullable=False
    )
    rights_status: Mapped[RightsStatus] = mapped_column(
        Enum(RightsStatus, name="rights_status_enum"), nullable=False, default=RightsStatus.unknown
    )
    decision_reason: Mapped[str | None] = mapped_column(Text())
    reviewer_id: Mapped[str | None] = mapped_column(String(255))
    fan_account_disclosed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    rendered_clip: Mapped[RenderedClip] = relationship(back_populates="compliance_audit")


class PerformanceSnapshot(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "performance_snapshots"

    publication_job_fk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("publication_jobs.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[PerformanceSource] = mapped_column(
        Enum(PerformanceSource, name="performance_source_enum"), nullable=False
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observation_window: Mapped[ObservationWindow] = mapped_column(
        Enum(ObservationWindow, name="observation_window_enum"), nullable=False
    )
    views: Mapped[int | None] = mapped_column(Integer)
    likes: Mapped[int | None] = mapped_column(Integer)
    comments: Mapped[int | None] = mapped_column(Integer)
    shares: Mapped[int | None] = mapped_column(Integer)
    saves: Mapped[int | None] = mapped_column(Integer)
    follows_lift: Mapped[int | None] = mapped_column(Integer)
    normalized_metrics: Mapped[dict | None] = mapped_column(JSONB)
    score_components: Mapped[dict | None] = mapped_column(JSONB)
    performance_score: Mapped[float | None] = mapped_column(Numeric(10, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    publication_job: Mapped[PublicationJob] = relationship(back_populates="performance_snapshots")
    experiment_links: Mapped[list[ExperimentSnapshotLink]] = relationship(back_populates="performance_snapshot")


class OptimizationRecommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "optimization_recommendations"

    dimension: Mapped[RecommendationDimension] = mapped_column(
        Enum(RecommendationDimension, name="recommendation_dimension_enum"), nullable=False
    )
    recommended_value: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[Platform | None] = mapped_column(Enum(Platform, name="platform_enum"), nullable=True)
    observation_window: Mapped[ObservationWindow] = mapped_column(
        Enum(ObservationWindow, name="observation_window_enum"), nullable=False
    )
    expected_uplift: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSONB)


class ExperimentRegistry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "experiment_registry"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    changed_variables: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    baseline_reference: Mapped[str | None] = mapped_column(String(255))
    sample_size_target: Mapped[int] = mapped_column(Integer, nullable=False)
    sample_size_current: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus, name="experiment_status_enum"), nullable=False, default=ExperimentStatus.draft
    )

    snapshot_links: Mapped[list[ExperimentSnapshotLink]] = relationship(back_populates="experiment")


class ExperimentSnapshotLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "experiment_snapshot_links"
    __table_args__ = (
        UniqueConstraint("experiment_fk", "performance_snapshot_fk", name="uq_experiment_snapshot_link"),
    )

    experiment_fk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiment_registry.id", ondelete="CASCADE"), nullable=False
    )
    performance_snapshot_fk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("performance_snapshots.id", ondelete="CASCADE"), nullable=False
    )

    experiment: Mapped[ExperimentRegistry] = relationship(back_populates="snapshot_links")
    performance_snapshot: Mapped[PerformanceSnapshot] = relationship(back_populates="experiment_links")


class ExplorationPolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "exploration_policies"

    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    target_exploration_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    min_exploration_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    max_exploration_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)


class TrendPack(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trend_packs"
    __table_args__ = (UniqueConstraint("pack_type", "version", name="uq_trend_packs_pack_type_version"),)

    pack_type: Mapped[PackType] = mapped_column(Enum(PackType, name="pack_type_enum"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[TrendPackStatus] = mapped_column(
        Enum(TrendPackStatus, name="trend_pack_status_enum"), nullable=False, default=TrendPackStatus.experiment
    )
    promoted_to_default: Mapped[bool] = mapped_column(default=False, nullable=False)
    retired_reason: Mapped[str | None] = mapped_column(Text())
    pack_config: Mapped[dict | None] = mapped_column(JSONB)
    performance_score: Mapped[float | None] = mapped_column(Float)
    fatigue_warning: Mapped[bool] = mapped_column(default=False, nullable=False)
    fatigue_ratio_rolling_30: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)