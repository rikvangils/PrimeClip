from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import CreativeFingerprint, PackType, RenderStatus, RenderedClip, TrendPack, TrendPackStatus


@dataclass(slots=True)
class CaptionCue:
    start_ts: float
    end_ts: float
    text: str


@dataclass(slots=True)
class CreativePackSelection:
    font_pack_version: str
    transition_pack_version: str
    animation_pack_version: str


DEFAULT_PACK_VERSIONS = {
    PackType.font: "fonts-default-v1",
    PackType.transition: "transitions-default-v1",
    PackType.animation: "animations-default-v1",
}


def _sanitize_drawtext(text: str) -> str:
    return text.replace("\\", r"\\").replace(":", r"\:").replace("'", r"\'")


def _build_layer_filter(hook_text: str, context_label: str, caption_cues: list[CaptionCue], font_color: str) -> str:
    filters: list[str] = []

    hook = _sanitize_drawtext(hook_text)
    context = _sanitize_drawtext(context_label)

    filters.append(
        "drawtext="
        f"text='{hook}':"
        "x=(w-text_w)/2:y=h*0.10:"
        "fontsize=68:fontcolor=white:borderw=3:bordercolor=black@0.8:"
        "enable='between(t,0,3.2)'"
    )

    filters.append("drawbox=x=0:y=h-170:w=w:h=170:color=black@0.40:t=fill")
    filters.append(
        "drawtext="
        f"text='{context}':"
        "x=(w-text_w)/2:y=h-130:"
        "fontsize=40:fontcolor=white:borderw=2:bordercolor=black@0.8"
    )

    for cue in caption_cues:
        if cue.end_ts <= cue.start_ts:
            continue

        caption_text = _sanitize_drawtext(cue.text)
        filters.append(
            "drawtext="
            f"text='{caption_text}':"
            "x=(w-text_w)/2:y=h-280:"
            f"fontsize=52:fontcolor={font_color}:borderw=3:bordercolor=black@0.9:"
            f"enable='between(t,{cue.start_ts:.2f},{cue.end_ts:.2f})'"
        )

    return ",".join(filters)


def _build_layered_output_path(original_path: str) -> Path:
    path = Path(original_path)
    return path.with_name(f"{path.stem}_layered{path.suffix}")


def _choose_pack_version(packs: list[TrendPack], pack_type: PackType) -> str:
    default_version = DEFAULT_PACK_VERSIONS[pack_type]

    for pack in packs:
        if pack.promoted_to_default and not pack.fatigue_warning:
            return pack.version
    for pack in packs:
        if not pack.fatigue_warning:
            return pack.version
    for pack in packs:
        if pack.promoted_to_default:
            return pack.version
    if packs:
        return packs[0].version
    return default_version


def _select_creative_pack_versions(db: Session) -> CreativePackSelection:
    selections: dict[PackType, str] = {}

    for pack_type in (PackType.font, PackType.transition, PackType.animation):
        packs = db.scalars(
            select(TrendPack)
            .where(TrendPack.pack_type == pack_type, TrendPack.status == TrendPackStatus.active)
            .order_by(TrendPack.promoted_to_default.desc(), TrendPack.created_at.desc())
        ).all()
        selections[pack_type] = _choose_pack_version(packs, pack_type)

    return CreativePackSelection(
        font_pack_version=selections[PackType.font],
        transition_pack_version=selections[PackType.transition],
        animation_pack_version=selections[PackType.animation],
    )


def _upsert_fingerprint(
    db: Session,
    rendered_clip_fk: str,
    hook_text: str,
    caption_pack_version: str,
    font_pack_version: str,
    transition_pack_version: str,
    animation_pack_version: str,
) -> None:
    fingerprint = db.scalar(
        select(CreativeFingerprint).where(CreativeFingerprint.rendered_clip_fk == rendered_clip_fk)
    )
    if fingerprint is None:
        fingerprint = CreativeFingerprint(rendered_clip_fk=rendered_clip_fk)

    fingerprint.hook_pattern = hook_text[:255]
    fingerprint.caption_pack_version = caption_pack_version
    fingerprint.font_pack_version = font_pack_version
    fingerprint.transition_pack_version = transition_pack_version
    fingerprint.animation_pack_version = animation_pack_version
    # Context presence is encoded in route metadata for E3-S2.
    fingerprint.edit_route = "hook-caption-context"

    db.add(fingerprint)


def apply_hook_caption_context_layers(
    db: Session,
    rendered_clip_id: str,
    hook_text: str,
    context_label: str,
    caption_cues: list[CaptionCue],
    caption_pack_version: str = "captions-v1",
) -> str:
    """Apply hook/caption/context layers and update creative metadata for the clip."""
    clip = db.scalar(select(RenderedClip).where(RenderedClip.id == rendered_clip_id))
    if clip is None:
        raise ValueError(f"Rendered clip not found: {rendered_clip_id}")
    if not clip.render_path:
        raise ValueError(f"Rendered clip has no base render path: {rendered_clip_id}")

    if not hook_text.strip():
        raise ValueError("hook_text is required for transformative layering")
    if not context_label.strip():
        raise ValueError("context_label is required for transformative layering")

    settings = get_settings()
    input_path = clip.render_path
    output_path = _build_layered_output_path(input_path)
    selected_packs = _select_creative_pack_versions(db)

    pack_font_color = "white"
    if caption_pack_version == "captions-v2":
        pack_font_color = "yellow"

    layer_filter = _build_layer_filter(
        hook_text=hook_text,
        context_label=context_label,
        caption_cues=caption_cues,
        font_color=pack_font_color,
    )

    command = [
        settings.ffmpeg_binary,
        "-y",
        "-i",
        input_path,
        "-vf",
        layer_filter,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "22",
        "-c:a",
        "copy",
        str(output_path),
    ]

    clip.render_status = RenderStatus.processing
    clip.last_error = None
    db.add(clip)
    db.commit()

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        clip.render_status = RenderStatus.completed
        clip.render_path = str(output_path)
        _upsert_fingerprint(
            db=db,
            rendered_clip_fk=clip.id,
            hook_text=hook_text,
            caption_pack_version=caption_pack_version,
            font_pack_version=selected_packs.font_pack_version,
            transition_pack_version=selected_packs.transition_pack_version,
            animation_pack_version=selected_packs.animation_pack_version,
        )
        db.add(clip)
        db.commit()
        return str(output_path)
    except subprocess.CalledProcessError as exc:
        clip.render_status = RenderStatus.failed
        clip.retry_count += 1
        stderr = exc.stderr.strip() if exc.stderr else "ffmpeg layering command failed"
        clip.last_error = stderr[:4000]
        db.add(clip)
        db.commit()
        raise RuntimeError(f"Layering failed for rendered clip {rendered_clip_id}: {stderr}") from exc