"""
Logic tests for publication_views, queue, recommendations and insights modules.

These tests cover the lower-coverage modules (27-36%) without requiring a live database.
The _FakeDb helper reuses the same queue-based pattern as test_experiments_recommendation_logic.py.
"""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.db.models import ObservationWindow, Platform, ReviewStatus
from app.review.insights import _top_grouped_scores, get_insights_dashboard
from app.review.publication_views import _snapshot_summary, list_publication_jobs, publication_calendar
from app.review.queue import _risk_flags, apply_review_decision
from app.review.recommendations import _choose_platform, _choose_time_slot, get_scheduling_recommendation
from app.review.schemas import PublicationListItem, ReviewDecisionAction


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


class _FakeDb:
    def __init__(self, *, scalar_values=None, execute_results=None):
        self.scalar_values = list(scalar_values or [])
        self.execute_results = list(execute_results or [])
        self.added = []

    def scalar(self, _statement):
        return self.scalar_values.pop(0) if self.scalar_values else None

    def execute(self, _statement):
        return self.execute_results.pop(0) if self.execute_results else _ExecuteResult()

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        return None

    def refresh(self, obj):
        pass


# ---------------------------------------------------------------------------
# publication_views._snapshot_summary
# ---------------------------------------------------------------------------

def test_snapshot_summary_no_row_returns_zeros() -> None:
    db = _FakeDb(execute_results=[_ExecuteResult(first_row=None)])
    count, latest = _snapshot_summary(db, "pub-1")
    assert count == 0
    assert latest is None


def test_snapshot_summary_with_row_returns_values() -> None:
    ts = datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc)
    db = _FakeDb(execute_results=[_ExecuteResult(first_row=(3, ts))])
    count, latest = _snapshot_summary(db, "pub-2")
    assert count == 3
    assert latest == ts


def test_snapshot_summary_none_count_coerces_to_zero() -> None:
    db = _FakeDb(execute_results=[_ExecuteResult(first_row=(None, None))])
    count, latest = _snapshot_summary(db, "pub-3")
    assert count == 0


# ---------------------------------------------------------------------------
# publication_views.list_publication_jobs
# ---------------------------------------------------------------------------

def test_list_publication_jobs_empty_db_returns_empty_list() -> None:
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[])])
    result = list_publication_jobs(db=db)
    assert result == []


def test_list_publication_jobs_builds_single_item(monkeypatch) -> None:
    from app.review import publication_views

    monkeypatch.setattr(publication_views, "_snapshot_summary", lambda _db, _id: (5, None))

    pub = SimpleNamespace(
        id="pub-1",
        distribution_provider=SimpleNamespace(value="manual"),
        platform=SimpleNamespace(value="instagram"),
        publish_status=SimpleNamespace(value="scheduled"),
        scheduled_at=None,
        external_post_ref=None,
        buffer_post_id=None,
    )
    clip = SimpleNamespace(id="clip-1")
    segment = SimpleNamespace()
    source = SimpleNamespace(title="Test Video")

    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[(pub, clip, segment, source)])])
    result = list_publication_jobs(db=db)

    assert len(result) == 1
    assert result[0].publication_job_id == "pub-1"
    assert result[0].rendered_clip_id == "clip-1"
    assert result[0].source_title == "Test Video"
    assert result[0].performance_snapshot_count == 5
    assert result[0].platform == "instagram"


# ---------------------------------------------------------------------------
# publication_views.publication_calendar
# ---------------------------------------------------------------------------

def _make_pub_item(pub_id: str, scheduled_at: datetime | None) -> PublicationListItem:
    return PublicationListItem(
        publication_job_id=pub_id,
        rendered_clip_id=f"clip-{pub_id}",
        source_title="Video",
        distribution_provider="manual",
        platform="instagram",
        publish_status="scheduled",
        scheduled_at=scheduled_at,
        external_post_ref=None,
        buffer_post_id=None,
        performance_snapshot_count=0,
        last_snapshot_at=None,
    )


def test_publication_calendar_groups_by_date(monkeypatch) -> None:
    from app.review import publication_views

    dt_a = datetime(2025, 7, 10, 10, 0, tzinfo=timezone.utc)
    dt_b = datetime(2025, 7, 11, 14, 0, tzinfo=timezone.utc)
    items = [_make_pub_item("a", dt_a), _make_pub_item("b", dt_b)]
    monkeypatch.setattr(publication_views, "list_publication_jobs", lambda *args, **kwargs: items)

    days = publication_calendar(db=None)  # type: ignore[arg-type]

    assert len(days) == 2
    assert days[0].date == "2025-07-10"
    assert days[1].date == "2025-07-11"
    assert days[0].items[0].publication_job_id == "a"


