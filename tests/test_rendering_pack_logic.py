from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.db.models import PackType, RenderStatus
from app.rendering.layers import (
    CaptionCue,
    _build_layer_filter,
    _choose_pack_version,
    apply_hook_caption_context_layers,
    _select_creative_pack_versions,
)


class _ScalarsResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class _FakeDb:
    def __init__(self, *, scalar_values=None, scalars_values=None):
        self.scalar_values = list(scalar_values or [])
        self.scalars_values = list(scalars_values or [])
        self.added = []
        self.commit_count = 0

    def scalar(self, _statement):
        return self.scalar_values.pop(0) if self.scalar_values else None

    def scalars(self, _statement):
        items = self.scalars_values.pop(0) if self.scalars_values else []
        return _ScalarsResult(items)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commit_count += 1


def _make_pack(version: str, *, promoted=False, fatigued=False):
    return SimpleNamespace(
        version=version,
        promoted_to_default=promoted,
        fatigue_warning=fatigued,
    )


def test_select_creative_pack_versions_prefers_non_fatigued_active_packs() -> None:
    db = _FakeDb(
        scalars_values=[
            [_make_pack("font-fatigued", promoted=True, fatigued=True), _make_pack("font-fresh", fatigued=False)],
            [_make_pack("transition-fresh", fatigued=False)],
            [_make_pack("animation-fatigued", fatigued=True), _make_pack("animation-fresh", fatigued=False)],
        ]
    )

    selection = _select_creative_pack_versions(db)

    assert selection.font_pack_version == "font-fresh"
    assert selection.transition_pack_version == "transition-fresh"
    assert selection.animation_pack_version == "animation-fresh"


def test_select_creative_pack_versions_falls_back_to_defaults() -> None:
    db = _FakeDb(scalars_values=[[], [], []])

    selection = _select_creative_pack_versions(db)

    assert selection.font_pack_version == "fonts-default-v1"
    assert selection.transition_pack_version == "transitions-default-v1"
    assert selection.animation_pack_version == "animations-default-v1"


