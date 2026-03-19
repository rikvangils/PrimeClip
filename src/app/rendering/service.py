from __future__ import annotations

import subprocess
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import CandidateSegment, RenderStatus, RenderedClip
from app.rendering.schemas import RenderProfile, RenderResult


def _build_output_path(candidate: CandidateSegment, variant_name: str) -> Path:
    settings = get_settings()
    base_dir = Path(settings.render_output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{candidate.id}_{variant_name}.mp4"
    return base_dir / filename


def _build_ffmpeg_command(
    input_path: str,
    output_path: Path,
    start_ts: float,
    end_ts: float,
    profile: RenderProfile,
) -> list[str]:
    settings = get_settings()
    duration = max(end_ts - start_ts, 1.0)
    vf = (
        "scale='if(gt(a,9/16),-2,1080)':'if(gt(a,9/16),1920,-2)',"
        "crop=1080:1920,format=yuv420p"
    )

    return [
        settings.ffmpeg_binary,
        "-y",
        "-ss",
        f"{start_ts:.3f}",
        "-i",
        input_path,
        "-t",
        f"{duration:.3f}",
        "-vf",
        vf,
        "-r",
        str(profile.fps),
        "-c:v",
        profile.video_codec,
        "-preset",
        profile.preset,
        "-crf",
        str(profile.crf),
        "-c:a",
        profile.audio_codec,
        str(output_path),
    ]


def _get_or_create_render_record(db: Session, candidate_segment_fk: str, variant_name: str) -> RenderedClip:
    clip = db.scalar(
        select(RenderedClip).where(
            RenderedClip.candidate_segment_fk == candidate_segment_fk,
            RenderedClip.variant_name == variant_name,
        )
    )
    if clip is not None:
        return clip

    clip = RenderedClip(
        candidate_segment_fk=candidate_segment_fk,
        variant_name=variant_name,
        render_status=RenderStatus.pending,
    )
    db.add(clip)
    db.flush()
    return clip


def render_candidate_variant(
    db: Session,
    candidate_segment_id: str,
    input_path: str,
    variant_name: str = "default",
    profile: RenderProfile | None = None,
) -> RenderResult:
    """Render one vertical clip variant and persist lifecycle state with retry support."""
    candidate = db.scalar(select(CandidateSegment).where(CandidateSegment.id == candidate_segment_id))
    if not candidate:
        raise ValueError(f"Candidate segment not found: {candidate_segment_id}")

    render_profile = profile or RenderProfile()
    clip = _get_or_create_render_record(db, candidate.id, variant_name)

    output_path = _build_output_path(candidate, variant_name)
    command = _build_ffmpeg_command(
        input_path=input_path,
        output_path=output_path,
        start_ts=candidate.start_ts,
        end_ts=candidate.end_ts,
        profile=render_profile,
    )

    clip.render_status = RenderStatus.processing
    clip.last_error = None
    db.add(clip)
    db.commit()

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        clip.render_status = RenderStatus.completed
        clip.render_path = str(output_path)
        db.add(clip)
        db.commit()
        db.refresh(clip)
        return RenderResult(rendered_clip_id=str(clip.id), output_path=str(output_path), status=clip.render_status.value)
    except subprocess.CalledProcessError as exc:
        clip.render_status = RenderStatus.failed
        clip.retry_count += 1
        stderr = exc.stderr.strip() if exc.stderr else "ffmpeg command failed"
        clip.last_error = stderr[:4000]
        db.add(clip)
        db.commit()
        db.refresh(clip)
        raise RuntimeError(f"Render failed for candidate {candidate_segment_id}: {stderr}") from exc


def retry_rendered_clip(
    db: Session,
    rendered_clip_id: str,
    input_path: str,
    profile: RenderProfile | None = None,
) -> RenderResult:
    clip = db.scalar(select(RenderedClip).where(RenderedClip.id == rendered_clip_id))
    if not clip:
        raise ValueError(f"Rendered clip not found: {rendered_clip_id}")

    return render_candidate_variant(
        db=db,
        candidate_segment_id=str(clip.candidate_segment_fk),
        input_path=input_path,
        variant_name=clip.variant_name,
        profile=profile,
    )