from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.db.models import (
    DistributionProvider,
    PackType,
    Platform,
    PublishStatus,
    ReviewStatus,
    TrendPackStatus,
)
from app.integrations.buffer_client import BufferApiError
from app.review.publishing import _create_manual_export, schedule_clip_for_distribution, sync_publication_job_status
from app.review.trend_packs import _field_for_pack_type, _refresh_fatigue, create_trend_pack


class _FakeScalarsResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class _FakeDb:
    def __init__(self, scalar_values=None, scalars_values=None):
        self.scalar_values = list(scalar_values or [])
        self.scalars_values = list(scalars_values or [])
        self.added = []

    def scalar(self, _statement):
        if self.scalar_values:
            return self.scalar_values.pop(0)
        return None

    def scalars(self, _statement):
        items = self.scalars_values.pop(0) if self.scalars_values else []
        return _FakeScalarsResult(items)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        return None

    def refresh(self, obj):
        if not getattr(obj, "id", None):
            obj.id = "generated-id"


class _FakePublicationJob:
    def __init__(self, **kwargs):
        self.id = kwargs.pop("id", "pub-1")
        self.buffer_post_id = kwargs.get("buffer_post_id")
        self.external_post_ref = kwargs.get("external_post_ref")
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_create_manual_export_writes_expected_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.publishing.get_settings",
        lambda: SimpleNamespace(manual_publish_export_dir=str(tmp_path)),
    )

    publication = SimpleNamespace(
        id="pub-100",
        platform=Platform.instagram,
        scheduled_at=datetime(2026, 3, 18, 20, 0, tzinfo=timezone.utc),
        distribution_provider=DistributionProvider.manual,
    )
    clip = SimpleNamespace(id="clip-100", render_path="render/output.mp4")

    export_path = _create_manual_export(publication=publication, clip=clip, caption="hello world #test")

    assert Path(export_path).exists()
    content = Path(export_path).read_text(encoding="utf-8")
    assert '"publication_job_id": "pub-100"' in content
    assert '"platform": "instagram"' in content
    assert '"title": "hello world"' in content
    assert '"description": "hello world"' in content
    assert '"hashtags": [' in content



def test_schedule_clip_for_distribution_manual_success(tmp_path, monkeypatch) -> None:
    clip = SimpleNamespace(id="clip-1", review_status=ReviewStatus.approved, render_path="render/out.mp4", last_error="old")
    db = _FakeDb(scalar_values=[clip])

    monkeypatch.setattr("app.review.publishing.assert_clip_compliant", lambda db, rendered_clip_id: None)
    monkeypatch.setattr("app.review.publishing.PublicationJob", _FakePublicationJob)
    monkeypatch.setattr(
        "app.review.publishing.get_settings",
        lambda: SimpleNamespace(publish_provider="manual", manual_publish_export_dir=str(tmp_path)),
    )

    publication = schedule_clip_for_distribution(
        db=db,
        rendered_clip_id="clip-1",
        platform=Platform.instagram,
        scheduled_at=datetime(2026, 3, 18, 20, 0, tzinfo=timezone.utc),
        caption="caption",
    )

    assert publication.distribution_provider == DistributionProvider.manual
    assert publication.publish_status == PublishStatus.scheduled
    assert publication.external_post_ref is not None
    assert Path(publication.external_post_ref).exists()
    assert clip.last_error is None


def test_schedule_clip_for_distribution_buffer_success(monkeypatch) -> None:
    clip = SimpleNamespace(id="clip-1", review_status=ReviewStatus.approved, render_path="render/out.mp4", last_error=None)
    db = _FakeDb(scalar_values=[clip])
    fake_publication = SimpleNamespace(buffer_post_id="buf-1", distribution_provider=None, external_post_ref=None)

    monkeypatch.setattr("app.review.publishing.assert_clip_compliant", lambda db, rendered_clip_id: None)
    monkeypatch.setattr(
        "app.review.publishing.get_settings",
        lambda: SimpleNamespace(publish_provider="buffer"),
    )
    monkeypatch.setattr("app.review.publishing.schedule_clip_via_buffer", lambda **kwargs: fake_publication)

    publication = schedule_clip_for_distribution(
        db=db,
        rendered_clip_id="clip-1",
        platform=Platform.tiktok,
        scheduled_at=datetime(2026, 3, 18, 20, 0, tzinfo=timezone.utc),
        caption="caption",
    )

    assert publication.distribution_provider == DistributionProvider.buffer
    assert publication.external_post_ref == "buf-1"


def test_schedule_clip_for_distribution_rejects_invalid_clip_states(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.publishing.get_settings",
        lambda: SimpleNamespace(publish_provider="manual", manual_publish_export_dir="generated/publish_queue"),
    )

    with pytest.raises(ValueError, match="Rendered clip not found"):
        schedule_clip_for_distribution(
            db=_FakeDb(scalar_values=[None]),
            rendered_clip_id="missing",
            platform=Platform.instagram,
            scheduled_at=datetime(2026, 3, 18, 20, 0, tzinfo=timezone.utc),
            caption="caption",
        )

    with pytest.raises(ValueError, match="Only approved clips"):
        schedule_clip_for_distribution(
            db=_FakeDb(scalar_values=[SimpleNamespace(id="clip", review_status=ReviewStatus.revise, render_path="a.mp4")]),
            rendered_clip_id="clip",
            platform=Platform.instagram,
            scheduled_at=datetime(2026, 3, 18, 20, 0, tzinfo=timezone.utc),
            caption="caption",
        )

    with pytest.raises(ValueError, match="no render path"):
        schedule_clip_for_distribution(
            db=_FakeDb(scalar_values=[SimpleNamespace(id="clip", review_status=ReviewStatus.approved, render_path=None)]),
            rendered_clip_id="clip",
            platform=Platform.instagram,
            scheduled_at=datetime(2026, 3, 18, 20, 0, tzinfo=timezone.utc),
            caption="caption",
        )


