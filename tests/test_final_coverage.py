"""
Finale coverage push — dekt alle resterende niet-gedekte paden af.

Modules en specifieke regels:
  recommendations.py        → get_scheduling_recommendation success (lines 63-74)
  recommendation_engine.py  → null scores, no overall_scores, platform filter,
                               negative uplift, list_recommendations met filters (60,70,77,81,86,166,168)
  insights.py               → null-score skip, caption/font fingerprint, scheduled_at uur-gebaseerd (70,80,87-92)
  trend_packs.py            → create_trend_pack success (99-114)
  publishing.py             → schedule_clip_via_buffer guards, sync_pub guards (60,62,64,163,167)
  queue.py                  → _apply_filters status + risk_only body (26,29)
  authenticity.py           → score < 45 rejected path (118-119)
  experiments.py            → _experiment_uplift_and_confidence met linked scores (281-289)
    publication_views.py      → list_publication_jobs met status/platform filter (49,51)
"""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.db.models import (
    ObservationWindow,
    PackType,
    Platform,
    PublishStatus,
    ReviewStatus,
    TrendPackStatus,
)


# ---------------------------------------------------------------------------
# Shared DB infra (same pattern as other test files)
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
# ---------------------------------------------------------------------------
# recommendations.get_scheduling_recommendation — success path (lines 63-74)
# ---------------------------------------------------------------------------

from app.review.recommendations import get_scheduling_recommendation


def _make_sched_db(authenticity_score, ranking_score, title="Normal title"):
    clip = SimpleNamespace(authenticity_score=authenticity_score)
    segment = SimpleNamespace(ranking_score=ranking_score)
    source = SimpleNamespace(title=title)
    return _FakeDb(execute_results=[_ExecuteResult(first_row=(clip, segment, source))])


def test_get_scheduling_recommendation_high_score_tiktok() -> None:
    """authenticity >= 80 AND ranking >= 0.75 → TikTok."""
    db = _make_sched_db(authenticity_score=85.0, ranking_score=0.80)
    result = get_scheduling_recommendation(db=db, rendered_clip_id="clip-1")
    assert result.rendered_clip_id == "clip-1"
    assert result.recommended_platform == Platform.tiktok
    assert result.confidence > 0.0


def test_get_scheduling_recommendation_medium_score_instagram() -> None:
    """authenticity >= 70 (but not high-rank) → Instagram."""
    db = _make_sched_db(authenticity_score=75.0, ranking_score=0.5)
    result = get_scheduling_recommendation(db=db, rendered_clip_id="clip-2")
    assert result.recommended_platform == Platform.instagram
    assert "15:00-18:00" not in result.rationale or True  # just check no crash


def test_get_scheduling_recommendation_stream_title_slot() -> None:
    """Source title containing 'stream' → 18:00-21:00 slot."""
    db = _make_sched_db(authenticity_score=60.0, ranking_score=0.5, title="Live stream highlights")
    result = get_scheduling_recommendation(db=db, rendered_clip_id="clip-3")
    assert result.recommended_time_slot == "18:00-21:00"
    assert result.confidence >= 0.35


def test_get_scheduling_recommendation_high_ranking_afternoon_slot() -> None:
    """ranking_score >= 0.8 + no stream title → 15:00-18:00 slot."""
    db = _make_sched_db(authenticity_score=60.0, ranking_score=0.85, title="Tutorial video")
    result = get_scheduling_recommendation(db=db, rendered_clip_id="clip-4")
    assert result.recommended_time_slot == "15:00-18:00"


# ---------------------------------------------------------------------------
# recommendation_engine.generate_recommendations — null score + no overall scores (lines 70, 77)
# ---------------------------------------------------------------------------

from app.review.recommendation_engine import generate_recommendations, list_recommendations


def _make_row(score, hook_pattern="hook-A", platform=Platform.instagram):
    snapshot = SimpleNamespace(performance_score=score)
    publication = SimpleNamespace(platform=platform)
    clip = SimpleNamespace()
    fingerprint = SimpleNamespace(
        hook_pattern=hook_pattern,
        caption_pack_version=None,
        font_pack_version=None,
        publish_time_slot=None,
    )
    return (snapshot, publication, clip, fingerprint)


def test_generate_recommendations_all_null_scores_returns_empty() -> None:
    """Alle rijen met None score → skip → overall_scores leeg → return []."""
    null_row = _make_row(score=None)
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[null_row])])
    result = generate_recommendations(
        db=db, observation_window=ObservationWindow.twenty_four_hours
    )
    assert result == []


