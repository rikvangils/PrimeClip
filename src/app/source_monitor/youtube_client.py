from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.source_monitor.schemas import YouTubeUpload


class YouTubeClient:
    BASE_URL = "https://www.googleapis.com/youtube/v3/search"

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 15.0) -> None:
        self.api_key = api_key or get_settings().youtube_api_key
        self.timeout_seconds = timeout_seconds

    def fetch_recent_uploads(self, channel_id_or_handle: str, max_results: int = 10) -> list[YouTubeUpload]:
        if not self.api_key:
            raise ValueError("Missing YouTube API key. Set PEANUTCLIP_YOUTUBE_API_KEY before polling uploads.")

        params = {
            "part": "snippet",
            "type": "video",
            "order": "date",
            "maxResults": max_results,
            "key": self.api_key,
        }

        # Accept either canonical channel IDs or handles from configuration.
        if channel_id_or_handle.startswith("UC"):
            params["channelId"] = channel_id_or_handle
        else:
            params["q"] = f"{channel_id_or_handle} channel"

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            payload = response.json()

        uploads: list[YouTubeUpload] = []
        for item in payload.get("items", []):
            id_block = item.get("id", {})
            snippet = item.get("snippet", {})
            video_id = id_block.get("videoId")
            if not video_id:
                continue

            published_raw = snippet.get("publishedAt")
            published_at = None
            if published_raw:
                published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00")).astimezone(timezone.utc)

            uploads.append(
                YouTubeUpload(
                    source_video_id=video_id,
                    channel_id=snippet.get("channelId", channel_id_or_handle),
                    title=snippet.get("title", ""),
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    published_at=published_at,
                )
            )

        return uploads