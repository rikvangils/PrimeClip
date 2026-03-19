"""
Tests voor de resterende niet-gedekte paden in performance.py en trend_packs.py.

Gedekte paden:
  performance._pull_metrics:
    - buffer success (adapter retourneert waarden)
    - instagram success
    - tiktok raises AnalyticsAdapterError (altijd) → foutpad in _pull_metrics
    - leeg buffer_post_id → AnalyticsAdapterError voor alle drie
  performance.ingest_performance_snapshot:
    - pull-mode (niet manual) → roept _pull_metrics aan
    - manual-mode met gevulde metrics → normalisatie en score berekend
    - adapter-warning wordt doorgegeven bij foutpad
  trend_packs.list_trend_packs:
    - lege lijst → []
    - lijst met packs → refresh-loop wordt doorlopen
  trend_packs._refresh_fatigue:
    - jobs aanwezig, fingerprint matcht → ratio > 0, warning kan True zijn
    - jobs aanwezig, fingerprint is None voor alle jobs → ratio 0
"""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.db.models import (
    ObservationWindow,
    PackType,
    PerformanceSource,
    Platform,
    TrendPackStatus,
)
from app.integrations.analytics import AnalyticsAdapterError
from app.review.performance import _pull_metrics, ingest_performance_snapshot
from app.review.trend_packs import _refresh_fatigue, list_trend_packs
from app.review.schemas import PerformanceSnapshotIngestRequest


# ---------------------------------------------------------------------------
# Shared fake-DB
# ---------------------------------------------------------------------------

class _ScalarsResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class _FakeDb:
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
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(timezone.utc)


def _make_publication(platform=Platform.instagram, buffer_post_id="buf-1", scheduled_at=None):
    return SimpleNamespace(
        id="pub-1",
        platform=platform,
        buffer_post_id=buffer_post_id,
        scheduled_at=scheduled_at,
    )


# ---------------------------------------------------------------------------
# performance._pull_metrics — per-source paden
# ---------------------------------------------------------------------------

def test_pull_metrics_buffer_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.performance.fetch_buffer_metrics",
        lambda post_id: {"views": 5000, "likes": 300, "comments": 20,
                         "shares": 10, "saves": 8, "follows_lift": 2},
    )
    publication = _make_publication(buffer_post_id="buf-ok")
    metrics, warning = _pull_metrics(PerformanceSource.buffer, publication)
    assert metrics["views"] == 5000
    assert warning is None


def test_pull_metrics_instagram_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.performance.fetch_instagram_metrics",
        lambda post_id: {"views": 2000, "likes": 120, "comments": 8,
                         "shares": 5, "saves": 4, "follows_lift": 1},
    )
    publication = _make_publication(platform=Platform.instagram, buffer_post_id="ig-post-1")
    metrics, warning = _pull_metrics(PerformanceSource.instagram, publication)
    assert metrics["views"] == 2000
    assert warning is None


def test_pull_metrics_tiktok_raises_adapter_error_returns_warning(monkeypatch) -> None:
    """TikTok adapter always raises → foutpad; lege metrics + warning worden teruggegeven."""
    monkeypatch.setattr(
        "app.review.performance.fetch_tiktok_metrics",
        lambda post_id: (_ for _ in ()).throw(
            AnalyticsAdapterError("TikTok analytics adapter not configured yet")
        ),
    )
    publication = _make_publication(platform=Platform.tiktok, buffer_post_id="tt-post-1")
    metrics, warning = _pull_metrics(PerformanceSource.tiktok, publication)
    assert warning is not None
    assert "TikTok" in warning
    for v in metrics.values():
        assert v is None


def test_pull_metrics_buffer_empty_post_id_returns_warning(monkeypatch) -> None:
    """Leeg buffer_post_id → AnalyticsAdapterError → foutpad geactiveerd."""
    publication = _make_publication(buffer_post_id="")
    metrics, warning = _pull_metrics(PerformanceSource.buffer, publication)
    assert warning is not None
    assert metrics["views"] is None


def test_pull_metrics_instagram_empty_post_id_returns_warning(monkeypatch) -> None:
    publication = _make_publication(platform=Platform.instagram, buffer_post_id="")
    metrics, warning = _pull_metrics(PerformanceSource.instagram, publication)
    assert warning is not None
    assert metrics["views"] is None


# ---------------------------------------------------------------------------
# performance.ingest_performance_snapshot — pull-mode
# ---------------------------------------------------------------------------