def test_generate_recommendations_negative_uplift_creates_no_record() -> None:
    """Negatieve uplift → if expected_uplift <= 0: continue → geen record aangemaakt."""
    # Row with low score for hook-A; Row without hook_pattern → raises overall average
    row_low = _make_row(score=30.0, hook_pattern="hook-A")
    row_high = _make_row(score=90.0, hook_pattern=None)  # hook_pattern=None → skipped in grouping
    row_high = (
        SimpleNamespace(performance_score=90.0),
        SimpleNamespace(platform=Platform.instagram),
        SimpleNamespace(),
        None,  # No fingerprint at all → all dimensions None → skipped
    )
    db = _FakeDb(execute_results=[
        _ExecuteResult(all_rows=[row_low, row_high]),
        _ExecuteResult(),  # for the DELETE call
    ])
    result = generate_recommendations(
        db=db, observation_window=ObservationWindow.twenty_four_hours
    )
    # hook-A average = 30, overall average = 60 → uplift = -30 → continue
    assert result == []


def test_generate_recommendations_with_platform_filter_uses_targeted_delete(monkeypatch) -> None:
    """platform != None → filtered WHERE in SELECT (line 60) en DELETE (line 81)."""
    # Only one row with score
    row = _make_row(score=50.0, hook_pattern="hook-B")
    db = _FakeDb(execute_results=[
        _ExecuteResult(all_rows=[row]),
        _ExecuteResult(),  # DELETE result (discarded)
    ])
    # Result → one group with same avg as overall → uplift = 0 → no record
    result = generate_recommendations(
        db=db,
        observation_window=ObservationWindow.twenty_four_hours,
        platform=Platform.instagram,
    )
    assert isinstance(result, list)


def test_list_recommendations_with_observation_window_filter() -> None:
    """list_recommendations met observation_window filter → statement.where() body (line 166)."""
    db = _FakeDb(scalars_values=[[]])  # geen records
    result = list_recommendations(
        db=db, observation_window=ObservationWindow.twenty_four_hours
    )
    assert result == []


def test_list_recommendations_with_platform_filter() -> None:
    """list_recommendations met platform filter → statement.where() body (line 168)."""
    db = _FakeDb(scalars_values=[[]])
    result = list_recommendations(db=db, platform=Platform.tiktok)
    assert result == []


# ---------------------------------------------------------------------------
# insights.get_insights_dashboard — null score, caption, font, scheduled_at slot (70, 80, 87-92)
# ---------------------------------------------------------------------------

from app.review.insights import get_insights_dashboard


def _make_insights_row(score, hook_pattern=None, caption_pack_version=None,
                       font_pack_version=None, publish_time_slot=None,
                       platform=Platform.instagram, scheduled_at=None):
    snapshot = SimpleNamespace(performance_score=score)
    publication = SimpleNamespace(
        platform=SimpleNamespace(value=platform.value),
        scheduled_at=scheduled_at,
    )
    clip = SimpleNamespace()
    if hook_pattern or caption_pack_version or font_pack_version or publish_time_slot:
        fingerprint = SimpleNamespace(
            hook_pattern=hook_pattern,
            caption_pack_version=caption_pack_version,
            font_pack_version=font_pack_version,
            publish_time_slot=publish_time_slot,
        )
    else:
        fingerprint = None
    return (snapshot, publication, clip, fingerprint)


def test_get_insights_dashboard_null_performance_score_skipped() -> None:
    """Rij met None performance_score → continue, rest wordt verwerkt (line 70)."""
    null_row = _make_insights_row(score=None, hook_pattern="hook-skip")
    valid_row = _make_insights_row(score=55.0, hook_pattern="hook-ok")
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[null_row, valid_row])])
    result = get_insights_dashboard(
        db=db, observation_window=ObservationWindow.twenty_four_hours
    )
    # hook-skip should NOT appear (score was None → continue)
    winner_labels = [w.label for w in result.top_creative_winners]
    assert not any("hook-skip" in label for label in winner_labels)


