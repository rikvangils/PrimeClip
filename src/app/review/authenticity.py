from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import ComplianceAudit, CreativeFingerprint, RenderedClip, ReviewStatus, RightsStatus


@dataclass(slots=True)
class AuthenticityRouteResult:
    rendered_clip_id: str
    authenticity_score: float
    review_status: str
    reason: str


def _latest_rights_status(db: Session, rendered_clip_id: str) -> RightsStatus | None:
    audit = db.scalar(
        select(ComplianceAudit)
        .where(ComplianceAudit.rendered_clip_fk == rendered_clip_id)
        .order_by(desc(ComplianceAudit.created_at))
    )
    return audit.rights_status if audit else None


def _compute_score(clip: RenderedClip, fingerprint: CreativeFingerprint | None) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    has_hook = bool(fingerprint and fingerprint.hook_pattern)
    has_caption_pack = bool(fingerprint and fingerprint.caption_pack_version)
    has_context_layer = bool(fingerprint and fingerprint.edit_route and "context" in fingerprint.edit_route)
    has_style_variety = bool(
        fingerprint
        and (
            fingerprint.font_pack_version
            or fingerprint.transition_pack_version
            or fingerprint.animation_pack_version
        )
    )

    if has_hook:
        score += 30
        reasons.append("hook layer present")
    if has_caption_pack:
        score += 25
        reasons.append("caption pack applied")
    if has_context_layer:
        score += 20
        reasons.append("context layer present")
    if has_style_variety:
        score += 15
        reasons.append("style variety metadata present")

    if clip.retry_count > 1:
        score -= 10
        reasons.append("render retry penalty applied")

    score = max(0.0, min(100.0, score))
    return score, reasons


def score_and_route_clip(db: Session, rendered_clip_id: str) -> AuthenticityRouteResult:
    """Score transformation quality and route clip to review-ready/revise/reject."""
    clip = db.scalar(select(RenderedClip).where(RenderedClip.id == rendered_clip_id))
    if clip is None:
        raise ValueError(f"Rendered clip not found: {rendered_clip_id}")

    fingerprint = db.scalar(
        select(CreativeFingerprint).where(CreativeFingerprint.rendered_clip_fk == rendered_clip_id)
    )
    score, reasons = _compute_score(clip=clip, fingerprint=fingerprint)

    rights_status = _latest_rights_status(db, rendered_clip_id)
    if rights_status != RightsStatus.approved:
        clip.authenticity_score = 0.0
        clip.review_status = ReviewStatus.rejected
        clip.last_error = "Hard fail: rights status missing or not approved"
        db.add(clip)
        db.commit()
        return AuthenticityRouteResult(
            rendered_clip_id=rendered_clip_id,
            authenticity_score=0.0,
            review_status=clip.review_status.value,
            reason=clip.last_error,
        )

    has_transform = bool(
        fingerprint
        and fingerprint.hook_pattern
        and fingerprint.caption_pack_version
        and fingerprint.edit_route
        and "context" in fingerprint.edit_route
    )

    if not has_transform:
        clip.authenticity_score = score
        clip.review_status = ReviewStatus.rejected
        clip.last_error = "Hard fail: insufficient transformation evidence"
        db.add(clip)
        db.commit()
        return AuthenticityRouteResult(
            rendered_clip_id=rendered_clip_id,
            authenticity_score=score,
            review_status=clip.review_status.value,
            reason=clip.last_error,
        )

    if score >= 70:
        clip.review_status = ReviewStatus.review_ready
        route_reason = "Score >= 70; clip routed to review-ready"
    elif score >= 45:
        clip.review_status = ReviewStatus.revise
        route_reason = "Score between 45 and 69; clip routed to revise"
    else:
        clip.review_status = ReviewStatus.rejected
        route_reason = "Score < 45; clip rejected"

    clip.authenticity_score = score
    clip.last_error = None if clip.review_status == ReviewStatus.review_ready else route_reason
    db.add(clip)
    db.commit()

    reason_text = "; ".join(reasons) if reasons else route_reason
    if clip.review_status != ReviewStatus.review_ready:
        reason_text = f"{route_reason}; {reason_text}" if reasons else route_reason

    return AuthenticityRouteResult(
        rendered_clip_id=rendered_clip_id,
        authenticity_score=score,
        review_status=clip.review_status.value,
        reason=reason_text,
    )