def test_ingest_performance_snapshot_pull_mode_calls_adapter(monkeypatch) -> None:
    """Pull-mode roept _pull_metrics aan; adapter-warning wordt doorgegeven."""
    from app.review import performance as perf_module

    monkeypatch.setattr(
        perf_module,
        "_pull_metrics",
        lambda source, publication: (
            {"views": 3000, "likes": 200, "comments": 15,
             "shares": 8, "saves": 6, "follows_lift": 3},
            None,
        ),
    )

    publication = _make_publication(platform=Platform.instagram, buffer_post_id="buf-1")
    snapshot_obj = SimpleNamespace(
        id="snap-new",
        publication_job_fk="pub-1",
        source=SimpleNamespace(value="instagram"),
        observation_window=SimpleNamespace(value="24h"),
        normalized_metrics={"view_velocity": 0.3},
        score_components={"formula": "..."},
        performance_score=22.5,
    )
    db = _FakeDb(scalar_values=[publication, snapshot_obj])

    payload = PerformanceSnapshotIngestRequest(
        source=PerformanceSource.instagram,
        observation_window=ObservationWindow.twenty_four_hours,
        mode="pull",
    )

    result = ingest_performance_snapshot(db=db, publication_job_id="pub-1", payload=payload)

    assert result.publication_job_id == "pub-1"
    assert result.adapter_warning is None


def test_ingest_performance_snapshot_pull_mode_with_warning(monkeypatch) -> None:
    """Als de adapter faalt geeft pull-mode een warning terug maar gooit geen exception."""
    from app.review import performance as perf_module

    empty_metrics = {k: None for k in ["views", "likes", "comments", "shares", "saves", "follows_lift"]}
    monkeypatch.setattr(
        perf_module,
        "_pull_metrics",
        lambda source, publication: (empty_metrics, "adapter unavailable"),
    )

    publication = _make_publication(platform=Platform.tiktok, buffer_post_id="tt-ref")
    snapshot_obj = SimpleNamespace(
        id="snap-warn",
        publication_job_fk="pub-1",
        source=SimpleNamespace(value="tiktok"),
        observation_window=SimpleNamespace(value="24h"),
        normalized_metrics={},
        score_components={},
        performance_score=None,
    )
    db = _FakeDb(scalar_values=[publication, snapshot_obj])

    payload = PerformanceSnapshotIngestRequest(
        source=PerformanceSource.tiktok,
        observation_window=ObservationWindow.twenty_four_hours,
        mode="pull",
    )

    result = ingest_performance_snapshot(db=db, publication_job_id="pub-1", payload=payload)

    assert result.adapter_warning == "adapter unavailable"
    assert result.performance_score is None


def test_ingest_performance_snapshot_manual_mode_no_adapter_called(monkeypatch) -> None:
    """Manual-mode mag de adapter nooit aanroepen; metrics komen direct van payload."""
    from app.review import performance as perf_module

    called = []
    monkeypatch.setattr(
        perf_module, "_pull_metrics",
        lambda *a, **kw: called.append(True) or ({}, None),
    )

    publication = _make_publication(platform=Platform.instagram)
    snapshot_obj = SimpleNamespace(
        id="snap-manual",
        publication_job_fk="pub-1",
        source=SimpleNamespace(value="instagram"),
        observation_window=SimpleNamespace(value="24h"),
        normalized_metrics={"view_velocity": 0.5},
        score_components={"formula": "..."},
        performance_score=30.0,
    )
    db = _FakeDb(scalar_values=[publication, snapshot_obj])

    payload = PerformanceSnapshotIngestRequest(
        source=PerformanceSource.instagram,
        observation_window=ObservationWindow.twenty_four_hours,
        mode="manual",
        views=5000,
        likes=300,
        comments=20,
        shares=10,
        saves=8,
        follows_lift=2,
    )

    result = ingest_performance_snapshot(db=db, publication_job_id="pub-1", payload=payload)

    assert called == []
    assert result.adapter_warning is None


def test_ingest_performance_snapshot_not_found_raises() -> None:
    db = _FakeDb(scalar_values=[None])
    payload = PerformanceSnapshotIngestRequest(
        source=PerformanceSource.instagram,
        observation_window=ObservationWindow.twenty_four_hours,
        mode="manual",
    )
    with pytest.raises(ValueError, match="Publication job not found"):
        ingest_performance_snapshot(db=db, publication_job_id="missing", payload=payload)


# ---------------------------------------------------------------------------
# trend_packs.list_trend_packs — met items
# ---------------------------------------------------------------------------

def _make_pack(pack_id: str, version: str = "v1", pack_type=PackType.hook):
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=pack_id,
        pack_type=pack_type,
        name="Test Pack",
        version=version,
        status=SimpleNamespace(value="active"),
        promoted_to_default=False,
        retired_reason=None,
        pack_config=None,
        performance_score=None,
        fatigue_warning=False,
        fatigue_ratio_rolling_30=0.0,
        created_at=ts,
    )