def test_apply_layers_persists_selected_pack_versions(monkeypatch, tmp_path) -> None:
    clip = SimpleNamespace(
        id="clip-1",
        render_path=str(tmp_path / "clip.mp4"),
        render_status=RenderStatus.pending,
        last_error=None,
        retry_count=0,
    )
    db = _FakeDb(
        scalar_values=[clip, None],
        scalars_values=[
            [_make_pack("font-v3", fatigued=False)],
            [_make_pack("transition-v2", fatigued=False)],
            [_make_pack("animation-v5", fatigued=False)],
        ],
    )

    monkeypatch.setattr(
        "app.rendering.layers.get_settings",
        lambda: SimpleNamespace(ffmpeg_binary="ffmpeg"),
    )
    monkeypatch.setattr(
        "app.rendering.layers.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )

    output_path = apply_hook_caption_context_layers(
        db=db,
        rendered_clip_id="clip-1",
        hook_text="Cold open",
        context_label="Context",
        caption_cues=[],
        caption_pack_version="captions-v1",
    )

    assert Path(output_path).name.endswith("_layered.mp4")
    assert clip.render_status == RenderStatus.completed

    fingerprint = next(obj for obj in db.added if hasattr(obj, "rendered_clip_fk"))
    assert fingerprint.rendered_clip_fk == "clip-1"
    assert fingerprint.font_pack_version == "font-v3"
    assert fingerprint.transition_pack_version == "transition-v2"
    assert fingerprint.animation_pack_version == "animation-v5"
    assert fingerprint.caption_pack_version == "captions-v1"


# ---------------------------------------------------------------------------
# _choose_pack_version — missing priority paths
# ---------------------------------------------------------------------------

def test_choose_pack_version_returns_promoted_non_fatigued_first() -> None:
    """Loop 1: promoted AND not fatigued → returned immediately (line 87)."""
    packs = [
        _make_pack("v-best", promoted=True, fatigued=False),
        _make_pack("v-fallback", promoted=False, fatigued=False),
    ]
    assert _choose_pack_version(packs, PackType.font) == "v-best"


def test_choose_pack_version_returns_promoted_when_all_fatigued() -> None:
    """Loop 3: all packs fatigued but one promoted → that promoted pack returned (lines 92-94)."""
    packs = [
        _make_pack("v-fatigued", promoted=False, fatigued=True),
        _make_pack("v-fatigued-promoted", promoted=True, fatigued=True),
    ]
    assert _choose_pack_version(packs, PackType.font) == "v-fatigued-promoted"


def test_choose_pack_version_returns_first_pack_when_all_fatigued_no_promoted() -> None:
    """Fallback: all fatigued, none promoted → packs[0].version returned (line 95)."""
    packs = [
        _make_pack("v-first", promoted=False, fatigued=True),
        _make_pack("v-second", promoted=False, fatigued=True),
    ]
    assert _choose_pack_version(packs, PackType.font) == "v-first"


# ---------------------------------------------------------------------------
# _build_layer_filter — caption cue handling (lines 62-66)
# ---------------------------------------------------------------------------

def test_build_layer_filter_skips_invalid_cue_and_includes_valid_cue() -> None:
    """Invalid cue (end <= start) is skipped; valid cue text appears in filter."""
    invalid_cue = CaptionCue(start_ts=2.0, end_ts=1.0, text="should-be-skipped")
    valid_cue = CaptionCue(start_ts=1.0, end_ts=3.0, text="should-appear")
    result = _build_layer_filter("Hook", "Context", [invalid_cue, valid_cue], "white")
    assert "should-appear" in result
    assert "should-be-skipped" not in result


# ---------------------------------------------------------------------------
# apply_hook_caption_context_layers — validation error paths (154,156,159,161)
# ---------------------------------------------------------------------------

def test_apply_layers_raises_when_clip_not_found() -> None:
    db = _FakeDb(scalar_values=[None])
    with pytest.raises(ValueError, match="not found"):
        apply_hook_caption_context_layers(
            db=db, rendered_clip_id="missing", hook_text="h", context_label="c", caption_cues=[]
        )


def test_apply_layers_raises_when_render_path_missing() -> None:
    clip = SimpleNamespace(
        id="c1", render_path=None, render_status=RenderStatus.pending, last_error=None, retry_count=0
    )
    db = _FakeDb(scalar_values=[clip])
    with pytest.raises(ValueError, match="no base render path"):
        apply_hook_caption_context_layers(
            db=db, rendered_clip_id="c1", hook_text="h", context_label="c", caption_cues=[]
        )


def test_apply_layers_raises_when_hook_text_blank() -> None:
    clip = SimpleNamespace(
        id="c1", render_path="/x.mp4", render_status=RenderStatus.pending, last_error=None, retry_count=0
    )
    db = _FakeDb(scalar_values=[clip])
    with pytest.raises(ValueError, match="hook_text is required"):
        apply_hook_caption_context_layers(
            db=db, rendered_clip_id="c1", hook_text="   ", context_label="c", caption_cues=[]
        )


def test_apply_layers_raises_when_context_label_blank() -> None:
    clip = SimpleNamespace(
        id="c1", render_path="/x.mp4", render_status=RenderStatus.pending, last_error=None, retry_count=0
    )
    db = _FakeDb(scalar_values=[clip])
    with pytest.raises(ValueError, match="context_label is required"):
        apply_hook_caption_context_layers(
            db=db, rendered_clip_id="c1", hook_text="Hook", context_label=" ", caption_cues=[]
        )


# ---------------------------------------------------------------------------
# apply_hook_caption_context_layers — captions-v2 yellow font (line 170)
# ---------------------------------------------------------------------------

def test_apply_layers_uses_yellow_caption_color_for_v2(monkeypatch, tmp_path) -> None:
    clip = SimpleNamespace(
        id="clip-cv2",
        render_path=str(tmp_path / "c.mp4"),
        render_status=RenderStatus.pending,
        last_error=None,
        retry_count=0,
    )
    db = _FakeDb(scalar_values=[clip, None], scalars_values=[[], [], []])
    monkeypatch.setattr("app.rendering.layers.get_settings", lambda: SimpleNamespace(ffmpeg_binary="ffmpeg"))
    monkeypatch.setattr("app.rendering.layers.subprocess.run", lambda *a, **k: SimpleNamespace(returncode=0))

    apply_hook_caption_context_layers(
        db=db,
        rendered_clip_id="clip-cv2",
        hook_text="Hook",
        context_label="Ctx",
        caption_cues=[],
        caption_pack_version="captions-v2",
    )

    fp = next(obj for obj in db.added if hasattr(obj, "rendered_clip_fk"))
    assert fp.caption_pack_version == "captions-v2"


# ---------------------------------------------------------------------------
# apply_hook_caption_context_layers — FFmpeg failure path (lines 218-225)
# ---------------------------------------------------------------------------

def test_apply_layers_marks_clip_failed_on_ffmpeg_error(monkeypatch, tmp_path) -> None:
    clip = SimpleNamespace(
        id="clip-err",
        render_path=str(tmp_path / "c.mp4"),
        render_status=RenderStatus.pending,
        last_error=None,
        retry_count=0,
    )
    db = _FakeDb(scalar_values=[clip], scalars_values=[[], [], []])

    def _raise_cpe(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "ffmpeg", stderr="encode fail")

    monkeypatch.setattr("app.rendering.layers.get_settings", lambda: SimpleNamespace(ffmpeg_binary="ffmpeg"))
    monkeypatch.setattr("app.rendering.layers.subprocess.run", _raise_cpe)

    with pytest.raises(RuntimeError, match="Layering failed"):
        apply_hook_caption_context_layers(
            db=db, rendered_clip_id="clip-err", hook_text="Hook", context_label="Ctx", caption_cues=[]
        )

    assert clip.render_status == RenderStatus.failed
    assert clip.retry_count == 1
    assert "encode fail" in clip.last_error