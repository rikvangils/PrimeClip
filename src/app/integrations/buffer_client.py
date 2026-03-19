from __future__ import annotations

from datetime import datetime

import httpx


class BufferApiError(RuntimeError):
    """Raised when Buffer API returns an error or unexpected payload."""


class BufferClient:
    def __init__(self, access_token: str, base_url: str = "https://api.bufferapp.com/1") -> None:
        if not access_token:
            raise BufferApiError("Missing Buffer access token")
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")

    def schedule_post(
        self,
        profile_id: str,
        text: str,
        media_url: str,
        scheduled_at: datetime,
    ) -> tuple[str, str]:
        if not profile_id:
            raise BufferApiError("Missing Buffer profile id")

        payload = {
            "profile_ids[]": profile_id,
            "text": text,
            "scheduled_at": int(scheduled_at.timestamp()),
            "media[video]": media_url,
            "access_token": self.access_token,
        }

        url = f"{self.base_url}/updates/create.json"
        with httpx.Client(timeout=20.0) as client:
            response = client.post(url, data=payload)

        if response.status_code >= 400:
            raise BufferApiError(f"Buffer create failed ({response.status_code}): {response.text[:500]}")

        data = response.json()
        update = data.get("update") if isinstance(data, dict) else None
        if not update or "id" not in update:
            raise BufferApiError("Buffer response missing update id")

        return str(update["id"]), str(update.get("status", "scheduled"))

    def fetch_update_status(self, update_id: str) -> str:
        if not update_id:
            raise BufferApiError("Missing Buffer update id")

        url = f"{self.base_url}/updates/{update_id}.json"
        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, params={"access_token": self.access_token})

        if response.status_code >= 400:
            raise BufferApiError(f"Buffer status fetch failed ({response.status_code}): {response.text[:500]}")

        data = response.json()
        if not isinstance(data, dict):
            raise BufferApiError("Unexpected Buffer status payload")
        return str(data.get("status", "scheduled"))