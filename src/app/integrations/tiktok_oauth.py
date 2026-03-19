from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from urllib.parse import urlencode

import httpx

from app.config import get_settings


class TikTokOAuthError(RuntimeError):
    """Raised when TikTok OAuth exchange/refresh fails."""


@dataclass
class TikTokTokenBundle:
    access_token: str
    expires_in: int | None
    refresh_token: str | None
    refresh_expires_in: int | None
    open_id: str | None
    scope: str | None
    token_type: str | None


_runtime_lock = Lock()
_runtime_access_token: str | None = None
_runtime_refresh_token: str | None = None


def _token_endpoint(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/v2/oauth/token/"


def _parse_bundle(payload: dict) -> TikTokTokenBundle:
    access_token = str(payload.get("access_token") or "").strip()
    if not access_token:
        raise TikTokOAuthError("TikTok OAuth response missing access_token")

    expires_in_raw = payload.get("expires_in")
    refresh_expires_raw = payload.get("refresh_expires_in")

    return TikTokTokenBundle(
        access_token=access_token,
        expires_in=int(expires_in_raw) if isinstance(expires_in_raw, int | float | str) and str(expires_in_raw).isdigit() else None,
        refresh_token=str(payload.get("refresh_token")) if payload.get("refresh_token") else None,
        refresh_expires_in=(
            int(refresh_expires_raw)
            if isinstance(refresh_expires_raw, int | float | str) and str(refresh_expires_raw).isdigit()
            else None
        ),
        open_id=str(payload.get("open_id")) if payload.get("open_id") else None,
        scope=str(payload.get("scope")) if payload.get("scope") else None,
        token_type=str(payload.get("token_type")) if payload.get("token_type") else None,
    )


def _post_token_form(form_data: dict[str, str]) -> TikTokTokenBundle:
    settings = get_settings()
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            _token_endpoint(settings.tiktok_api_base_url),
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if response.status_code >= 400:
        raise TikTokOAuthError(f"TikTok OAuth request failed ({response.status_code}): {response.text[:500]}")

    payload = response.json()
    if not isinstance(payload, dict):
        raise TikTokOAuthError("Unexpected TikTok OAuth payload")

    if payload.get("error"):
        desc = payload.get("error_description") or payload.get("description") or payload.get("error")
        raise TikTokOAuthError(f"TikTok OAuth request failed: {desc}")

    return _parse_bundle(payload)


def build_tiktok_authorize_url(state: str, scope: str = "user.info.basic,video.upload") -> str:
    settings = get_settings()
    if not settings.tiktok_client_key:
        raise TikTokOAuthError("Missing PEANUTCLIP_TIKTOK_CLIENT_KEY")
    if not settings.tiktok_redirect_uri:
        raise TikTokOAuthError("Missing PEANUTCLIP_TIKTOK_REDIRECT_URI")

    query = urlencode(
        {
            "client_key": settings.tiktok_client_key,
            "response_type": "code",
            "scope": scope,
            "redirect_uri": settings.tiktok_redirect_uri,
            "state": state,
        }
    )
    return f"https://www.tiktok.com/v2/auth/authorize/?{query}"


def exchange_code_for_tokens(code: str) -> TikTokTokenBundle:
    settings = get_settings()
    if not code:
        raise TikTokOAuthError("Missing OAuth code")
    if not settings.tiktok_client_key or not settings.tiktok_client_secret:
        raise TikTokOAuthError("Missing TikTok client credentials")
    if not settings.tiktok_redirect_uri:
        raise TikTokOAuthError("Missing PEANUTCLIP_TIKTOK_REDIRECT_URI")

    bundle = _post_token_form(
        {
            "client_key": settings.tiktok_client_key,
            "client_secret": settings.tiktok_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.tiktok_redirect_uri,
        }
    )
    set_runtime_tokens(bundle)
    return bundle


def refresh_tiktok_access_token(refresh_token: str | None = None) -> TikTokTokenBundle:
    settings = get_settings()
    token_to_use = refresh_token or get_tiktok_refresh_token() or settings.tiktok_refresh_token
    if not token_to_use:
        raise TikTokOAuthError("Missing TikTok refresh token")
    if not settings.tiktok_client_key or not settings.tiktok_client_secret:
        raise TikTokOAuthError("Missing TikTok client credentials")

    bundle = _post_token_form(
        {
            "client_key": settings.tiktok_client_key,
            "client_secret": settings.tiktok_client_secret,
            "grant_type": "refresh_token",
            "refresh_token": token_to_use,
        }
    )
    set_runtime_tokens(bundle)
    return bundle


def set_runtime_tokens(bundle: TikTokTokenBundle) -> None:
    global _runtime_access_token
    global _runtime_refresh_token
    with _runtime_lock:
        _runtime_access_token = bundle.access_token
        if bundle.refresh_token:
            _runtime_refresh_token = bundle.refresh_token


def get_tiktok_access_token() -> str | None:
    with _runtime_lock:
        if _runtime_access_token:
            return _runtime_access_token
    return get_settings().tiktok_access_token


def get_tiktok_refresh_token() -> str | None:
    with _runtime_lock:
        if _runtime_refresh_token:
            return _runtime_refresh_token
    return get_settings().tiktok_refresh_token