def test_publication_calendar_unscheduled_uses_unscheduled_key(monkeypatch) -> None:
    from app.review import publication_views

    items = [_make_pub_item("x", None)]
    monkeypatch.setattr(publication_views, "list_publication_jobs", lambda *args, **kwargs: items)

    days = publication_calendar(db=None)  # type: ignore[arg-type]

    assert len(days) == 1
    assert days[0].date == "unscheduled"


def test_publication_calendar_sorts_dates_alphabetically(monkeypatch) -> None:
    from app.review import publication_views

    dt_late = datetime(2025, 9, 1, 0, 0, tzinfo=timezone.utc)
    dt_early = datetime(2025, 8, 1, 0, 0, tzinfo=timezone.utc)
    # Intentionally out of chronological order to verify sorting
    items = [_make_pub_item("late", dt_late), _make_pub_item("early", dt_early)]
    monkeypatch.setattr(publication_views, "list_publication_jobs", lambda *args, **kwargs: items)

    days = publication_calendar(db=None)  # type: ignore[arg-type]

    assert days[0].date == "2025-08-01"
    assert days[1].date == "2025-09-01"


# ---------------------------------------------------------------------------
# queue._risk_flags
# ---------------------------------------------------------------------------

def test_queue_risk_flags_missing_score_adds_flag() -> None:
    clip = SimpleNamespace(authenticity_score=None, last_error=None, retry_count=0)
    assert "missing_authenticity_score" in _risk_flags(clip)


def test_queue_risk_flags_low_score_adds_flag() -> None:
    clip = SimpleNamespace(authenticity_score=55.0, last_error=None, retry_count=0)
    assert "low_authenticity_score" in _risk_flags(clip)


def test_queue_risk_flags_processing_error_adds_flag() -> None:
    clip = SimpleNamespace(authenticity_score=80.0, last_error="render failed", retry_count=0)
    assert "processing_error" in _risk_flags(clip)


def test_queue_risk_flags_high_retry_adds_flag() -> None:
    clip = SimpleNamespace(authenticity_score=80.0, last_error=None, retry_count=3)
    assert "high_retry_count" in _risk_flags(clip)


def test_queue_risk_flags_healthy_clip_returns_empty() -> None:
    clip = SimpleNamespace(authenticity_score=85.0, last_error=None, retry_count=0)
    assert _risk_flags(clip) == []


def test_queue_risk_flags_multiple_issues_returned_together() -> None:
    clip = SimpleNamespace(authenticity_score=None, last_error="boom", retry_count=5)
    flags = _risk_flags(clip)
    assert "missing_authenticity_score" in flags
    assert "processing_error" in flags
    assert "high_retry_count" in flags


# ---------------------------------------------------------------------------
# queue.apply_review_decision
# ---------------------------------------------------------------------------

def test_apply_review_decision_not_found_raises() -> None:
    db = _FakeDb(scalar_values=[None])
    with pytest.raises(ValueError, match="Rendered clip not found"):
        apply_review_decision(db=db, rendered_clip_id="missing", action=ReviewDecisionAction.approve)


def test_apply_review_decision_approve_sets_status_and_clears_error() -> None:
    clip = SimpleNamespace(id="clip-a", review_status=None, last_error="old error")
    db = _FakeDb(scalar_values=[clip])
    result = apply_review_decision(db=db, rendered_clip_id="clip-a", action=ReviewDecisionAction.approve)
    assert result.review_status == ReviewStatus.approved
    assert result.last_error is None


def test_apply_review_decision_revise_sets_status() -> None:
    clip = SimpleNamespace(id="clip-b", review_status=None, last_error=None)
    db = _FakeDb(scalar_values=[clip])
    result = apply_review_decision(db=db, rendered_clip_id="clip-b", action=ReviewDecisionAction.revise)
    assert result.review_status == ReviewStatus.revise


def test_apply_review_decision_reject_sets_status() -> None:
    clip = SimpleNamespace(id="clip-c", review_status=None, last_error=None)
    db = _FakeDb(scalar_values=[clip])
    result = apply_review_decision(db=db, rendered_clip_id="clip-c", action=ReviewDecisionAction.reject)
    assert result.review_status == ReviewStatus.rejected


