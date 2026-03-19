from __future__ import annotations

from pathlib import Path

import httpx


class TikTokApiError(RuntimeError):
    """Raised when TikTok API returns an error or unexpected payload."""


class TikTokClient:
    def __init__(self, access_token: str, base_url: str = "https://open.tiktokapis.com") -> None:
        if not access_token:
            raise TikTokApiError("Missing TikTok access token")
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    def initialize_file_upload(self, video_size: int) -> tuple[str, str]:
        if video_size <= 0:
            raise TikTokApiError("Video size must be greater than zero")

        payload = {
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1,
            }
        }
        url = f"{self.base_url}/v2/post/publish/inbox/video/init/"
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=self._headers(), json=payload)

        if response.status_code >= 400:
            raise TikTokApiError(f"TikTok init upload failed ({response.status_code}): {response.text[:500]}")

        data = response.json()
        if not isinstance(data, dict):
            raise TikTokApiError("Unexpected TikTok init payload")

        error = data.get("error")
        if isinstance(error, dict) and str(error.get("code", "")).lower() != "ok":
            message = str(error.get("message", "Unknown TikTok API error"))
            raise TikTokApiError(f"TikTok init upload failed: {message}")

        result_data = data.get("data") if isinstance(data.get("data"), dict) else {}
        publish_id = result_data.get("publish_id")
        upload_url = result_data.get("upload_url")
        if not publish_id or not upload_url:
            raise TikTokApiError("TikTok init upload response missing publish_id or upload_url")

        return str(publish_id), str(upload_url)

    def upload_video_file(self, upload_url: str, video_file_path: str) -> None:
        if not upload_url:
            raise TikTokApiError("Missing TikTok upload URL")

        file_path = Path(video_file_path)
        if not file_path.exists() or not file_path.is_file():
            raise TikTokApiError(f"Render file not found for TikTok upload: {video_file_path}")

        content = file_path.read_bytes()
        total_bytes = len(content)
        if total_bytes == 0:
            raise TikTokApiError("Cannot upload empty video file to TikTok")

        headers = {
            "Content-Type": "video/mp4",
            "Content-Length": str(total_bytes),
            "Content-Range": f"bytes 0-{total_bytes - 1}/{total_bytes}",
        }

        with httpx.Client(timeout=120.0) as client:
            response = client.put(upload_url, headers=headers, content=content)

        if response.status_code >= 400:
            raise TikTokApiError(f"TikTok video upload failed ({response.status_code}): {response.text[:500]}")

    def fetch_publish_status(self, publish_id: str) -> str:
        if not publish_id:
            raise TikTokApiError("Missing TikTok publish id")

        url = f"{self.base_url}/v2/post/publish/status/fetch/"
        payload = {"publish_id": publish_id}
        with httpx.Client(timeout=20.0) as client:
            response = client.post(url, headers=self._headers(), json=payload)

        if response.status_code >= 400:
            raise TikTokApiError(f"TikTok publish status fetch failed ({response.status_code}): {response.text[:500]}")

        data = response.json()
        if not isinstance(data, dict):
            raise TikTokApiError("Unexpected TikTok status payload")

        error = data.get("error")
        if isinstance(error, dict) and str(error.get("code", "")).lower() != "ok":
            message = str(error.get("message", "Unknown TikTok API error"))
            raise TikTokApiError(f"TikTok publish status fetch failed: {message}")

        payload_data = data.get("data") if isinstance(data.get("data"), dict) else {}
        status = payload_data.get("status")
        if status is None:
            # TikTok status payloads can differ by rollout. Fallback keeps sync non-fatal.
            return "scheduled"
        return str(status)

    def schedule_post(self, video_file_path: str) -> tuple[str, str]:
        file_path = Path(video_file_path)
        if not file_path.exists() or not file_path.is_file():
            raise TikTokApiError(f"Render file not found for TikTok upload: {video_file_path}")

        publish_id, upload_url = self.initialize_file_upload(video_size=file_path.stat().st_size)
        self.upload_video_file(upload_url=upload_url, video_file_path=video_file_path)
        return publish_id, "scheduled"
