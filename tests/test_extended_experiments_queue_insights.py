"""
Extended logic tests for experiments, queue and insights modules.

Targets the remaining uncovered paths in:
  experiments.py  63%  -> set_experiment_status, list_experiments, duplicate link skip,
                          extend_experiment, stop_experiment, promote_experiment,
                          clone_experiment, get_or_create_default_exploration_policy
  queue.py        64%  -> list_review_queue (no rows, with rows, publish_failed flag,
                          _apply_filters, _latest_publication_job)
  insights.py     68%  -> get_insights_dashboard with performance data (creative/slot/
                          platform scoring, recommendation-driven next_actions,
                          top_winners fallback)
"""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.db.models import (
    ExperimentStatus,
    ObservationWindow,
    Platform,
    PublishStatus,
    ReviewStatus,
)
from app.review.experiments import (
    clone_experiment,
    extend_experiment,
    get_or_create_default_exploration_policy,
    list_experiments,
    promote_experiment,
    set_experiment_status,
    stop_experiment,
    upsert_exploration_policy,
)
from app.review.insights import get_insights_dashboard
from app.review.queue import _apply_filters, list_review_queue


# ---------------------------------------------------------------------------
# Shared fake-DB infrastructure
# ---------------------------------------------------------------------------

class _ExecuteResult:
    def __init__(self, first_row=None, all_rows=None):
        self._first_row = first_row
        self._all_rows = all_rows or []

    def first(self):
        return self._first_row

    def all(self):
        return self._all_rows