def test_sync_publication_job_status_returns_manual_without_changes() -> None:
    publication = SimpleNamespace(distribution_provider=DistributionProvider.manual)
    db = _FakeDb(scalar_values=[publication])

    result = sync_publication_job_status(db=db, publication_job_id="pub-1")

    assert result is publication


def test_sync_publication_job_status_buffer_success(monkeypatch) -> None:
    publication = SimpleNamespace(
        id="pub-1",
        distribution_provider=DistributionProvider.buffer,
        buffer_post_id="buf-1",
        publish_status=PublishStatus.pending,
        rendered_clip_fk="clip-1",
    )
    db = _FakeDb(scalar_values=[publication])

    class _FakeBufferClient:
        def __init__(self, access_token: str, base_url: str):
            self.access_token = access_token
            self.base_url = base_url

        def fetch_update_status(self, post_id: str) -> str:
            assert post_id == "buf-1"
            return "published"

    monkeypatch.setattr("app.review.publishing.BufferClient", _FakeBufferClient)
    monkeypatch.setattr(
        "app.review.publishing.get_settings",
        lambda: SimpleNamespace(buffer_access_token="token", buffer_api_base_url="https://api.buffer.test"),
    )

    result = sync_publication_job_status(db=db, publication_job_id="pub-1")

    assert result.publish_status == PublishStatus.published


def test_sync_publication_job_status_buffer_error_marks_failed(monkeypatch) -> None:
    publication = SimpleNamespace(
        id="pub-2",
        distribution_provider=DistributionProvider.buffer,
        buffer_post_id="buf-2",
        publish_status=PublishStatus.pending,
        rendered_clip_fk="clip-2",
    )
    clip = SimpleNamespace(last_error=None)
    db = _FakeDb(scalar_values=[publication, clip])

    class _FailingBufferClient:
        def __init__(self, access_token: str, base_url: str):
            self.access_token = access_token
            self.base_url = base_url

        def fetch_update_status(self, post_id: str) -> str:
            raise BufferApiError("boom")

    monkeypatch.setattr("app.review.publishing.BufferClient", _FailingBufferClient)
    monkeypatch.setattr(
        "app.review.publishing.get_settings",
        lambda: SimpleNamespace(buffer_access_token="token", buffer_api_base_url="https://api.buffer.test"),
    )

    result = sync_publication_job_status(db=db, publication_job_id="pub-2")

    assert result.publish_status == PublishStatus.failed
    assert "Publish status sync failed" in clip.last_error


def test_field_for_pack_type_mapping_is_complete() -> None:
    assert _field_for_pack_type(PackType.hook) == "hook_pattern"
    assert _field_for_pack_type(PackType.caption) == "caption_pack_version"
    assert _field_for_pack_type(PackType.font) == "font_pack_version"
    assert _field_for_pack_type(PackType.transition) == "transition_pack_version"
    assert _field_for_pack_type(PackType.animation) == "animation_pack_version"
    assert _field_for_pack_type(PackType.series_format) == "edit_route"


def test_refresh_fatigue_no_jobs_sets_zero_ratio() -> None:
    pack = SimpleNamespace(pack_type=PackType.caption, version="cap-v1", fatigue_ratio_rolling_30=1.0, fatigue_warning=True)
    db = _FakeDb(scalars_values=[[]])

    _refresh_fatigue(db=db, pack=pack)

    assert pack.fatigue_ratio_rolling_30 == 0.0
    assert pack.fatigue_warning is False


def test_refresh_fatigue_sets_warning_when_ratio_above_threshold() -> None:
    jobs = [SimpleNamespace(rendered_clip_fk="clip-1"), SimpleNamespace(rendered_clip_fk="clip-2"), SimpleNamespace(rendered_clip_fk="clip-3")]
    fingerprints = [
        SimpleNamespace(caption_pack_version="cap-v2"),
        SimpleNamespace(caption_pack_version="cap-v2"),
        SimpleNamespace(caption_pack_version="other"),
    ]
    pack = SimpleNamespace(pack_type=PackType.caption, version="cap-v2", fatigue_ratio_rolling_30=0.0, fatigue_warning=False)
    db = _FakeDb(scalars_values=[jobs], scalar_values=fingerprints)

    _refresh_fatigue(db=db, pack=pack, fatigue_threshold=0.4)

    assert pack.fatigue_ratio_rolling_30 == 0.6667
    assert pack.fatigue_warning is True


def test_create_trend_pack_duplicate_raises() -> None:
    existing = SimpleNamespace()
    db = _FakeDb(scalar_values=[existing])

    with pytest.raises(ValueError, match="Trend pack already exists"):
        create_trend_pack(
            db=db,
            pack_type=PackType.caption,
            name="Caption 1",
            version="cap-v1",
            status=TrendPackStatus.experiment,
            pack_config={"style": "neon"},
        )