def test_list_trend_packs_empty_returns_empty() -> None:
    db = _FakeDb(scalars_values=[[]])
    result = list_trend_packs(db=db)
    assert result == []


def test_list_trend_packs_with_items_calls_refresh_for_each(monkeypatch) -> None:
    """list_trend_packs moet voor elk pack _refresh_fatigue aanroepen."""
    from app.review import trend_packs as tp_module

    refreshed = []

    def _fake_refresh(db, pack, **kwargs):
        refreshed.append(pack.id)

    monkeypatch.setattr(tp_module, "_refresh_fatigue", _fake_refresh)

    pack_a = _make_pack("pack-a")
    pack_b = _make_pack("pack-b")
    db = _FakeDb(scalars_values=[[pack_a, pack_b]])
    result = list_trend_packs(db=db)

    assert len(result) == 2
    assert set(refreshed) == {"pack-a", "pack-b"}
    assert result[0].trend_pack_id == "pack-a"


def test_list_trend_packs_with_pack_type_filter(monkeypatch) -> None:
    """Filter-pad wordt uitgevoerd zonder fout (statement wordt aangevuld)."""
    from app.review import trend_packs as tp_module

    monkeypatch.setattr(tp_module, "_refresh_fatigue", lambda db, pack, **kw: None)

    pack = _make_pack("pack-c", pack_type=PackType.caption)
    pack.pack_type = PackType.caption
    db = _FakeDb(scalars_values=[[pack]])
    result = list_trend_packs(db=db, pack_type=PackType.caption, status=TrendPackStatus.active)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# trend_packs._refresh_fatigue — met fingerprint-matches
# ---------------------------------------------------------------------------

def test_refresh_fatigue_with_matching_fingerprints_sets_ratio() -> None:
    pack = _make_pack("pack-fat", version="hook-v1", pack_type=PackType.hook)
    pack.pack_type = PackType.hook

    job1 = SimpleNamespace(id="job-1", rendered_clip_fk="clip-1")
    job2 = SimpleNamespace(id="job-2", rendered_clip_fk="clip-2")

    fp_match = SimpleNamespace(
        hook_pattern="hook-v1",
        caption_pack_version=None, font_pack_version=None,
        transition_pack_version=None, animation_pack_version=None,
        edit_route=None,
    )
    fp_no_match = SimpleNamespace(
        hook_pattern="hook-v2",  # different version → no match
        caption_pack_version=None, font_pack_version=None,
        transition_pack_version=None, animation_pack_version=None,
        edit_route=None,
    )

    # scalars_values: [jobs], scalar_values: fp for job1, fp for job2
    db = _FakeDb(
        scalar_values=[fp_match, fp_no_match],
        scalars_values=[[job1, job2]],
    )

    _refresh_fatigue(db, pack)

    # 1 match out of 2 jobs → ratio = 0.5
    assert pack.fatigue_ratio_rolling_30 == pytest.approx(0.5)
    assert pack.fatigue_warning is True  # 0.5 > 0.40 threshold


def test_refresh_fatigue_all_fingerprints_none_gives_zero_ratio() -> None:
    pack = _make_pack("pack-nofp", version="hook-v1", pack_type=PackType.hook)
    pack.pack_type = PackType.hook

    job1 = SimpleNamespace(id="job-1", rendered_clip_fk="clip-1")
    job2 = SimpleNamespace(id="job-2", rendered_clip_fk="clip-2")

    # scalar_values: None for both jobs → no fingerprint found
    db = _FakeDb(
        scalar_values=[None, None],
        scalars_values=[[job1, job2]],
    )

    _refresh_fatigue(db, pack)

    # 0 matches, 2 jobs → ratio = 0.0
    assert pack.fatigue_ratio_rolling_30 == pytest.approx(0.0)
    assert pack.fatigue_warning is False


def test_refresh_fatigue_all_jobs_match_triggers_warning() -> None:
    pack = _make_pack("pack-full", version="cap-v1", pack_type=PackType.caption)
    pack.pack_type = PackType.caption

    jobs = [SimpleNamespace(id=f"job-{i}", rendered_clip_fk=f"clip-{i}") for i in range(5)]
    fingerprints = [
        SimpleNamespace(
            hook_pattern=None,
            caption_pack_version="cap-v1",  # all match
            font_pack_version=None,
            transition_pack_version=None,
            animation_pack_version=None,
            edit_route=None,
        )
        for _ in range(5)
    ]

    db = _FakeDb(scalar_values=fingerprints, scalars_values=[jobs])

    _refresh_fatigue(db, pack)

    assert pack.fatigue_ratio_rolling_30 == pytest.approx(1.0)
    assert pack.fatigue_warning is True