class _ScalarsResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class _FakeDb:
    def __init__(self, *, scalar_values=None, scalars_values=None, execute_results=None):
        self.scalar_values = list(scalar_values or [])
        self.scalars_values = list(scalars_values or [])
        self.execute_results = list(execute_results or [])
        self.added = []

    def scalar(self, _statement):
        return self.scalar_values.pop(0) if self.scalar_values else None

    def scalars(self, _statement):
        items = self.scalars_values.pop(0) if self.scalars_values else []
        return _ScalarsResult(items)

    def execute(self, _statement):
        return self.execute_results.pop(0) if self.execute_results else _ExecuteResult()

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        return None

    def refresh(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = "generated-id"
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(timezone.utc)


def _make_experiment(exp_id="exp-1", status=ExperimentStatus.active, current=3, target=10):
    return SimpleNamespace(
        id=exp_id,
        name="Test Exp",
        hypothesis="H",
        changed_variables=["hook_pattern"],
        baseline_reference=None,
        sample_size_target=target,
        sample_size_current=current,
        status=status,
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# experiments.set_experiment_status
# ---------------------------------------------------------------------------

def test_set_experiment_status_not_found_raises() -> None:
    db = _FakeDb(scalar_values=[None])
    with pytest.raises(ValueError, match="Experiment not found"):
        set_experiment_status(db=db, experiment_id="missing", status=ExperimentStatus.active)


def test_set_experiment_status_updates_status() -> None:
    exp = _make_experiment(status=ExperimentStatus.draft)
    db = _FakeDb(
        scalar_values=[exp],
        execute_results=[_ExecuteResult(first_row=(0,))],
    )
    result = set_experiment_status(db=db, experiment_id="exp-1", status=ExperimentStatus.active)
    assert exp.status == ExperimentStatus.active
    assert result.status == "active"


# ---------------------------------------------------------------------------
# experiments.list_experiments
# ---------------------------------------------------------------------------

def test_list_experiments_empty_returns_empty() -> None:
    db = _FakeDb(scalars_values=[[]])
    result = list_experiments(db=db)
    assert result == []


def test_list_experiments_returns_all_records() -> None:
    exp_a = _make_experiment("exp-a", ExperimentStatus.draft)
    exp_b = _make_experiment("exp-b", ExperimentStatus.completed)
    db = _FakeDb(
        scalars_values=[[exp_a, exp_b]],
        execute_results=[
            _ExecuteResult(first_row=(0,)),
            _ExecuteResult(first_row=(5,)),
        ],
    )
    result = list_experiments(db=db)
    assert len(result) == 2
    assert {r.status for r in result} == {"draft", "completed"}


def test_list_experiments_with_status_filter_called_without_error() -> None:
    # Verifies filter path doesn't raise; db returns empty for filtered query
    db = _FakeDb(scalars_values=[[]])
    result = list_experiments(db=db, status=ExperimentStatus.active)
    assert result == []


# ---------------------------------------------------------------------------
# experiments.link_snapshot_to_experiment — duplicate skip path
# ---------------------------------------------------------------------------

def test_link_snapshot_to_experiment_skips_duplicate_link() -> None:
    exp = _make_experiment(current=3, target=10, status=ExperimentStatus.active)
    snapshot = SimpleNamespace(id="snap-x")
    existing_link = SimpleNamespace(id="link-1")  # already linked → skip
    db = _FakeDb(
        scalar_values=[exp, snapshot, existing_link],
        execute_results=[_ExecuteResult(first_row=(3,))],
    )
    from app.review.experiments import link_snapshot_to_experiment
    result = link_snapshot_to_experiment(db=db, experiment_id="exp-1", performance_snapshot_id="snap-x")
    # sample_size_current must NOT have been incremented
    assert result.sample_size_current == 3


def test_link_snapshot_to_experiment_snapshot_not_found_raises() -> None:
    exp = _make_experiment()
    db = _FakeDb(scalar_values=[exp, None])
    from app.review.experiments import link_snapshot_to_experiment
    with pytest.raises(ValueError, match="Performance snapshot not found"):
        link_snapshot_to_experiment(db=db, experiment_id="exp-1", performance_snapshot_id="missing-snap")


# ---------------------------------------------------------------------------
# experiments.extend_experiment
# ---------------------------------------------------------------------------

def test_extend_experiment_not_found_raises() -> None:
    db = _FakeDb(scalar_values=[None])
    with pytest.raises(ValueError, match="Experiment not found"):
        extend_experiment(db=db, experiment_id="missing", additional_samples=5)


def test_extend_experiment_increases_sample_size_target() -> None:
    exp = _make_experiment(target=10, current=5)
    db = _FakeDb(
        scalar_values=[exp],
        execute_results=[_ExecuteResult(first_row=(5,))],
    )
    result = extend_experiment(db=db, experiment_id="exp-1", additional_samples=5)
    assert exp.sample_size_target == 15
    assert result.sample_size_target == 15


# ---------------------------------------------------------------------------
# experiments.stop_experiment
# ---------------------------------------------------------------------------

def test_stop_experiment_not_found_raises() -> None:
    db = _FakeDb(scalar_values=[None])
    with pytest.raises(ValueError, match="Experiment not found"):
        stop_experiment(db=db, experiment_id="missing")


def test_stop_experiment_sets_stopped_status() -> None:
    exp = _make_experiment(status=ExperimentStatus.active)
    db = _FakeDb(
        scalar_values=[exp],
        execute_results=[_ExecuteResult(first_row=(0,))],
    )
    result = stop_experiment(db=db, experiment_id="exp-1")
    assert result.status == "stopped"


# ---------------------------------------------------------------------------
# experiments.promote_experiment
# ---------------------------------------------------------------------------

def test_promote_experiment_not_found_raises() -> None:
    db = _FakeDb(scalar_values=[None])
    with pytest.raises(ValueError, match="Experiment not found"):
        promote_experiment(db=db, experiment_id="missing")


def test_promote_experiment_sets_completed_status() -> None:
    exp = _make_experiment(status=ExperimentStatus.active)
    db = _FakeDb(
        scalar_values=[exp],
        execute_results=[_ExecuteResult(first_row=(0,))],
    )
    result = promote_experiment(db=db, experiment_id="exp-1")
    assert result.status == "completed"


# ---------------------------------------------------------------------------
# experiments.clone_experiment
# ---------------------------------------------------------------------------

def test_clone_experiment_not_found_raises() -> None:
    db = _FakeDb(scalar_values=[None])
    with pytest.raises(ValueError, match="Experiment not found"):
        clone_experiment(db=db, experiment_id="missing", name="Clone")


def test_clone_experiment_creates_draft_with_new_name() -> None:
    exp = _make_experiment(status=ExperimentStatus.completed, current=10, target=10)
    db = _FakeDb(scalar_values=[exp])
    result = clone_experiment(db=db, experiment_id="exp-1", name="My Clone")
    assert result.name == "My Clone"
    assert result.status == "draft"
    assert result.sample_size_current == 0
    assert result.linked_snapshot_count == 0


# ---------------------------------------------------------------------------
# experiments.get_or_create_default_exploration_policy
# ---------------------------------------------------------------------------

def test_get_or_create_default_policy_returns_existing() -> None:
    policy = SimpleNamespace(
        id="pol-1",
        name="default",
        target_exploration_ratio=0.25,
        min_exploration_ratio=0.20,
        max_exploration_ratio=0.30,
        active=True,
    )
    db = _FakeDb(scalar_values=[policy])
    result = get_or_create_default_exploration_policy(db=db)
    assert result.name == "default"
    assert result.target_exploration_ratio == 0.25


def test_get_or_create_default_policy_creates_when_missing() -> None:
    # First scalar call returns None → triggers upsert_exploration_policy
    # upsert_exploration_policy calls scalar again → returns None (new policy)
    db = _FakeDb(scalar_values=[None, None])
    result = get_or_create_default_exploration_policy(db=db)
    assert result.name == "default"
    assert result.target_exploration_ratio == 0.25


# ---------------------------------------------------------------------------
# experiments.upsert_exploration_policy — update existing path
# ---------------------------------------------------------------------------

def test_upsert_exploration_policy_updates_existing() -> None:
    existing_policy = SimpleNamespace(
        id="pol-2",
        name="test",
        target_exploration_ratio=0.20,
        min_exploration_ratio=0.10,
        max_exploration_ratio=0.30,
        active=True,
    )
    db = _FakeDb(scalar_values=[existing_policy])
    result = upsert_exploration_policy(
        db=db, name="test",
        target_exploration_ratio=0.25,
        min_exploration_ratio=0.10,
        max_exploration_ratio=0.40,
    )
    assert existing_policy.target_exploration_ratio == 0.25
    assert result.max_exploration_ratio == 0.40


# ---------------------------------------------------------------------------
# queue._apply_filters
# ---------------------------------------------------------------------------

def test_apply_filters_returns_statement_unchanged_with_no_filters() -> None:
    """_apply_filters should return a statement even when all filters are None."""
    from sqlalchemy import select
    from app.db.models import RenderedClip

    statement = select(RenderedClip)
    result = _apply_filters(statement, status=None, risk_only=False, platform=None)
    # The resulting statement must still be a valid Select
    assert result is not None


def test_apply_filters_platform_filter_does_not_raise() -> None:
    """Platform filter is currently a no-op (E4-S2 placeholder) but must not raise."""
    from sqlalchemy import select
    from app.db.models import RenderedClip

    statement = select(RenderedClip)
    result = _apply_filters(statement, status=None, risk_only=False, platform=Platform.tiktok)
    assert result is not None


# ---------------------------------------------------------------------------
# queue.list_review_queue
# ---------------------------------------------------------------------------

def test_list_review_queue_empty_returns_empty_list() -> None:
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[])])
    result = list_review_queue(db=db)
    assert result == []


