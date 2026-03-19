from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PEANUTCLIP_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "PeanutClip AutoFlow"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/peanutclip"
    render_output_dir: str = "generated/renders"
    manual_publish_export_dir: str = "generated/publish_queue"
    ffmpeg_binary: str = "ffmpeg"
    publish_provider: str = "manual"

    # Start with one allowed source as required by Sprint 1 whitelisting.
    source_channel_whitelist: list[str] = Field(default_factory=lambda: ["theburntpeanut"])

    youtube_api_key: str | None = None
    buffer_access_token: str | None = None
    buffer_api_base_url: str = "https://api.bufferapp.com/1"
    buffer_profile_id_instagram: str | None = None
    buffer_profile_id_tiktok: str | None = None
    tiktok_access_token: str | None = None
    tiktok_api_base_url: str = "https://open.tiktokapis.com"
    tiktok_client_key: str | None = None
    tiktok_client_secret: str | None = None
    tiktok_redirect_uri: str | None = None
    tiktok_refresh_token: str | None = None
    instagram_access_token: str | None = None

    @field_validator("source_channel_whitelist", mode="before")
    @classmethod
    def parse_source_channel_whitelist(cls, value: Any) -> list[str]:
        if value is None:
            return ["theburntpeanut"]

        if isinstance(value, str):
            cleaned = [item.strip() for item in value.split(",") if item.strip()]
            return cleaned or ["theburntpeanut"]

        if isinstance(value, list):
            cleaned = [str(item).strip() for item in value if str(item).strip()]
            return cleaned or ["theburntpeanut"]

        raise ValueError("PEANUTCLIP_SOURCE_CHANNEL_WHITELIST must be a comma-separated string or list")

    def validate_required_integrations(self) -> None:
        missing: list[str] = []
        if not self.youtube_api_key:
            missing.append("PEANUTCLIP_YOUTUBE_API_KEY")

        if self.publish_provider == "buffer":
            if not self.buffer_access_token:
                missing.append("PEANUTCLIP_BUFFER_ACCESS_TOKEN")
            if not (self.buffer_profile_id_instagram or self.buffer_profile_id_tiktok):
                missing.append("PEANUTCLIP_BUFFER_PROFILE_ID_INSTAGRAM or PEANUTCLIP_BUFFER_PROFILE_ID_TIKTOK")

        if self.publish_provider == "tiktok":
            if not self.tiktok_access_token:
                missing.append("PEANUTCLIP_TIKTOK_ACCESS_TOKEN")
            if self.tiktok_refresh_token and (not self.tiktok_client_key or not self.tiktok_client_secret):
                missing.append("PEANUTCLIP_TIKTOK_CLIENT_KEY and PEANUTCLIP_TIKTOK_CLIENT_SECRET")

        if missing:
            required = ", ".join(missing)
            raise ValueError(f"Missing required integration settings: {required}")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()