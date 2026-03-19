from __future__ import annotations

from types import SimpleNamespace

from app.db.models import Platform
from app.review.authenticity import _compute_score
from app.review.publishing import _resolve_buffer_profile_id, _to_publish_status
from app.review.queue import _risk_flags


def test_compute_score_with_full_transformation_metadata() -> None:
    clip = SimpleNamespace(retry_count=0)
    fingerprint = SimpleNamespace(
        hook_pattern="cold_open",
        caption_pack_version="captions-v1",
        edit_route="context+style",
        font_pack_version="font-v1",
        transition_pack_version=None,
        animation_pack_version=None,
    )

    score, reasons = _compute_score(clip=clip, fingerprint=fingerprint)

    assert score == 90.0
    assert "hook layer present" in reasons
    assert "caption pack applied" in reasons
    assert "context layer present" in reasons
    assert "style variety metadata present" in reasons


def test_compute_score_applies_retry_penalty() -> None:
    clip = SimpleNamespace(retry_count=2)
    fingerprint = SimpleNamespace(
        hook_pattern="cold_open",
        caption_pack_version="captions-v1",
        edit_route="context+style",
        font_pack_version="font-v1",
        transition_pack_version="transition-v1",
        animation_pack_version="anim-v1",
    )

    score, reasons = _compute_score(clip=clip, fingerprint=fingerprint)

    assert score == 80.0
    assert "render retry penalty applied" in reasons


def test_compute_score_without_fingerprint() -> None:
    clip = SimpleNamespace(retry_count=0)

    score, reasons = _compute_score(clip=clip, fingerprint=None)

    assert score == 0.0
    assert reasons == []


def test_compute_score_is_capped_at_zero() -> None:
    clip = SimpleNamespace(retry_count=3)
    fingerprint = None

    score, reasons = _compute_score(clip=clip, fingerprint=fingerprint)

    assert score == 0.0
    assert "render retry penalty applied" in reasons


def test_risk_flags_all_relevant_flags_present() -> None:
    clip = SimpleNamespace(authenticity_score=None, last_error="boom", retry_count=3)

    flags = _risk_flags(clip)

    assert "missing_authenticity_score" in flags
    assert "processing_error" in flags
    assert "high_retry_count" in flags


def test_risk_flags_low_score_flag_present() -> None:
    clip = SimpleNamespace(authenticity_score=55.0, last_error=None, retry_count=0)

    flags = _risk_flags(clip)

    assert flags == ["low_authenticity_score"]


def test_risk_flags_empty_when_clip_is_healthy() -> None:
    clip = SimpleNamespace(authenticity_score=85.0, last_error=None, retry_count=0)

    flags = _risk_flags(clip)

    assert flags == []


def test_to_publish_status_mappings() -> None:
    assert _to_publish_status("posted").value == "published"
    assert _to_publish_status("FAILED").value == "failed"
    assert _to_publish_status("pending").value == "scheduled"
    assert _to_publish_status("PUBLISH_COMPLETE").value == "published"
    assert _to_publish_status("PROCESSING_UPLOAD").value == "scheduled"


def test_to_publish_status_fallback_defaults_to_scheduled() -> None:
    assert _to_publish_status("unknown-status").value == "scheduled"


def test_resolve_buffer_profile_id_uses_platform_specific_setting(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.publishing.get_settings",
        lambda: SimpleNamespace(
            buffer_profile_id_instagram="ig-123",
            buffer_profile_id_tiktok="tt-456",
        ),
    )

    instagram_profile = _resolve_buffer_profile_id(Platform.instagram)
    tiktok_profile = _resolve_buffer_profile_id(Platform.tiktok)

    assert instagram_profile == "ig-123"
    assert tiktok_profile == "tt-456"