def test_list_review_queue_builds_item_without_fingerprint() -> None:
    clip = SimpleNamespace(
        id="clip-1",
        review_status=SimpleNamespace(value="review_ready"),
        authenticity_score=85.0,
        render_path="out/clip-1.mp4",
        last_error=None,
        retry_count=0,
    )
    segment = SimpleNamespace(ranking_score=0.8, start_ts=10.0, end_ts=40.0)
    source = SimpleNamespace(
        source_video_id="vid-1", title="My Video", url="https://yt.test/v/1"
    )
    fingerprint = None
    row = (clip, segment, source, fingerprint)

    db = _FakeDb(
        execute_results=[_ExecuteResult(all_rows=[row])],
        scalar_values=[None],  # _latest_publication_job → no job
    )
    result = list_review_queue(db=db)

    assert len(result) == 1
    item = result[0]
    assert item.rendered_clip_id == "clip-1"
    assert item.hook_pattern is None
    assert item.publish_status is None
    assert item.risk_flags == []


def test_list_review_queue_adds_publish_failed_flag() -> None:
    clip = SimpleNamespace(
        id="clip-2",
        review_status=SimpleNamespace(value="review_ready"),
        authenticity_score=90.0,
        render_path="out/clip-2.mp4",
        last_error=None,
        retry_count=0,
    )
    segment = SimpleNamespace(ranking_score=0.7, start_ts=5.0, end_ts=30.0)
    source = SimpleNamespace(source_video_id="vid-2", title="V2", url="https://yt.test/v/2")
    fingerprint = None

    publication = SimpleNamespace(
        distribution_provider=SimpleNamespace(value="buffer"),
        publish_status=PublishStatus.failed,
        external_post_ref=None,
        buffer_post_id="buf-1",
    )

    db = _FakeDb(
        execute_results=[_ExecuteResult(all_rows=[(clip, segment, source, fingerprint)])],
        scalar_values=[publication],
    )
    result = list_review_queue(db=db)

    assert "publish_failed" in result[0].risk_flags


