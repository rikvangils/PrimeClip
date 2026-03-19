from __future__ import annotations

from app.config import get_settings


class IntegrationConfigurationError(ValueError):
    """Raised when required integration configuration is missing or invalid."""


def ensure_integrations_ready() -> None:
    """Validate that required integration settings are present with actionable errors."""
    settings = get_settings()
    try:
        settings.validate_required_integrations()
    except ValueError as exc:
        raise IntegrationConfigurationError(
            f"Integration configuration invalid: {exc}. "
            "Populate the missing PEANUTCLIP_* environment variables or .env values."
        ) from exc