# ---------------------------------------------------------------------------
# recommendations._choose_platform
# ---------------------------------------------------------------------------

def test_choose_platform_high_auth_and_ranking_gives_tiktok() -> None:
    platform, reasons = _choose_platform(authenticity_score=85.0, ranking_score=0.80)
    assert platform == Platform.tiktok
    assert any("authenticity" in r.lower() for r in reasons)


def test_choose_platform_high_auth_borderline_ranking_gives_instagram() -> None:
    # ranking < 0.75 should fall through to the second branch
    platform, _ = _choose_platform(authenticity_score=85.0, ranking_score=0.50)
    assert platform == Platform.instagram


def test_choose_platform_medium_auth_gives_instagram() -> None:
    platform, _ = _choose_platform(authenticity_score=72.0, ranking_score=0.40)
    assert platform == Platform.instagram


def test_choose_platform_none_auth_treated_as_zero_gives_instagram() -> None:
    # None → 0.0; 0.0 < 70 → conservative branch
    platform, _ = _choose_platform(authenticity_score=None, ranking_score=0.90)
    assert platform == Platform.instagram


# ---------------------------------------------------------------------------
# recommendations._choose_time_slot
# ---------------------------------------------------------------------------

def test_choose_time_slot_stream_title_gives_evening_window() -> None:
    slot, reasons = _choose_time_slot("Sunday stream recap", ranking_score=0.5)
    assert slot == "18:00-21:00"
    assert any("evening" in r.lower() or "stream" in r.lower() for r in reasons)


def test_choose_time_slot_live_title_gives_evening_window() -> None:
    slot, _ = _choose_time_slot("Best of live show", ranking_score=0.5)
    assert slot == "18:00-21:00"


def test_choose_time_slot_high_ranking_gives_afternoon_window() -> None:
    slot, _ = _choose_time_slot("Normal video", ranking_score=0.85)
    assert slot == "15:00-18:00"


def test_choose_time_slot_default_gives_midday_window() -> None:
    slot, _ = _choose_time_slot("Normal video", ranking_score=0.50)
    assert slot == "12:00-15:00"


def test_get_scheduling_recommendation_not_found_raises() -> None:
    db = _FakeDb(execute_results=[_ExecuteResult(first_row=None)])
    with pytest.raises(ValueError, match="Rendered clip not found"):
        get_scheduling_recommendation(db=db, rendered_clip_id="nope")


# ---------------------------------------------------------------------------
# insights._top_grouped_scores
# ---------------------------------------------------------------------------

def test_top_grouped_scores_empty_dict_returns_empty_list() -> None:
    assert _top_grouped_scores({}) == []


def test_top_grouped_scores_sorted_highest_first() -> None:
    grouped = {"low": [0.3, 0.5], "high": [0.9, 0.9]}
    result = _top_grouped_scores(grouped)
    assert result[0].label == "high"
    assert result[0].average_score == pytest.approx(0.9)
    assert result[1].label == "low"


def test_top_grouped_scores_respects_limit() -> None:
    grouped = {f"item{i}": [float(i)] for i in range(10)}
    result = _top_grouped_scores(grouped, limit=3)
    assert len(result) == 3


def test_top_grouped_scores_skips_empty_score_lists() -> None:
    grouped = {"has_scores": [0.8], "empty": []}
    result = _top_grouped_scores(grouped)
    labels = [item.label for item in result]
    assert "has_scores" in labels
    assert "empty" not in labels


# ---------------------------------------------------------------------------
# insights.get_insights_dashboard
# ---------------------------------------------------------------------------

def test_get_insights_dashboard_empty_rows_returns_fallback_action(monkeypatch) -> None:
    from app.review import insights

    monkeypatch.setattr(insights, "list_recommendations", lambda **kwargs: [])

    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[])])
    dashboard = get_insights_dashboard(db=db)

    assert dashboard.top_creative_winners == []
    assert dashboard.best_posting_windows == []
    assert dashboard.platform_comparison == []
    assert len(dashboard.suggested_next_actions) == 1
    assert "performance snapshots" in dashboard.suggested_next_actions[0]


def test_get_insights_dashboard_observation_window_in_output(monkeypatch) -> None:
    from app.review import insights

    monkeypatch.setattr(insights, "list_recommendations", lambda **kwargs: [])

    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[])])
    dashboard = get_insights_dashboard(db=db, observation_window=ObservationWindow.twenty_four_hours)

    assert dashboard.observation_window == ObservationWindow.twenty_four_hours.value