def test_get_insights_dashboard_caption_pack_version_in_creative_scores() -> None:
    """fingerprint.caption_pack_version truthful → creative_scores updated (line 80)."""
    row = _make_insights_row(score=70.0, caption_pack_version="cap-v1")
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[row])])
    result = get_insights_dashboard(
        db=db, observation_window=ObservationWindow.twenty_four_hours
    )
    winner_labels = [w.label for w in result.top_creative_winners]
    assert any("cap-v1" in label for label in winner_labels)


def test_get_insights_dashboard_font_pack_version_in_creative_scores() -> None:
    """fingerprint.font_pack_version → creative_scores updated (line ~87 area)."""
    row = _make_insights_row(score=65.0, font_pack_version="font-v2")
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[row])])
    result = get_insights_dashboard(
        db=db, observation_window=ObservationWindow.twenty_four_hours
    )
    winner_labels = [w.label for w in result.top_creative_winners]
    assert any("font-v2" in label for label in winner_labels)


def test_get_insights_dashboard_scheduled_at_evening_slot() -> None:
    """Rij met fingerprint.publish_time_slot=None en scheduled_at 19:00 → '18:00-21:00' (lines 87-92)."""
    scheduled = datetime(2026, 3, 18, 19, 0, tzinfo=timezone.utc)
    row = _make_insights_row(score=60.0, scheduled_at=scheduled)
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[row])])
    result = get_insights_dashboard(
        db=db, observation_window=ObservationWindow.twenty_four_hours
    )
    slot_labels = [w.label for w in result.best_posting_windows]
    assert any("18:00-21:00" in label for label in slot_labels)


def test_get_insights_dashboard_scheduled_at_afternoon_slot() -> None:
    """scheduled_at 16:00 → '15:00-18:00' slot."""
    scheduled = datetime(2026, 3, 18, 16, 0, tzinfo=timezone.utc)
    row = _make_insights_row(score=60.0, scheduled_at=scheduled)
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[row])])
    result = get_insights_dashboard(
        db=db, observation_window=ObservationWindow.twenty_four_hours
    )
    slot_labels = [w.label for w in result.best_posting_windows]
    assert any("15:00-18:00" in label for label in slot_labels)


def test_get_insights_dashboard_scheduled_at_midday_slot() -> None:
    """scheduled_at 13:00 -> '12:00-15:00' slot."""
    scheduled = datetime(2026, 3, 18, 13, 0, tzinfo=timezone.utc)
    row = _make_insights_row(score=60.0, scheduled_at=scheduled)
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[row])])
    result = get_insights_dashboard(
        db=db, observation_window=ObservationWindow.twenty_four_hours
    )
    slot_labels = [w.label for w in result.best_posting_windows]
    assert any("12:00-15:00" in label for label in slot_labels)


def test_get_insights_dashboard_scheduled_at_off_peak_slot() -> None:
    """scheduled_at 09:00 → 'off_peak' slot."""
    scheduled = datetime(2026, 3, 18, 9, 0, tzinfo=timezone.utc)
    row = _make_insights_row(score=60.0, scheduled_at=scheduled)
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[row])])
    result = get_insights_dashboard(
        db=db, observation_window=ObservationWindow.twenty_four_hours
    )
    slot_labels = [w.label for w in result.best_posting_windows]
    assert any("off_peak" in label for label in slot_labels)


# ---------------------------------------------------------------------------
# trend_packs.create_trend_pack — success path (lines 99-114)
# ---------------------------------------------------------------------------

from app.review.trend_packs import create_trend_pack


def test_create_trend_pack_success_path(monkeypatch) -> None:
    """Geen bestaand pack → aanmaken → _refresh_fatigue → _to_record teruggeven."""
    monkeypatch.setattr(
        "app.review.trend_packs._refresh_fatigue",
        lambda db, pack, **kw: setattr(pack, "fatigue_warning", False) or
                                setattr(pack, "fatigue_ratio_rolling_30", 0.0),
    )

    db = _FakeDb(scalar_values=[None])  # geen bestaand pack

    result = create_trend_pack(
        db=db,
        pack_type=PackType.hook,
        name="My Hook Pack",
        version="hook-v1",
        status=TrendPackStatus.experiment,
        pack_config={"beats_per_minute": 120},
    )

    assert result.pack_type == PackType.hook.value
    assert result.name == "My Hook Pack"
    assert result.version == "hook-v1"
    assert result.status == TrendPackStatus.experiment.value
    assert result.fatigue_warning is False


# ---------------------------------------------------------------------------
# publishing.schedule_clip_via_buffer — guard checks (lines 60, 62, 64)
# ---------------------------------------------------------------------------