def test_list_review_queue_with_fingerprint_maps_fields() -> None:
    clip = SimpleNamespace(
        id="clip-3",
        review_status=SimpleNamespace(value="review_ready"),
        authenticity_score=75.0,
        render_path="out/clip-3.mp4",
        last_error=None,
        retry_count=0,
    )
    segment = SimpleNamespace(ranking_score=0.6, start_ts=0.0, end_ts=20.0)
    source = SimpleNamespace(source_video_id="vid-3", title="V3", url="https://yt.test/v/3")
    fingerprint = SimpleNamespace(
        hook_pattern="cold_open",
        caption_pack_version="cap-v1",
        font_pack_version="font-v1",
        transition_pack_version=None,
        animation_pack_version=None,
    )

    db = _FakeDb(
        execute_results=[_ExecuteResult(all_rows=[(clip, segment, source, fingerprint)])],
        scalar_values=[None],
    )
    result = list_review_queue(db=db)

    assert result[0].hook_pattern == "cold_open"
    assert result[0].caption_pack_version == "cap-v1"


# ---------------------------------------------------------------------------
# insights.get_insights_dashboard — data-driven paths
# ---------------------------------------------------------------------------

def _make_dashboard_row(
    *,
    platform_value: str = "instagram",
    score: float = 0.75,
    hook: str | None = "cold_open",
    caption: str | None = "cap-v1",
    font: str | None = None,
    publish_time_slot: str | None = None,
    scheduled_hour: int | None = 19,
) -> tuple:
    snapshot = SimpleNamespace(
        performance_score=score,
        observation_window=ObservationWindow.twenty_four_hours,
    )
    publication = SimpleNamespace(
        platform=SimpleNamespace(value=platform_value),
        scheduled_at=datetime(2026, 3, 18, scheduled_hour, 0, tzinfo=timezone.utc)
        if scheduled_hour is not None
        else None,
    )
    clip = SimpleNamespace()
    fingerprint = SimpleNamespace(
        hook_pattern=hook,
        caption_pack_version=caption,
        font_pack_version=font,
        publish_time_slot=publish_time_slot,
    )
    return (snapshot, publication, clip, fingerprint)


