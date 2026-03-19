from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.integrations.analytics import AnalyticsAdapterError, fetch_buffer_metrics, fetch_instagram_metrics, fetch_tiktok_metrics
from app.integrations.buffer_client import BufferApiError, BufferClient
from app.integrations.readiness import IntegrationConfigurationError, ensure_integrations_ready
from app.main import app


# ---------------------------------------------------------------------------
# BufferClient – construction guards
# ---------------------------------------------------------------------------


def test_buffer_client_raises_on_empty_access_token() -> None:
    with pytest.raises(BufferApiError, match="Missing Buffer access token"):
        BufferClient(access_token="")


def test_buffer_client_instantiates_with_valid_token() -> None:
    client = BufferClient(access_token="tok-abc")
    assert client.access_token == "tok-abc"
    assert "bufferapp.com" in client.base_url


def test_buffer_client_strips_trailing_slash_from_base_url() -> None:
    client = BufferClient(access_token="tok", base_url="https://api.bufferapp.com/1/")
    assert not client.base_url.endswith("/")


# ---------------------------------------------------------------------------
# BufferClient.schedule_post – success path
# ---------------------------------------------------------------------------


def test_schedule_post_returns_update_id_and_status() -> None:
    client = BufferClient(access_token="tok-123")
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"update": {"id": "buf-post-1", "status": "scheduled"}}

    with patch("app.integrations.buffer_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = fake_response
        MockClient.return_value = mock_ctx

        post_id, status = client.schedule_post(
            profile_id="prof-1",
            text="Test caption",
            media_url="https://cdn.example.com/clip.mp4",
            scheduled_at=datetime(2026, 4, 1, 18, 0, tzinfo=timezone.utc),
        )

    assert post_id == "buf-post-1"
    assert status == "scheduled"


def test_schedule_post_uses_status_sent_when_missing_from_response() -> None:
    client = BufferClient(access_token="tok-123")
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"update": {"id": "buf-post-2"}}  # no "status" key

    with patch("app.integrations.buffer_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = fake_response
        MockClient.return_value = mock_ctx

        post_id, status = client.schedule_post(
            profile_id="prof-1",
            text="caption",
            media_url="https://cdn.example.com/clip.mp4",
            scheduled_at=datetime(2026, 4, 1, 18, 0, tzinfo=timezone.utc),
        )

    assert post_id == "buf-post-2"
    assert status == "scheduled"  # default fallback


# ---------------------------------------------------------------------------
# BufferClient.schedule_post – failure paths
# ---------------------------------------------------------------------------


def test_schedule_post_raises_on_missing_profile_id() -> None:
    client = BufferClient(access_token="tok-123")
    with pytest.raises(BufferApiError, match="Missing Buffer profile id"):
        client.schedule_post(
            profile_id="",
            text="caption",
            media_url="https://cdn.example.com/clip.mp4",
            scheduled_at=datetime(2026, 4, 1, 18, 0, tzinfo=timezone.utc),
        )


def test_schedule_post_raises_on_http_error_status() -> None:
    client = BufferClient(access_token="tok-123")
    fake_response = MagicMock()
    fake_response.status_code = 401
    fake_response.text = "Unauthorized"

    with patch("app.integrations.buffer_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = fake_response
        MockClient.return_value = mock_ctx

        with pytest.raises(BufferApiError, match="Buffer create failed"):
            client.schedule_post(
                profile_id="prof-1",
                text="caption",
                media_url="https://cdn.example.com/clip.mp4",
                scheduled_at=datetime(2026, 4, 1, 18, 0, tzinfo=timezone.utc),
            )


def test_schedule_post_raises_when_update_id_missing_in_response() -> None:
    client = BufferClient(access_token="tok-123")
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"success": True}  # no "update" key

    with patch("app.integrations.buffer_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = fake_response
        MockClient.return_value = mock_ctx

        with pytest.raises(BufferApiError, match="missing update id"):
            client.schedule_post(
                profile_id="prof-1",
                text="caption",
                media_url="https://cdn.example.com/clip.mp4",
                scheduled_at=datetime(2026, 4, 1, 18, 0, tzinfo=timezone.utc),
            )


# ---------------------------------------------------------------------------
# BufferClient.fetch_update_status – success and failure paths
# ---------------------------------------------------------------------------


def test_fetch_update_status_returns_status_string() -> None:
    client = BufferClient(access_token="tok-123")
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"id": "buf-post-1", "status": "sent"}

    with patch("app.integrations.buffer_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.get.return_value = fake_response
        MockClient.return_value = mock_ctx

        result = client.fetch_update_status("buf-post-1")

    assert result == "sent"


def test_fetch_update_status_raises_on_empty_update_id() -> None:
    client = BufferClient(access_token="tok-123")
    with pytest.raises(BufferApiError, match="Missing Buffer update id"):
        client.fetch_update_status("")


def test_fetch_update_status_raises_on_http_error() -> None:
    client = BufferClient(access_token="tok-123")
    fake_response = MagicMock()
    fake_response.status_code = 404
    fake_response.text = "Not found"

    with patch("app.integrations.buffer_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.get.return_value = fake_response
        MockClient.return_value = mock_ctx

        with pytest.raises(BufferApiError, match="Buffer status fetch failed"):
            client.fetch_update_status("buf-post-1")


def test_fetch_update_status_raises_on_non_dict_response() -> None:
    client = BufferClient(access_token="tok-123")
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = ["unexpected", "list"]

    with patch("app.integrations.buffer_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.get.return_value = fake_response
        MockClient.return_value = mock_ctx

        with pytest.raises(BufferApiError, match="Unexpected Buffer status payload"):
            client.fetch_update_status("buf-post-1")


def test_fetch_update_status_falls_back_to_scheduled_when_status_absent() -> None:
    client = BufferClient(access_token="tok-123")
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"id": "buf-post-1"}  # no "status" key

    with patch("app.integrations.buffer_client.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.get.return_value = fake_response
        MockClient.return_value = mock_ctx

        result = client.fetch_update_status("buf-post-1")

    assert result == "scheduled"


# ---------------------------------------------------------------------------
# Analytics adapters
# ---------------------------------------------------------------------------


def test_fetch_buffer_metrics_raises_on_missing_post_id() -> None:
    with pytest.raises(AnalyticsAdapterError, match="Buffer post id"):
        fetch_buffer_metrics("")


def test_fetch_buffer_metrics_returns_placeholder_dict() -> None:
    result = fetch_buffer_metrics("buf-1")
    assert result["views"] is None
    assert "likes" in result


def test_fetch_instagram_metrics_raises_on_missing_post_id() -> None:
    with pytest.raises(AnalyticsAdapterError, match="Instagram proxy"):
        fetch_instagram_metrics("")


def test_fetch_instagram_metrics_returns_placeholder_dict() -> None:
    result = fetch_instagram_metrics("ig-1")
    assert result["views"] is None


def test_fetch_tiktok_metrics_raises_on_missing_post_id() -> None:
    with pytest.raises(AnalyticsAdapterError, match="TikTok metrics lookup"):
        fetch_tiktok_metrics("")


def test_fetch_tiktok_metrics_raises_not_configured() -> None:
    with pytest.raises(AnalyticsAdapterError, match="not configured"):
        fetch_tiktok_metrics("tt-1")


# ---------------------------------------------------------------------------
# /health/ready API endpoint
# ---------------------------------------------------------------------------


def _override_db():
    yield None


def test_health_ready_returns_503_when_config_invalid(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.main.get_settings",
        lambda: SimpleNamespace(
            validate_required_integrations=lambda: (_ for _ in ()).throw(
                ValueError("Missing required integration settings: PEANUTCLIP_YOUTUBE_API_KEY")
            )
        ),
    )

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert "PEANUTCLIP_YOUTUBE_API_KEY" in response.json()["detail"]


def test_health_ready_returns_200_when_config_valid(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.main.get_settings",
        lambda: SimpleNamespace(validate_required_integrations=lambda: None),
    )

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


# ---------------------------------------------------------------------------
# IntegrationConfigurationError / ensure_integrations_ready
# ---------------------------------------------------------------------------


def test_ensure_integrations_ready_raises_config_error_on_missing_settings(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.integrations.readiness.get_settings",
        lambda: SimpleNamespace(
            validate_required_integrations=lambda: (_ for _ in ()).throw(
                ValueError("Missing: PEANUTCLIP_YOUTUBE_API_KEY")
            )
        ),
    )
    with pytest.raises(IntegrationConfigurationError, match="Integration configuration invalid"):
        ensure_integrations_ready()


def test_ensure_integrations_ready_passes_when_all_settings_present(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.integrations.readiness.get_settings",
        lambda: SimpleNamespace(validate_required_integrations=lambda: None),
    )
    # Should not raise
    ensure_integrations_ready()