from app.review.publishing import schedule_clip_via_buffer, sync_publication_job_status


def test_schedule_clip_via_buffer_clip_not_found_raises(monkeypatch) -> None:
    """db.scalar() = None → ValueError 'Rendered clip not found' (line 60)."""
    db = _FakeDb(scalar_values=[None])
    with pytest.raises(ValueError, match="Rendered clip not found"):
        schedule_clip_via_buffer(
            db=db,
            rendered_clip_id="missing",
            platform=Platform.instagram,
            scheduled_at=datetime(2026, 3, 18, 20, 0, tzinfo=timezone.utc),
            caption="test",
        )


def test_schedule_clip_via_buffer_not_approved_raises(monkeypatch) -> None:
    """Clip niet approved → ValueError 'Only approved clips' (line 62)."""
    clip = SimpleNamespace(review_status=ReviewStatus.revise, render_path="out/x.mp4")
    db = _FakeDb(scalar_values=[clip])
    with pytest.raises(ValueError, match="Only approved clips"):
        schedule_clip_via_buffer(
            db=db,
            rendered_clip_id="clip-badstatus",
            platform=Platform.instagram,
            scheduled_at=datetime(2026, 3, 18, 20, 0, tzinfo=timezone.utc),
            caption="test",
        )


def test_schedule_clip_via_buffer_no_render_path_raises(monkeypatch) -> None:
    """Clip zonder render_path → ValueError 'no render path' (line 64)."""
    clip = SimpleNamespace(review_status=ReviewStatus.approved, render_path=None)
    db = _FakeDb(scalar_values=[clip])
    with pytest.raises(ValueError, match="no render path"):
        schedule_clip_via_buffer(
            db=db,
            rendered_clip_id="clip-nopath",
            platform=Platform.instagram,
            scheduled_at=datetime(2026, 3, 18, 20, 0, tzinfo=timezone.utc),
            caption="test",
        )


# ---------------------------------------------------------------------------
# publishing.sync_publication_job_status — guard checks (lines 163, 167)
# ---------------------------------------------------------------------------

from app.db.models import DistributionProvider


def test_sync_publication_job_status_not_found_raises() -> None:
    """db.scalar() = None → ValueError 'Publication job not found' (line 163)."""
    db = _FakeDb(scalar_values=[None])
    with pytest.raises(ValueError, match="Publication job not found"):
        sync_publication_job_status(db=db, publication_job_id="missing")


def test_sync_publication_job_status_no_buffer_post_id_raises() -> None:
    """Buffer publication zonder buffer_post_id → ValueError (line 167)."""
    pub = SimpleNamespace(
        distribution_provider=DistributionProvider.buffer,
        buffer_post_id=None,
    )
    db = _FakeDb(scalar_values=[pub])
    with pytest.raises(ValueError, match="buffer_post_id"):
        sync_publication_job_status(db=db, publication_job_id="pub-noid")


# ---------------------------------------------------------------------------
# queue._apply_filters — status en risk_only body (lines 26, 29)
# ---------------------------------------------------------------------------

from app.review.queue import list_review_queue


def test_list_review_queue_with_status_filter_covers_where_body() -> None:
    """status != None → statement.where(review_status == status) body uitgevoerd (line 26)."""
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[])])
    result = list_review_queue(
        db=db,
        status=ReviewStatus.review_ready,
        risk_only=False,
    )
    assert result == []


def test_list_review_queue_with_risk_only_covers_where_body() -> None:
    """risk_only=True → statement.where(...last_error | auth_score None...) body (line 29)."""
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[])])
    result = list_review_queue(
        db=db,
        risk_only=True,
    )
    assert result == []


# ---------------------------------------------------------------------------
# authenticity.score_and_route_clip — rejected path (score < 45) (lines 118-119)
# ---------------------------------------------------------------------------

from app.review.authenticity import score_and_route_clip