def test_insights_dashboard_with_data_builds_platform_comparison(monkeypatch) -> None:
    from app.review import insights

    monkeypatch.setattr(insights, "list_recommendations", lambda **kwargs: [])

    rows = [
        _make_dashboard_row(platform_value="instagram", score=0.6),
        _make_dashboard_row(platform_value="tiktok", score=0.9),
    ]
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=rows)])
    dashboard = get_insights_dashboard(db=db)

    platform_labels = [p.platform for p in dashboard.platform_comparison]
    assert "instagram" in platform_labels
    assert "tiktok" in platform_labels
    # TikTok has higher score → should come first
    assert dashboard.platform_comparison[0].platform == "tiktok"


def test_insights_dashboard_creative_winners_scored(monkeypatch) -> None:
    from app.review import insights

    monkeypatch.setattr(insights, "list_recommendations", lambda **kwargs: [])

    rows = [_make_dashboard_row(hook="cold_open", caption="cap-v1", score=0.8)]
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=rows)])
    dashboard = get_insights_dashboard(db=db)

    winner_labels = [w.label for w in dashboard.top_creative_winners]
    assert any("hook:cold_open" in label for label in winner_labels)
    assert any("caption:cap-v1" in label for label in winner_labels)


def test_insights_dashboard_slot_scores_from_publish_time_slot(monkeypatch) -> None:
    from app.review import insights

    monkeypatch.setattr(insights, "list_recommendations", lambda **kwargs: [])

    rows = [_make_dashboard_row(publish_time_slot="18:00-21:00", scheduled_hour=None, score=0.9)]
    # Need to override scheduled_at=None for this case
    snapshot, publication, clip, fp = rows[0]
    publication = SimpleNamespace(
        platform=SimpleNamespace(value="instagram"),
        scheduled_at=None,
    )
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[(snapshot, publication, clip, fp)])])
    dashboard = get_insights_dashboard(db=db)

    window_labels = [w.label for w in dashboard.best_posting_windows]
    assert "18:00-21:00" in window_labels


def test_insights_dashboard_with_recommendations_builds_next_actions(monkeypatch) -> None:
    from app.review import insights

    fake_recs = [
        SimpleNamespace(dimension="hook_pattern", recommended_value="cold_open", observation_window="24h"),
        SimpleNamespace(dimension="caption", recommended_value="cap-v2", observation_window="24h"),
    ]
    monkeypatch.setattr(insights, "list_recommendations", lambda **kwargs: fake_recs)

    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[])])
    dashboard = get_insights_dashboard(db=db)

    assert len(dashboard.suggested_next_actions) >= 1
    # With no rows but recommendations, the rec-based next_actions path should fire
    assert any("hook_pattern" in action for action in dashboard.suggested_next_actions)


def test_insights_dashboard_no_rows_no_recs_top_winners_fallback(monkeypatch) -> None:
    """With no rows and no recs, the third fallback message should fire."""
    from app.review import insights

    monkeypatch.setattr(insights, "list_recommendations", lambda **kwargs: [])

    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[])])
    dashboard = get_insights_dashboard(db=db)

    assert any("performance snapshots" in action for action in dashboard.suggested_next_actions)


def test_insights_dashboard_top_winners_fallback_fires_when_recs_empty(monkeypatch) -> None:
    """When rows exist (so top_winners is non-empty) but list_recommendations returns [],
    the 'Test more variants' fallback message should appear."""
    from app.review import insights

    monkeypatch.setattr(insights, "list_recommendations", lambda **kwargs: [])

    rows = [_make_dashboard_row(hook="edge_cut", caption=None, score=0.7)]
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=rows)])
    dashboard = get_insights_dashboard(db=db)

    assert any("Test more variants" in action for action in dashboard.suggested_next_actions)
