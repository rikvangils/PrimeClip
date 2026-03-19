from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.db.models import DistributionProvider, Platform, PublishStatus, ReviewStatus
from app.integrations.tiktok_client import TikTokApiError, TikTokClient
from app.integrations.tiktok_oauth import TikTokOAuthError
from app.review.publishing import schedule_clip_for_distribution, schedule_clip_via_tiktok, sync_publication_job_status


class _FakeDb:
    def __init__(self, scalar_values=None):
        self.scalar_values = list(scalar_values or [])
        self.added = []

    def scalar(self, _statement):
        if self.scalar_values:
            return self.scalar_values.pop(0)
        return None

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


def test_tiktok_client_raises_on_missing_access_token() -> None:
    with pytest.raises(TikTokApiError, match="Missing TikTok access token"):
        TikTokClient(access_token="")


def test_tiktok_client_schedule_post_success(tmp_path: Path) -> None:
    clip_path = tmp_path / "clip.mp4"
    clip_path.write_bytes(b"1234567890")

    init_response = MagicMock()
    init_response.status_code = 200
    init_response.json.return_value = {
        "data": {
            "publish_id": "v_inbox_file~v2.abc123",
            "upload_url": "https://open-upload.tiktokapis.com/video/?upload_id=1&upload_token=abc",
        },
        "error": {"code": "ok", "message": ""},
    }

    upload_response = MagicMock()
    upload_response.status_code = 200
    upload_response.text = ""

    with patch("app.integrations.tiktok_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = init_response
        mock_ctx.put.return_value = upload_response
        MockClient.return_value = mock_ctx

        publish_id, status = TikTokClient(access_token="tt-token").schedule_post(str(clip_path))

    assert publish_id == "v_inbox_file~v2.abc123"
    assert status == "scheduled"


def test_tiktok_client_schedule_post_missing_file_raises() -> None:
    with pytest.raises(TikTokApiError, match="Render file not found"):
        TikTokClient(access_token="tt-token").schedule_post("missing.mp4")


def test_tiktok_client_initialize_upload_validates_video_size() -> None:
    with pytest.raises(TikTokApiError, match="greater than zero"):
        TikTokClient(access_token="tt-token").initialize_file_upload(video_size=0)


def test_tiktok_client_initialize_upload_raises_on_http_error() -> None:
    response = MagicMock()
    response.status_code = 401
    response.text = "invalid token"

    with patch("app.integrations.tiktok_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = response
        MockClient.return_value = mock_ctx

        with pytest.raises(TikTokApiError, match="init upload failed"):
            TikTokClient(access_token="tt-token").initialize_file_upload(video_size=1024)


def test_tiktok_client_initialize_upload_raises_on_non_dict_payload() -> None:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = []

    with patch("app.integrations.tiktok_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = response
        MockClient.return_value = mock_ctx

        with pytest.raises(TikTokApiError, match="Unexpected TikTok init payload"):
            TikTokClient(access_token="tt-token").initialize_file_upload(video_size=1024)


def test_tiktok_client_initialize_upload_raises_on_missing_fields() -> None:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"data": {}, "error": {"code": "ok", "message": ""}}

    with patch("app.integrations.tiktok_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = response
        MockClient.return_value = mock_ctx

        with pytest.raises(TikTokApiError, match="missing publish_id or upload_url"):
            TikTokClient(access_token="tt-token").initialize_file_upload(video_size=1024)


def test_tiktok_client_fetch_publish_status_success() -> None:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "data": {"status": "PUBLISH_COMPLETE"},
        "error": {"code": "ok", "message": ""},
    }

    with patch("app.integrations.tiktok_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = response
        MockClient.return_value = mock_ctx

        status = TikTokClient(access_token="tt-token").fetch_publish_status("v_inbox_file~v2.abc123")

    assert status == "PUBLISH_COMPLETE"


def test_tiktok_client_upload_video_file_missing_upload_url_raises(tmp_path: Path) -> None:
    clip_path = tmp_path / "clip.mp4"
    clip_path.write_bytes(b"abc")

    with pytest.raises(TikTokApiError, match="Missing TikTok upload URL"):
        TikTokClient(access_token="tt-token").upload_video_file(upload_url="", video_file_path=str(clip_path))


def test_tiktok_client_upload_video_file_missing_file_raises() -> None:
    with pytest.raises(TikTokApiError, match="Render file not found"):
        TikTokClient(access_token="tt-token").upload_video_file(
            upload_url="https://open-upload.tiktokapis.com/video/?upload_id=1",
            video_file_path="missing.mp4",
        )


def test_tiktok_client_upload_video_file_empty_file_raises(tmp_path: Path) -> None:
    clip_path = tmp_path / "empty.mp4"
    clip_path.write_bytes(b"")

    with pytest.raises(TikTokApiError, match="empty video file"):
        TikTokClient(access_token="tt-token").upload_video_file(
            upload_url="https://open-upload.tiktokapis.com/video/?upload_id=1",
            video_file_path=str(clip_path),
        )


def test_tiktok_client_upload_video_file_http_error_raises(tmp_path: Path) -> None:
    clip_path = tmp_path / "clip.mp4"
    clip_path.write_bytes(b"abc")

    response = MagicMock()
    response.status_code = 500
    response.text = "upload failed"

    with patch("app.integrations.tiktok_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.put.return_value = response
        MockClient.return_value = mock_ctx

        with pytest.raises(TikTokApiError, match="video upload failed"):
            TikTokClient(access_token="tt-token").upload_video_file(
                upload_url="https://open-upload.tiktokapis.com/video/?upload_id=1",
                video_file_path=str(clip_path),
            )


def test_tiktok_client_raises_on_init_error_code() -> None:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "data": {},
        "error": {"code": "scope_not_authorized", "message": "video.upload missing"},
    }

    with patch("app.integrations.tiktok_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = response
        MockClient.return_value = mock_ctx

        with pytest.raises(TikTokApiError, match="video.upload missing"):
            TikTokClient(access_token="tt-token").initialize_file_upload(video_size=1024)


def test_tiktok_client_fetch_publish_status_missing_id_raises() -> None:
    with pytest.raises(TikTokApiError, match="Missing TikTok publish id"):
        TikTokClient(access_token="tt-token").fetch_publish_status("")


def test_tiktok_client_fetch_publish_status_raises_on_http_error() -> None:
    response = MagicMock()
    response.status_code = 403
    response.text = "forbidden"

    with patch("app.integrations.tiktok_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = response
        MockClient.return_value = mock_ctx

        with pytest.raises(TikTokApiError, match="status fetch failed"):
            TikTokClient(access_token="tt-token").fetch_publish_status("v_inbox_file~v2.abc123")


def test_tiktok_client_fetch_publish_status_raises_on_non_dict_payload() -> None:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = []

    with patch("app.integrations.tiktok_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = response
        MockClient.return_value = mock_ctx

        with pytest.raises(TikTokApiError, match="Unexpected TikTok status payload"):
            TikTokClient(access_token="tt-token").fetch_publish_status("v_inbox_file~v2.abc123")


def test_tiktok_client_fetch_publish_status_raises_on_error_code() -> None:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "data": {},
        "error": {"code": "scope_not_authorized", "message": "video.upload missing"},
    }

    with patch("app.integrations.tiktok_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = response
        MockClient.return_value = mock_ctx

        with pytest.raises(TikTokApiError, match="video.upload missing"):
            TikTokClient(access_token="tt-token").fetch_publish_status("v_inbox_file~v2.abc123")


def test_tiktok_client_fetch_publish_status_falls_back_to_scheduled() -> None:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "data": {},
        "error": {"code": "ok", "message": ""},
    }

    with patch("app.integrations.tiktok_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = response
        MockClient.return_value = mock_ctx

        status = TikTokClient(access_token="tt-token").fetch_publish_status("v_inbox_file~v2.abc123")

    assert status == "scheduled"


def test_schedule_clip_via_tiktok_rejects_non_tiktok_platform(monkeypatch) -> None:
    db = _FakeDb(scalar_values=[])
    monkeypatch.setattr("app.review.publishing.get_settings", lambda: SimpleNamespace())

    with pytest.raises(ValueError, match="only supports platform=tiktok"):
        schedule_clip_via_tiktok(
            db=db,
            rendered_clip_id="clip-1",
            platform=Platform.instagram,
            scheduled_at=datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
            caption="caption",
        )


def test_schedule_clip_via_tiktok_marks_failed_on_api_error(monkeypatch, tmp_path: Path) -> None:
    clip_path = tmp_path / "render.mp4"
    clip_path.write_bytes(b"video-bytes")
    clip = SimpleNamespace(id="clip-1", review_status=ReviewStatus.approved, render_path=str(clip_path), last_error=None)
    db = _FakeDb(scalar_values=[clip])

    class _FailingTikTokClient:
        def __init__(self, access_token: str, base_url: str):
            self.access_token = access_token
            self.base_url = base_url

        def schedule_post(self, video_file_path: str):
            raise TikTokApiError("upload failure")

    monkeypatch.setattr("app.review.publishing.PublicationJob", _FakePublicationJob)
    monkeypatch.setattr("app.review.publishing.TikTokClient", _FailingTikTokClient)
    monkeypatch.setattr("app.review.publishing.get_tiktok_access_token", lambda: "tok")
    monkeypatch.setattr(
        "app.review.publishing.get_settings",
        lambda: SimpleNamespace(tiktok_api_base_url="https://open.tiktokapis.com"),
    )

    result = schedule_clip_via_tiktok(
        db=db,
        rendered_clip_id="clip-1",
        platform=Platform.tiktok,
        scheduled_at=datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
        caption="caption",
    )

    assert result.publish_status == PublishStatus.failed
    assert "TikTok publish failed" in clip.last_error


def test_sync_publication_job_status_unsupported_provider_raises() -> None:
    publication = SimpleNamespace(
        id="pub-unk-1",
        distribution_provider="other",
        publish_status=PublishStatus.pending,
        rendered_clip_fk="clip-1",
    )
    db = _FakeDb(scalar_values=[publication])

    with pytest.raises(ValueError, match="Unsupported distribution provider"):
        sync_publication_job_status(db=db, publication_job_id="pub-unk-1")


def test_schedule_clip_for_distribution_tiktok_success(monkeypatch, tmp_path: Path) -> None:
    clip_path = tmp_path / "render.mp4"
    clip_path.write_bytes(b"video-bytes")
    clip = SimpleNamespace(id="clip-1", review_status=ReviewStatus.approved, render_path=str(clip_path), last_error="old")
    db = _FakeDb(scalar_values=[clip])

    fake_publication = _FakePublicationJob(
        rendered_clip_fk="clip-1",
        platform=Platform.tiktok,
        publish_status=PublishStatus.scheduled,
        external_post_ref="v_inbox_file~v2.abc123",
        distribution_provider=None,
    )

    monkeypatch.setattr("app.review.publishing.assert_clip_compliant", lambda db, rendered_clip_id: None)
    monkeypatch.setattr("app.review.publishing.PublicationJob", _FakePublicationJob)
    monkeypatch.setattr(
        "app.review.publishing.get_settings",
        lambda: SimpleNamespace(publish_provider="tiktok"),
    )
    monkeypatch.setattr("app.review.publishing.schedule_clip_via_tiktok", lambda **kwargs: fake_publication)

    publication = schedule_clip_for_distribution(
        db=db,
        rendered_clip_id="clip-1",
        platform=Platform.tiktok,
        scheduled_at=datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
        caption="caption",
    )

    assert publication.distribution_provider == DistributionProvider.tiktok
    assert publication.external_post_ref == "v_inbox_file~v2.abc123"


def test_sync_publication_job_status_tiktok_success(monkeypatch) -> None:
    publication = SimpleNamespace(
        id="pub-tt-1",
        distribution_provider=DistributionProvider.tiktok,
        external_post_ref="v_inbox_file~v2.123",
        publish_status=PublishStatus.pending,
        rendered_clip_fk="clip-1",
    )
    db = _FakeDb(scalar_values=[publication])

    class _FakeTikTokClient:
        def __init__(self, access_token: str, base_url: str):
            self.access_token = access_token
            self.base_url = base_url

        def fetch_publish_status(self, publish_id: str) -> str:
            assert publish_id == "v_inbox_file~v2.123"
            return "PUBLISH_COMPLETE"

    monkeypatch.setattr("app.review.publishing.TikTokClient", _FakeTikTokClient)
    monkeypatch.setattr("app.review.publishing.get_tiktok_access_token", lambda: "tok")
    monkeypatch.setattr(
        "app.review.publishing.get_settings",
        lambda: SimpleNamespace(tiktok_api_base_url="https://open.tiktokapis.com"),
    )

    result = sync_publication_job_status(db=db, publication_job_id="pub-tt-1")
    assert result.publish_status == PublishStatus.published


def test_sync_publication_job_status_tiktok_missing_ref_raises() -> None:
    publication = SimpleNamespace(
        id="pub-tt-2",
        distribution_provider=DistributionProvider.tiktok,
        external_post_ref=None,
        publish_status=PublishStatus.pending,
        rendered_clip_fk="clip-2",
    )
    db = _FakeDb(scalar_values=[publication])

    with pytest.raises(ValueError, match="no TikTok publish reference"):
        sync_publication_job_status(db=db, publication_job_id="pub-tt-2")


def test_sync_publication_job_status_tiktok_error_marks_failed(monkeypatch) -> None:
    publication = SimpleNamespace(
        id="pub-tt-3",
        distribution_provider=DistributionProvider.tiktok,
        external_post_ref="v_inbox_file~v2.err",
        publish_status=PublishStatus.pending,
        rendered_clip_fk="clip-3",
    )
    clip = SimpleNamespace(last_error=None)
    db = _FakeDb(scalar_values=[publication, clip])

    class _FailingTikTokClient:
        def __init__(self, access_token: str, base_url: str):
            self.access_token = access_token
            self.base_url = base_url

        def fetch_publish_status(self, publish_id: str) -> str:
            raise TikTokApiError("status endpoint temporary failure")

    monkeypatch.setattr("app.review.publishing.TikTokClient", _FailingTikTokClient)
    monkeypatch.setattr("app.review.publishing.get_tiktok_access_token", lambda: "tok")
    monkeypatch.setattr(
        "app.review.publishing.get_settings",
        lambda: SimpleNamespace(tiktok_api_base_url="https://open.tiktokapis.com"),
    )

    result = sync_publication_job_status(db=db, publication_job_id="pub-tt-3")
    assert result.publish_status == PublishStatus.failed
    assert "TikTok status sync failed" in clip.last_error


def test_schedule_clip_via_tiktok_auth_error_retries_after_refresh(monkeypatch, tmp_path: Path) -> None:
    clip_path = tmp_path / "render.mp4"
    clip_path.write_bytes(b"video-bytes")
    clip = SimpleNamespace(id="clip-1", review_status=ReviewStatus.approved, render_path=str(clip_path), last_error=None)
    db = _FakeDb(scalar_values=[clip])

    class _RetryingTikTokClient:
        calls: list[str] = []

        def __init__(self, access_token: str, base_url: str):
            self.access_token = access_token
            self.base_url = base_url

        def schedule_post(self, video_file_path: str):
            self.calls.append(self.access_token)
            if self.access_token == "old-token":
                raise TikTokApiError("access_token_invalid")
            return "v_inbox_file~v2.new", "scheduled"

    monkeypatch.setattr("app.review.publishing.PublicationJob", _FakePublicationJob)
    monkeypatch.setattr("app.review.publishing.TikTokClient", _RetryingTikTokClient)
    monkeypatch.setattr("app.review.publishing.get_settings", lambda: SimpleNamespace(tiktok_api_base_url="https://open.tiktokapis.com"))

    token_state = {"value": "old-token"}
    monkeypatch.setattr("app.review.publishing.get_tiktok_access_token", lambda: token_state["value"])

    def _refresh() -> object:
        token_state["value"] = "new-token"
        return SimpleNamespace(access_token="new-token")

    monkeypatch.setattr("app.review.publishing.refresh_tiktok_access_token", _refresh)

    result = schedule_clip_via_tiktok(
        db=db,
        rendered_clip_id="clip-1",
        platform=Platform.tiktok,
        scheduled_at=datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
        caption="caption",
    )

    assert result.publish_status == PublishStatus.scheduled
    assert result.external_post_ref == "v_inbox_file~v2.new"
    assert _RetryingTikTokClient.calls == ["old-token", "new-token"]


def test_sync_tiktok_status_auth_error_retries_after_refresh(monkeypatch) -> None:
    publication = SimpleNamespace(
        id="pub-tt-retry",
        distribution_provider=DistributionProvider.tiktok,
        external_post_ref="v_inbox_file~v2.123",
        publish_status=PublishStatus.pending,
        rendered_clip_fk="clip-1",
    )
    db = _FakeDb(scalar_values=[publication])

    class _RetryStatusClient:
        calls: list[str] = []

        def __init__(self, access_token: str, base_url: str):
            self.access_token = access_token
            self.base_url = base_url

        def fetch_publish_status(self, publish_id: str) -> str:
            self.calls.append(self.access_token)
            if self.access_token == "old-token":
                raise TikTokApiError("access_token_invalid")
            return "PUBLISH_COMPLETE"

    monkeypatch.setattr("app.review.publishing.TikTokClient", _RetryStatusClient)
    monkeypatch.setattr("app.review.publishing.get_settings", lambda: SimpleNamespace(tiktok_api_base_url="https://open.tiktokapis.com"))

    token_state = {"value": "old-token"}
    monkeypatch.setattr("app.review.publishing.get_tiktok_access_token", lambda: token_state["value"])

    def _refresh() -> object:
        token_state["value"] = "new-token"
        return SimpleNamespace(access_token="new-token")

    monkeypatch.setattr("app.review.publishing.refresh_tiktok_access_token", _refresh)

    result = sync_publication_job_status(db=db, publication_job_id="pub-tt-retry")

    assert result.publish_status == PublishStatus.published
    assert _RetryStatusClient.calls == ["old-token", "new-token"]


def test_schedule_clip_via_tiktok_auth_error_with_refresh_failure_marks_failed(monkeypatch, tmp_path: Path) -> None:
    clip_path = tmp_path / "render.mp4"
    clip_path.write_bytes(b"video-bytes")
    clip = SimpleNamespace(id="clip-1", review_status=ReviewStatus.approved, render_path=str(clip_path), last_error=None)
    db = _FakeDb(scalar_values=[clip])

    class _AuthFailClient:
        def __init__(self, access_token: str, base_url: str):
            self.access_token = access_token
            self.base_url = base_url

        def schedule_post(self, video_file_path: str):
            raise TikTokApiError("access_token_invalid")

    monkeypatch.setattr("app.review.publishing.PublicationJob", _FakePublicationJob)
    monkeypatch.setattr("app.review.publishing.TikTokClient", _AuthFailClient)
    monkeypatch.setattr("app.review.publishing.get_tiktok_access_token", lambda: "old-token")
    monkeypatch.setattr("app.review.publishing.get_settings", lambda: SimpleNamespace(tiktok_api_base_url="https://open.tiktokapis.com"))
    monkeypatch.setattr(
        "app.review.publishing.refresh_tiktok_access_token",
        lambda: (_ for _ in ()).throw(TikTokOAuthError("refresh failed")),
    )

    result = schedule_clip_via_tiktok(
        db=db,
        rendered_clip_id="clip-1",
        platform=Platform.tiktok,
        scheduled_at=datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
        caption="caption",
    )

    assert result.publish_status == PublishStatus.failed
    assert "TikTok publish failed" in clip.last_error