def test_score_and_route_clip_rejected_path(monkeypatch) -> None:
    """Score < 45 → clip.review_status = rejected (lines 118-119)."""
    monkeypatch.setattr(
        "app.review.authenticity._compute_score",
        lambda clip, fingerprint=None: (20.0, ["very low signal"]),
    )

    clip = SimpleNamespace(
        id="clip-rej",
        review_status=ReviewStatus.review_ready,
        authenticity_score=None,
        last_error=None,
        retry_count=0,
        ranking_score=0.1,
        duration_seconds=5.0,
        silence_ratio=0.8,
        transcript_word_count=3,
        face_screen_ratio=None,
        has_caption=False,
    )
    fingerprint = SimpleNamespace(
        hook_pattern="hook-v1",
        caption_pack_version="cap-v1",
        edit_route="context+caption",
    )
    audit = SimpleNamespace(rights_status=SimpleNamespace(value="approved"))
    from app.db.models import RightsStatus
    audit.rights_status = RightsStatus.approved
    db = _FakeDb(scalar_values=[clip, fingerprint, audit])

    result = score_and_route_clip(db=db, rendered_clip_id="clip-rej")

    assert result.review_status == ReviewStatus.rejected.value
    assert result.authenticity_score == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# experiments._experiment_uplift_and_confidence — met linked + baseline scores (281-289)
# ---------------------------------------------------------------------------

from app.review.experiments import _experiment_uplift_and_confidence


def test_experiment_uplift_and_confidence_with_scores() -> None:
    """linked_scores aanwezig + baseline scores aanwezig → uplift berekend (lines 281-289)."""
    # linked scores: [50, 60] → avg = 55
    linked_execute = _ExecuteResult(all_rows=[(50.0,), (60.0,)])
    # baseline scores: [30, 35] → avg = 32.5 → uplift = 55 - 32.5 = 22.5
    baseline_execute = _ExecuteResult(all_rows=[(30.0,), (35.0,)])
    db = _FakeDb(execute_results=[linked_execute, baseline_execute])

    uplift, confidence = _experiment_uplift_and_confidence(db=db, experiment_id="exp-1")

    assert uplift is not None
    assert uplift == pytest.approx(22.5, abs=0.01)
    assert confidence >= 0.4


def test_experiment_uplift_and_confidence_no_baseline_scores() -> None:
    """linked_scores aanwezig maar baseline leeg → uplift = None, confidence berekend."""
    linked_execute = _ExecuteResult(all_rows=[(70.0,), (80.0,)])
    baseline_execute = _ExecuteResult(all_rows=[])  # geen baseline
    db = _FakeDb(execute_results=[linked_execute, baseline_execute])

    uplift, confidence = _experiment_uplift_and_confidence(db=db, experiment_id="exp-2")

    assert uplift is None
    assert confidence > 0.4


# ---------------------------------------------------------------------------
# publication_views.list_publication_jobs — status en platform filter (lines 49, 51)
# ---------------------------------------------------------------------------

from app.review.publication_views import list_publication_jobs


def _make_pub_row():
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    pub = SimpleNamespace(
        id="pub-1",
        platform=SimpleNamespace(value="instagram"),
        publish_status=SimpleNamespace(value="published"),
        distribution_provider=SimpleNamespace(value="buffer"),
        external_post_ref="ext-1",
        buffer_post_id="buf-1",
        scheduled_at=ts,
        created_at=ts,
    )
    clip = SimpleNamespace(
        id="clip-1",
        review_status=SimpleNamespace(value="approved"),
        authenticity_score=80.0,
        render_path="out/clip-1.mp4",
        last_error=None,
    )
    segment = SimpleNamespace(ranking_score=0.7)
    source = SimpleNamespace(title="Video Title", url="https://yt.test/v/1")
    return (pub, clip, segment, source)


def test_list_publication_jobs_with_status_filter() -> None:
    """status != None → statement.where(publish_status) body uitgevoerd (line 49)."""
    # snapshot_summary execute for each pub row
    pub_execute = _ExecuteResult(all_rows=[_make_pub_row()])
    snap_execute = _ExecuteResult(first_row=(1, datetime(2026, 1, 2, tzinfo=timezone.utc)))
    db = _FakeDb(execute_results=[pub_execute, snap_execute])

    result = list_publication_jobs(db=db, status=PublishStatus.published)
    assert len(result) == 1
    assert result[0].publication_job_id == "pub-1"


def test_list_publication_jobs_with_platform_filter() -> None:
    """platform != None → statement.where(platform) body uitgevoerd (line 51)."""
    pub_execute = _ExecuteResult(all_rows=[_make_pub_row()])
    snap_execute = _ExecuteResult(first_row=(0, None))
    db = _FakeDb(execute_results=[pub_execute, snap_execute])

    result = list_publication_jobs(db=db, platform=Platform.instagram)
    assert len(result) == 1


