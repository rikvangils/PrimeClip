"""Initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-03-18 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


ingest_status_enum = sa.Enum("pending", "processing", "completed", "failed", "rejected", name="ingest_status_enum")
job_status_enum = sa.Enum("pending", "running", "completed", "failed", name="job_status_enum")
review_status_enum = sa.Enum("review_ready", "revise", "rejected", "approved", name="review_status_enum")
render_status_enum = sa.Enum("pending", "processing", "completed", "failed", name="render_status_enum")
platform_enum = sa.Enum("instagram", "tiktok", name="platform_enum")
distribution_provider_enum = sa.Enum("manual", "buffer", name="distribution_provider_enum")
publish_status_enum = sa.Enum("pending", "scheduled", "published", "failed", name="publish_status_enum")
rights_status_enum = sa.Enum("unknown", "pending", "approved", "rejected", name="rights_status_enum")
observation_window_enum = sa.Enum("1h", "24h", "48h", name="observation_window_enum")
performance_source_enum = sa.Enum("buffer", "instagram", "tiktok", name="performance_source_enum")
recommendation_dimension_enum = sa.Enum(
    "hook_pattern",
    "caption_pack_version",
    "font_pack_version",
    "publish_time_slot",
    "platform",
    name="recommendation_dimension_enum",
)
experiment_status_enum = sa.Enum("draft", "active", "paused", "completed", "stopped", name="experiment_status_enum")
pack_type_enum = sa.Enum("hook", "caption", "font", "transition", "animation", "series_format", name="pack_type_enum")
trend_pack_status_enum = sa.Enum("experiment", "active", "paused", "retired", name="trend_pack_status_enum")


def upgrade() -> None:
    bind = op.get_bind()
    ingest_status_enum.create(bind, checkfirst=True)
    job_status_enum.create(bind, checkfirst=True)
    review_status_enum.create(bind, checkfirst=True)
    render_status_enum.create(bind, checkfirst=True)
    platform_enum.create(bind, checkfirst=True)
    distribution_provider_enum.create(bind, checkfirst=True)
    publish_status_enum.create(bind, checkfirst=True)
    rights_status_enum.create(bind, checkfirst=True)
    observation_window_enum.create(bind, checkfirst=True)
    performance_source_enum.create(bind, checkfirst=True)
    recommendation_dimension_enum.create(bind, checkfirst=True)
    experiment_status_enum.create(bind, checkfirst=True)
    pack_type_enum.create(bind, checkfirst=True)
    trend_pack_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "source_videos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_video_id", sa.String(length=128), nullable=False),
        sa.Column("channel_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingest_status", ingest_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_source_videos"),
        sa.UniqueConstraint("source_video_id", name="uq_source_videos_source_video_id"),
    )

    op.create_table(
        "ingest_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_video_fk", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", job_status_enum, nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["source_video_fk"], ["source_videos.id"], name="fk_ingest_jobs_source_video_fk_source_videos", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_ingest_jobs"),
    )

    op.create_table(
        "source_analysis_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_video_fk", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transcript_segments", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("audio_markers", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("scene_cuts", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["source_video_fk"], ["source_videos.id"], name="fk_source_analysis_signals_source_video_fk_source_videos", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_source_analysis_signals"),
        sa.UniqueConstraint("source_video_fk", name="uq_source_analysis_signals_source_video_fk"),
    )

    op.create_table(
        "candidate_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_video_fk", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_ts", sa.Float(), nullable=False),
        sa.Column("end_ts", sa.Float(), nullable=False),
        sa.Column("ranking_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["source_video_fk"], ["source_videos.id"], name="fk_candidate_segments_source_video_fk_source_videos", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_candidate_segments"),
    )

    op.create_table(
        "rendered_clips",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_segment_fk", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_name", sa.String(length=64), nullable=False, server_default="default"),
        sa.Column("render_status", render_status_enum, nullable=False, server_default="pending"),
        sa.Column("render_path", sa.String(length=1024), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("authenticity_score", sa.Float(), nullable=True),
        sa.Column("review_status", review_status_enum, nullable=False, server_default="review_ready"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["candidate_segment_fk"], ["candidate_segments.id"], name="fk_rendered_clips_candidate_segment_fk_candidate_segments", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_rendered_clips"),
        sa.UniqueConstraint("candidate_segment_fk", "variant_name", name="uq_rendered_clips_candidate_segment_variant"),
    )

    op.create_table(
        "publication_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rendered_clip_fk", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("distribution_provider", distribution_provider_enum, nullable=False, server_default="manual"),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("external_post_ref", sa.String(length=1024), nullable=True),
        sa.Column("buffer_post_id", sa.String(length=255), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("publish_status", publish_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["rendered_clip_fk"], ["rendered_clips.id"], name="fk_publication_jobs_rendered_clip_fk_rendered_clips", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_publication_jobs"),
    )

    op.create_table(
        "creative_fingerprints",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rendered_clip_fk", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hook_pattern", sa.String(length=255), nullable=True),
        sa.Column("title_variant", sa.String(length=255), nullable=True),
        sa.Column("caption_pack_version", sa.String(length=64), nullable=True),
        sa.Column("font_pack_version", sa.String(length=64), nullable=True),
        sa.Column("transition_pack_version", sa.String(length=64), nullable=True),
        sa.Column("animation_pack_version", sa.String(length=64), nullable=True),
        sa.Column("edit_route", sa.String(length=64), nullable=True),
        sa.Column("duration_bucket", sa.String(length=64), nullable=True),
        sa.Column("publish_time_slot", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["rendered_clip_fk"], ["rendered_clips.id"], name="fk_creative_fingerprints_rendered_clip_fk_rendered_clips", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_creative_fingerprints"),
        sa.UniqueConstraint("rendered_clip_fk", name="uq_creative_fingerprints_rendered_clip_fk"),
    )

    op.create_table(
        "compliance_audit",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rendered_clip_fk", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rights_status", rights_status_enum, nullable=False, server_default="unknown"),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("reviewer_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["rendered_clip_fk"], ["rendered_clips.id"], name="fk_compliance_audit_rendered_clip_fk_rendered_clips", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_compliance_audit"),
    )

    op.create_table(
        "performance_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("publication_job_fk", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", performance_source_enum, nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observation_window", observation_window_enum, nullable=False),
        sa.Column("views", sa.Integer(), nullable=True),
        sa.Column("likes", sa.Integer(), nullable=True),
        sa.Column("comments", sa.Integer(), nullable=True),
        sa.Column("shares", sa.Integer(), nullable=True),
        sa.Column("saves", sa.Integer(), nullable=True),
        sa.Column("follows_lift", sa.Integer(), nullable=True),
        sa.Column("normalized_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("score_components", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("performance_score", sa.Numeric(10, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["publication_job_fk"], ["publication_jobs.id"], name="fk_performance_snapshots_publication_job_fk_publication_jobs", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_performance_snapshots"),
    )

    op.create_table(
        "optimization_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dimension", recommendation_dimension_enum, nullable=False),
        sa.Column("recommended_value", sa.String(length=255), nullable=False),
        sa.Column("platform", platform_enum, nullable=True),
        sa.Column("observation_window", observation_window_enum, nullable=False),
        sa.Column("expected_uplift", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_optimization_recommendations"),
    )

    op.create_table(
        "experiment_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("changed_variables", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("baseline_reference", sa.String(length=255), nullable=True),
        sa.Column("sample_size_target", sa.Integer(), nullable=False),
        sa.Column("sample_size_current", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", experiment_status_enum, nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_experiment_registry"),
    )

    op.create_table(
        "experiment_snapshot_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("experiment_fk", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("performance_snapshot_fk", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["experiment_fk"], ["experiment_registry.id"], name="fk_experiment_snapshot_links_experiment_fk_experiment_registry", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["performance_snapshot_fk"], ["performance_snapshots.id"], name="fk_experiment_snapshot_links_performance_snapshot_fk_performance_snapshots", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_experiment_snapshot_links"),
        sa.UniqueConstraint("experiment_fk", "performance_snapshot_fk", name="uq_experiment_snapshot_link"),
    )

    op.create_table(
        "exploration_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("target_exploration_ratio", sa.Float(), nullable=False),
        sa.Column("min_exploration_ratio", sa.Float(), nullable=False),
        sa.Column("max_exploration_ratio", sa.Float(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_exploration_policies"),
        sa.UniqueConstraint("name", name="uq_exploration_policies_name"),
    )

    op.create_table(
        "trend_packs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pack_type", pack_type_enum, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("status", trend_pack_status_enum, nullable=False, server_default="experiment"),
        sa.Column("promoted_to_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("retired_reason", sa.Text(), nullable=True),
        sa.Column("pack_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("performance_score", sa.Float(), nullable=True),
        sa.Column("fatigue_warning", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("fatigue_ratio_rolling_30", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_trend_packs"),
        sa.UniqueConstraint("pack_type", "version", name="uq_trend_packs_pack_type_version"),
    )


def downgrade() -> None:
    op.drop_table("exploration_policies")
    op.drop_table("trend_packs")
    op.drop_table("experiment_snapshot_links")
    op.drop_table("experiment_registry")
    op.drop_table("optimization_recommendations")
    op.drop_table("performance_snapshots")
    op.drop_table("compliance_audit")
    op.drop_table("creative_fingerprints")
    op.drop_table("publication_jobs")
    op.drop_table("rendered_clips")
    op.drop_table("candidate_segments")
    op.drop_table("source_analysis_signals")
    op.drop_table("ingest_jobs")
    op.drop_table("source_videos")

    bind = op.get_bind()
    observation_window_enum.drop(bind, checkfirst=True)
    rights_status_enum.drop(bind, checkfirst=True)
    publish_status_enum.drop(bind, checkfirst=True)
    distribution_provider_enum.drop(bind, checkfirst=True)
    platform_enum.drop(bind, checkfirst=True)
    review_status_enum.drop(bind, checkfirst=True)
    render_status_enum.drop(bind, checkfirst=True)
    job_status_enum.drop(bind, checkfirst=True)
    ingest_status_enum.drop(bind, checkfirst=True)
    performance_source_enum.drop(bind, checkfirst=True)
    recommendation_dimension_enum.drop(bind, checkfirst=True)
    experiment_status_enum.drop(bind, checkfirst=True)
    pack_type_enum.drop(bind, checkfirst=True)
    trend_pack_status_enum.drop(bind, checkfirst=True)