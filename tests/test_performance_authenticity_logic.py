"""
Logic tests for performance, authenticity and trend_packs modules.

Targets the remaining low-coverage modules:
  performance.py  41%  → pure-function and DB-path coverage
  authenticity.py 49%  → score_and_route_clip routing paths
  trend_packs.py  51%  → set_trend_pack_status / promote_trend_pack / _to_record
"""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.db.models import (
    ObservationWindow,
    PackType,
    Platform,
    ReviewStatus,
    RightsStatus,
    TrendPackStatus,
)
from app.review.authenticity import _latest_rights_status, score_and_route_clip
from app.review.performance import (
    _compute_performance_score,
    _normalize_metrics,
    _safe_ratio,
    _time_slot_baseline,
    get_performance_snapshot_detail,
)
from app.review.trend_packs import _to_record, promote_trend_pack, set_trend_pack_status


# ---------------------------------------------------------------------------
# Shared fake-DB infrastructure
# ---------------------------------------------------------------------------

class _ScalarsResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class _FakeDb:
    """Minimal fake-DB supporting both scalar() and scalars() via pop-queues."""

    def __init__(self, *, scalar_values=None, scalars_values=None):
        self.scalar_values = list(scalar_values or [])
        self.scalars_values = list(scalars_values or [])
        self.added = []

    def scalar(self, _statement):
        return self.scalar_values.pop(0) if self.scalar_values else None

    def scalars(self, _statement):
        items = self.scalars_values.pop(0) if self.scalars_values else []
        return _ScalarsResult(items)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        return None

    def refresh(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = "generated-id"


# ---------------------------------------------------------------------------
# performance._time_slot_baseline
# ---------------------------------------------------------------------------

def test_time_slot_baseline_none_scheduled_at_returns_unknown() -> None:
    label, factor = _time_slot_baseline(None)
    assert label == "unknown"
    assert factor == 1.0


def test_time_slot_baseline_evening_window() -> None:
    dt = datetime(2026, 3, 18, 19, 0, tzinfo=timezone.utc)
    label, factor = _time_slot_baseline(dt)
    assert label == "18:00-21:00"
    assert factor == 1.1


def test_time_slot_baseline_afternoon_window() -> None:
    dt = datetime(2026, 3, 18, 16, 0, tzinfo=timezone.utc)
    label, factor = _time_slot_baseline(dt)
    assert label == "15:00-18:00"
    assert factor == 1.05


def test_time_slot_baseline_midday_window() -> None:
    dt = datetime(2026, 3, 18, 13, 0, tzinfo=timezone.utc)
    label, factor = _time_slot_baseline(dt)
    assert label == "12:00-15:00"
    assert factor == 1.0


def test_time_slot_baseline_off_peak() -> None:
    dt = datetime(2026, 3, 18, 8, 0, tzinfo=timezone.utc)
    label, factor = _time_slot_baseline(dt)
    assert label == "off_peak"
    assert factor == 0.9


# ---------------------------------------------------------------------------
# performance._safe_ratio
# ---------------------------------------------------------------------------

def test_safe_ratio_normal_case() -> None:
    result = _safe_ratio(200.0, 1000.0)
    assert result == pytest.approx(0.2)


def test_safe_ratio_zero_denominator_treated_as_one() -> None:
    # denominator is max(0, 1.0) = 1.0 → no division by zero
    result = _safe_ratio(5.0, 0.0)
    assert result == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# performance._normalize_metrics
# ---------------------------------------------------------------------------

def test_normalize_metrics_zero_views_yields_all_none() -> None:
    metrics = {"views": 0, "likes": 100, "comments": 10, "shares": 5, "saves": 3, "follows_lift": 1}
    normalized, _ = _normalize_metrics(metrics, Platform.instagram, ObservationWindow.twenty_four_hours, None)
    for value in normalized.values():
        assert value is None


def test_normalize_metrics_with_views_yields_floats() -> None:
    metrics = {"views": 1000, "likes": 200, "comments": 50, "shares": 30, "saves": 40, "follows_lift": 5}
    normalized, components = _normalize_metrics(
        metrics, Platform.instagram, ObservationWindow.twenty_four_hours, None
    )
    assert normalized["view_velocity"] is not None
    assert normalized["engagement_rate"] is not None
    assert isinstance(components["platform_baseline"], float)
    assert isinstance(components["window_baseline"], float)


def test_normalize_metrics_tiktok_has_higher_platform_baseline() -> None:
    metrics = {"views": 1000, "likes": 100, "comments": 10, "shares": 5, "saves": 5, "follows_lift": 2}
    _, components_ig = _normalize_metrics(metrics, Platform.instagram, ObservationWindow.twenty_four_hours, None)
    _, components_tt = _normalize_metrics(metrics, Platform.tiktok, ObservationWindow.twenty_four_hours, None)
    assert components_tt["platform_baseline"] > components_ig["platform_baseline"]


# ---------------------------------------------------------------------------
# performance._compute_performance_score
# ---------------------------------------------------------------------------

def test_compute_performance_score_no_view_velocity_returns_none() -> None:
    normalized = {k: None for k in [
        "view_velocity", "engagement_rate", "share_rate",
        "save_rate", "follow_lift", "completion_proxy", "search_discovery_lift",
    ]}
    score, components = _compute_performance_score(normalized, {"platform_baseline": 1.0})
    assert score is None
    assert "reason" in components


def test_compute_performance_score_with_values_returns_float() -> None:
    normalized = {
        "view_velocity": 0.5,
        "engagement_rate": 0.3,
        "share_rate": 0.1,
        "save_rate": 0.05,
        "follow_lift": 0.02,
        "completion_proxy": 0.04,
        "search_discovery_lift": 0.01,
    }
    score, components = _compute_performance_score(normalized, {"platform_baseline": 1.0})
    assert score is not None
    assert score > 0
    assert "formula" in components


# ---------------------------------------------------------------------------
# performance.get_performance_snapshot_detail
# ---------------------------------------------------------------------------

def test_get_performance_snapshot_detail_not_found_raises() -> None:
    db = _FakeDb(scalar_values=[None])
    with pytest.raises(ValueError, match="Performance snapshot not found"):
        get_performance_snapshot_detail(db=db, performance_snapshot_id="missing")


def test_get_performance_snapshot_detail_returns_dataclass() -> None:
    snapshot = SimpleNamespace(
        id="snap-1",
        publication_job_fk="pub-1",
        source=SimpleNamespace(value="instagram"),
        observation_window=SimpleNamespace(value="24h"),
        observed_at=datetime(2026, 3, 18, tzinfo=timezone.utc),
        views=5000,
        likes=250,
        comments=30,
        shares=20,
        saves=15,
        follows_lift=5,
        normalized_metrics={"view_velocity": 0.5},
        score_components={"formula": "..."},
        performance_score=42.5,
    )
    db = _FakeDb(scalar_values=[snapshot])
    result = get_performance_snapshot_detail(db=db, performance_snapshot_id="snap-1")
    assert result.performance_snapshot_id == "snap-1"
    assert result.views == 5000
    assert result.performance_score == pytest.approx(42.5)


# ---------------------------------------------------------------------------
# authenticity._latest_rights_status
# ---------------------------------------------------------------------------

def test_latest_rights_status_no_audit_returns_none() -> None:
    db = _FakeDb(scalar_values=[None])
    result = _latest_rights_status(db=db, rendered_clip_id="clip-1")
    assert result is None


def test_latest_rights_status_with_audit_returns_status() -> None:
    audit = SimpleNamespace(rights_status=RightsStatus.approved)
    db = _FakeDb(scalar_values=[audit])
    result = _latest_rights_status(db=db, rendered_clip_id="clip-1")
    assert result == RightsStatus.approved


# ---------------------------------------------------------------------------
# authenticity.score_and_route_clip
# ---------------------------------------------------------------------------

def test_score_and_route_clip_not_found_raises() -> None:
    db = _FakeDb(scalar_values=[None])
    with pytest.raises(ValueError, match="Rendered clip not found"):
        score_and_route_clip(db=db, rendered_clip_id="missing")


def test_score_and_route_clip_rights_not_approved_hard_fails() -> None:
    clip = SimpleNamespace(id="clip-1", retry_count=0, authenticity_score=None,
                           review_status=None, last_error=None)
    fingerprint = None
    # No audit → rights_status=None → not approved
    db = _FakeDb(scalar_values=[clip, fingerprint, None])

    result = score_and_route_clip(db=db, rendered_clip_id="clip-1")

    assert result.authenticity_score == 0.0
    assert result.review_status == ReviewStatus.rejected.value
    assert "rights" in result.reason.lower()


def test_score_and_route_clip_missing_transform_evidence_rejects() -> None:
    clip = SimpleNamespace(id="clip-2", retry_count=0, authenticity_score=None,
                           review_status=None, last_error=None)
    # Hook only, no caption/context → has_transform=False
    fingerprint = SimpleNamespace(
        hook_pattern="cold_open",
        caption_pack_version=None,
        edit_route=None,
        font_pack_version=None,
        transition_pack_version=None,
        animation_pack_version=None,
    )
    audit = SimpleNamespace(rights_status=RightsStatus.approved)
    db = _FakeDb(scalar_values=[clip, fingerprint, audit])

    result = score_and_route_clip(db=db, rendered_clip_id="clip-2")

    assert result.review_status == ReviewStatus.rejected.value
    assert "transformation" in result.reason.lower()


def test_score_and_route_clip_high_score_routes_to_review_ready() -> None:
    clip = SimpleNamespace(id="clip-3", retry_count=0, authenticity_score=None,
                           review_status=None, last_error=None)
    # hook(30) + caption(25) + context(20) + style(15) = 90 → review_ready
    fingerprint = SimpleNamespace(
        hook_pattern="cold_open",
        caption_pack_version="v1",
        edit_route="context+style",
        font_pack_version="font-v1",
        transition_pack_version=None,
        animation_pack_version=None,
    )
    audit = SimpleNamespace(rights_status=RightsStatus.approved)
    db = _FakeDb(scalar_values=[clip, fingerprint, audit])

    result = score_and_route_clip(db=db, rendered_clip_id="clip-3")

    assert result.authenticity_score == 90.0
    assert result.review_status == ReviewStatus.review_ready.value


def test_score_and_route_clip_medium_score_routes_to_revise() -> None:
    clip = SimpleNamespace(id="clip-4", retry_count=2, authenticity_score=None,
                           review_status=None, last_error=None)
    # hook(30) + caption(25) + context(20) = 75 - 10(penalty) = 65 → revise
    fingerprint = SimpleNamespace(
        hook_pattern="cold_open",
        caption_pack_version="v1",
        edit_route="context+style",
        font_pack_version=None,
        transition_pack_version=None,
        animation_pack_version=None,
    )
    audit = SimpleNamespace(rights_status=RightsStatus.approved)
    db = _FakeDb(scalar_values=[clip, fingerprint, audit])

    result = score_and_route_clip(db=db, rendered_clip_id="clip-4")

    assert result.authenticity_score == 65.0
    assert result.review_status == ReviewStatus.revise.value


# ---------------------------------------------------------------------------
# trend_packs._to_record
# ---------------------------------------------------------------------------

def test_to_record_maps_all_fields() -> None:
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    pack = SimpleNamespace(
        id="pack-1",
        pack_type=SimpleNamespace(value="hook"),
        name="My Hook",
        version="v1",
        status=SimpleNamespace(value="active"),
        promoted_to_default=True,
        retired_reason=None,
        pack_config={"key": "val"},
        performance_score=0.82,
        fatigue_warning=False,
        fatigue_ratio_rolling_30=0.15,
        created_at=ts,
    )
    record = _to_record(pack)

    assert record.trend_pack_id == "pack-1"
    assert record.pack_type == "hook"
    assert record.promoted_to_default is True
    assert record.performance_score == pytest.approx(0.82)


# ---------------------------------------------------------------------------
# trend_packs.set_trend_pack_status
# ---------------------------------------------------------------------------

def test_set_trend_pack_status_not_found_raises() -> None:
    db = _FakeDb(scalar_values=[None])
    with pytest.raises(ValueError, match="Trend pack not found"):
        set_trend_pack_status(db=db, trend_pack_id="missing", status=TrendPackStatus.retired)


def test_set_trend_pack_status_updates_status_and_clears_promoted() -> None:
    pack = SimpleNamespace(
        id="pack-5",
        pack_type=SimpleNamespace(value="hook"),
        name="P",
        version="v1",
        status=TrendPackStatus.active,
        promoted_to_default=True,
        retired_reason=None,
        pack_config=None,
        performance_score=None,
        fatigue_warning=False,
        fatigue_ratio_rolling_30=0.0,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    # scalars_values: empty job list  so _refresh_fatigue short-circuits
    db = _FakeDb(scalar_values=[pack], scalars_values=[[]])

    result = set_trend_pack_status(
        db=db, trend_pack_id="pack-5", status=TrendPackStatus.retired, retired_reason="Stale"
    )

    assert pack.status == TrendPackStatus.retired
    assert pack.promoted_to_default is False
    assert result.status == "retired"


def test_set_trend_pack_status_retired_reason_saved() -> None:
    pack = SimpleNamespace(
        id="pack-6",
        pack_type=SimpleNamespace(value="caption"),
        name="Cap",
        version="v2",
        status=TrendPackStatus.active,
        promoted_to_default=False,
        retired_reason=None,
        pack_config=None,
        performance_score=None,
        fatigue_warning=False,
        fatigue_ratio_rolling_30=0.0,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    db = _FakeDb(scalar_values=[pack], scalars_values=[[]])

    set_trend_pack_status(db=db, trend_pack_id="pack-6", status=TrendPackStatus.retired, retired_reason="Old format")

    assert pack.retired_reason == "Old format"


# ---------------------------------------------------------------------------
# trend_packs.promote_trend_pack
# ---------------------------------------------------------------------------

def test_promote_trend_pack_not_found_raises() -> None:
    db = _FakeDb(scalar_values=[None])
    with pytest.raises(ValueError, match="Trend pack not found"):
        promote_trend_pack(db=db, trend_pack_id="missing")


def test_promote_trend_pack_sets_promoted_and_demotes_sibling() -> None:
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    target = SimpleNamespace(
        id="pack-A",
        pack_type=PackType.hook,
        name="A",
        version="v2",
        status=TrendPackStatus.active,
        promoted_to_default=False,
        retired_reason=None,
        pack_config=None,
        performance_score=None,
        fatigue_warning=False,
        fatigue_ratio_rolling_30=0.0,
        created_at=ts,
    )
    sibling = SimpleNamespace(
        id="pack-B",
        pack_type=PackType.hook,
        name="B",
        version="v1",
        status=TrendPackStatus.active,
        promoted_to_default=True,  # previously promoted
        retired_reason=None,
        pack_config=None,
        performance_score=None,
        fatigue_warning=False,
        fatigue_ratio_rolling_30=0.0,
        created_at=ts,
    )
    # scalars_values: siblings list, then empty jobs for _refresh_fatigue
    db = _FakeDb(scalar_values=[target], scalars_values=[[target, sibling], []])

    result = promote_trend_pack(db=db, trend_pack_id="pack-A")

    assert target.promoted_to_default is True
    assert target.status == TrendPackStatus.active
    assert sibling.promoted_to_default is False
    assert result.trend_pack_id == "pack-A"
