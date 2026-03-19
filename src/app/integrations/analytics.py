from __future__ import annotations


class AnalyticsAdapterError(RuntimeError):
    """Raised when an analytics adapter cannot fetch metrics."""


def fetch_buffer_metrics(buffer_post_id: str) -> dict[str, int | None]:
    if not buffer_post_id:
        raise AnalyticsAdapterError("Buffer post id is required for metrics fetch")

    # MVP placeholder until direct Buffer analytics endpoint contract is finalized.
    return {
        "views": None,
        "likes": None,
        "comments": None,
        "shares": None,
        "saves": None,
        "follows_lift": None,
    }


def fetch_instagram_metrics(buffer_post_id: str) -> dict[str, int | None]:
    if not buffer_post_id:
        raise AnalyticsAdapterError("Instagram proxy lookup requires post reference")

    # MVP placeholder for integration adapter.
    return {
        "views": None,
        "likes": None,
        "comments": None,
        "shares": None,
        "saves": None,
        "follows_lift": None,
    }


def fetch_tiktok_metrics(buffer_post_id: str) -> dict[str, int | None]:
    if not buffer_post_id:
        raise AnalyticsAdapterError("TikTok metrics lookup requires post reference")

    # Pluggable path: non-fatal until concrete adapter is introduced.
    raise AnalyticsAdapterError("TikTok analytics adapter not configured yet")