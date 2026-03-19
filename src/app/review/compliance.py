from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ComplianceAudit, RenderedClip, RightsStatus


def get_clip_compliance(db: Session, rendered_clip_id: str) -> ComplianceAudit | None:
    """Return the most recent compliance audit record for a clip, or None if absent."""
    return db.scalar(
        select(ComplianceAudit)
        .where(ComplianceAudit.rendered_clip_fk == rendered_clip_id)
        .order_by(ComplianceAudit.created_at.desc())
        .limit(1)
    )


def set_clip_compliance(
    db: Session,
    rendered_clip_id: str,
    rights_status: RightsStatus,
    decision_reason: str | None,
    reviewer_id: str | None,
    fan_account_disclosed: bool,
) -> ComplianceAudit:
    """Create a new compliance audit record for a clip."""
    clip = db.scalar(select(RenderedClip).where(RenderedClip.id == rendered_clip_id))
    if clip is None:
        raise ValueError(f"Rendered clip not found: {rendered_clip_id}")

    audit = ComplianceAudit(
        rendered_clip_fk=clip.id,
        rights_status=rights_status,
        decision_reason=decision_reason,
        reviewer_id=reviewer_id,
        fan_account_disclosed=fan_account_disclosed,
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


def assert_clip_compliant(db: Session, rendered_clip_id: str) -> None:
    """Raise ValueError if the clip is not cleared for scheduling.

    Blocks scheduling when:
    - No compliance record exists (rights status unknown by default).
    - Rights status is not ``approved``.
    - Fan-account disclosure has not been confirmed.
    """
    audit = get_clip_compliance(db=db, rendered_clip_id=rendered_clip_id)
    if audit is None or audit.rights_status != RightsStatus.approved:
        raise ValueError(
            "Clip rights status must be approved before scheduling. "
            "Record a compliance decision via POST /review/clips/{id}/compliance."
        )
    if not audit.fan_account_disclosed:
        raise ValueError(
            "Fan-account disclosure is required before scheduling. "
            "Set fan_account_disclosed=true in the compliance record."
        )
