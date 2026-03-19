from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.integrations.tiktok_oauth import (
    TikTokOAuthError,
    TikTokTokenBundle,
    build_tiktok_authorize_url,
    exchange_code_for_tokens,
    get_tiktok_access_token,
    refresh_tiktok_access_token,
    set_runtime_tokens,
)


def test_build_tiktok_authorize_url_contains_expected_query(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.integrations.tiktok_oauth.get_settings",
        lambda: SimpleNamespace(
            tiktok_client_key="client-key",
            tiktok_redirect_uri="https://app.example/review/integrations/tiktok/oauth/callback",
        ),
    )

    url = build_tiktok_authorize_url(state="state-123")

    assert "https://www.tiktok.com/v2/auth/authorize/" in url
    assert "client_key=client-key" in url
    assert "response_type=code" in url
    assert "state=state-123" in url


def test_build_tiktok_authorize_url_raises_without_client_key(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.integrations.tiktok_oauth.get_settings",
        lambda: SimpleNamespace(tiktok_client_key=None, tiktok_redirect_uri="https://app.example/callback"),
    )

    with pytest.raises(TikTokOAuthError, match="CLIENT_KEY"):
        build_tiktok_authorize_url(state="state")


def test_exchange_code_for_tokens_success(monkeypatch) -> None:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "access_token": "act-123",
        "expires_in": 86400,
        "refresh_token": "rft-123",
        "refresh_expires_in": 31536000,
        "open_id": "open-1",
        "scope": "user.info.basic,video.upload",
        "token_type": "Bearer",
    }

    monkeypatch.setattr(
        "app.integrations.tiktok_oauth.get_settings",
        lambda: SimpleNamespace(
            tiktok_client_key="client-key",
            tiktok_client_secret="client-secret",
            tiktok_redirect_uri="https://app.example/review/integrations/tiktok/oauth/callback",
            tiktok_api_base_url="https://open.tiktokapis.com",
            tiktok_refresh_token=None,
            tiktok_access_token=None,
        ),
    )

    with patch("app.integrations.tiktok_oauth.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = response
        MockClient.return_value = mock_ctx

        bundle = exchange_code_for_tokens(code="code-123")

    assert isinstance(bundle, TikTokTokenBundle)
    assert bundle.access_token == "act-123"
    assert get_tiktok_access_token() == "act-123"


def test_exchange_code_for_tokens_raises_on_error_payload(monkeypatch) -> None:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "error": "invalid_request",
        "error_description": "code expired",
    }

    monkeypatch.setattr(
        "app.integrations.tiktok_oauth.get_settings",
        lambda: SimpleNamespace(
            tiktok_client_key="client-key",
            tiktok_client_secret="client-secret",
            tiktok_redirect_uri="https://app.example/review/integrations/tiktok/oauth/callback",
            tiktok_api_base_url="https://open.tiktokapis.com",
            tiktok_refresh_token=None,
            tiktok_access_token=None,
        ),
    )

    with patch("app.integrations.tiktok_oauth.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = response
        MockClient.return_value = mock_ctx

        with pytest.raises(TikTokOAuthError, match="code expired"):
            exchange_code_for_tokens(code="code-123")


def test_refresh_tiktok_access_token_uses_runtime_refresh_token(monkeypatch) -> None:
    set_runtime_tokens(
        TikTokTokenBundle(
            access_token="act-old",
            expires_in=3600,
            refresh_token="rft-runtime",
            refresh_expires_in=31536000,
            open_id="open",
            scope="video.upload",
            token_type="Bearer",
        )
    )

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "access_token": "act-new",
        "expires_in": 3600,
        "refresh_token": "rft-new",
    }

    monkeypatch.setattr(
        "app.integrations.tiktok_oauth.get_settings",
        lambda: SimpleNamespace(
            tiktok_client_key="client-key",
            tiktok_client_secret="client-secret",
            tiktok_api_base_url="https://open.tiktokapis.com",
            tiktok_refresh_token=None,
            tiktok_access_token=None,
            tiktok_redirect_uri="https://app.example/review/integrations/tiktok/oauth/callback",
        ),
    )

    with patch("app.integrations.tiktok_oauth.httpx.Client") as MockClient:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_ctx
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = response
        MockClient.return_value = mock_ctx

        bundle = refresh_tiktok_access_token()

    assert bundle.access_token == "act-new"
    assert get_tiktok_access_token() == "act-new"


def test_refresh_tiktok_access_token_raises_without_refresh_token(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.integrations.tiktok_oauth.get_settings",
        lambda: SimpleNamespace(
            tiktok_client_key="client-key",
            tiktok_client_secret="client-secret",
            tiktok_api_base_url="https://open.tiktokapis.com",
            tiktok_refresh_token=None,
            tiktok_access_token=None,
            tiktok_redirect_uri="https://app.example/review/integrations/tiktok/oauth/callback",
        ),
    )
    monkeypatch.setattr("app.integrations.tiktok_oauth.get_tiktok_refresh_token", lambda: None)

    with pytest.raises(TikTokOAuthError, match="refresh token"):
        refresh_tiktok_access_token(refresh_token=None)
