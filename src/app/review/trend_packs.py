from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CreativeFingerprint, PackType, PublicationJob, TrendPack, TrendPackStatus


@dataclass(slots=True)
class TrendPackRecord:
    trend_pack_id: str
    pack_type: str
    name: str
    version: str
    status: str
    promoted_to_default: bool
    retired_reason: str | None
    pack_config: dict | None
    performance_score: float | None
    fatigue_warning: bool
    fatigue_ratio_rolling_30: float
    created_at: object


def _field_for_pack_type(pack_type: PackType) -> str:
    mapping = {
        PackType.hook: "hook_pattern",
        PackType.caption: "caption_pack_version",
        PackType.font: "font_pack_version",
        PackType.transition: "transition_pack_version",
        PackType.animation: "animation_pack_version",
        PackType.series_format: "edit_route",
    }
    return mapping[pack_type]


def _refresh_fatigue(db: Session, pack: TrendPack, window_size: int = 30, fatigue_threshold: float = 0.40) -> None:
    jobs = db.scalars(
        select(PublicationJob)
        .order_by(PublicationJob.created_at.desc())
        .limit(window_size)
    ).all()

    if not jobs:
        pack.fatigue_ratio_rolling_30 = 0.0
        pack.fatigue_warning = False
        db.add(pack)
        return

    fingerprint_field = _field_for_pack_type(pack.pack_type)
    matches = 0
    for job in jobs:
        fingerprint = db.scalar(select(CreativeFingerprint).where(CreativeFingerprint.rendered_clip_fk == job.rendered_clip_fk))
        if fingerprint is None:
            continue
        value = getattr(fingerprint, fingerprint_field)
        if value == pack.version:
            matches += 1

    ratio = round(matches / len(jobs), 4)
    pack.fatigue_ratio_rolling_30 = ratio
    pack.fatigue_warning = ratio > fatigue_threshold
    db.add(pack)


def _to_record(pack: TrendPack) -> TrendPackRecord:
    return TrendPackRecord(
        trend_pack_id=str(pack.id),
        pack_type=pack.pack_type.value,
        name=pack.name,
        version=pack.version,
        status=pack.status.value,
        promoted_to_default=pack.promoted_to_default,
        retired_reason=pack.retired_reason,
        pack_config=pack.pack_config,
        performance_score=pack.performance_score,
        fatigue_warning=pack.fatigue_warning,
        fatigue_ratio_rolling_30=pack.fatigue_ratio_rolling_30,
        created_at=pack.created_at,
    )


def create_trend_pack(
    db: Session,
    pack_type: PackType,
    name: str,
    version: str,
    status: TrendPackStatus,
    pack_config: dict | None,
) -> TrendPackRecord:
    existing = db.scalar(
        select(TrendPack).where(TrendPack.pack_type == pack_type, TrendPack.version == version)
    )
    if existing is not None:
        raise ValueError(f"Trend pack already exists for {pack_type.value}:{version}")

    pack = TrendPack(
        pack_type=pack_type,
        name=name,
        version=version,
        status=status,
        pack_config=pack_config,
        promoted_to_default=False,
    )
    db.add(pack)
    db.commit()
    db.refresh(pack)

    _refresh_fatigue(db, pack)
    db.commit()
    db.refresh(pack)
    return _to_record(pack)


def list_trend_packs(
    db: Session,
    pack_type: PackType | None = None,
    status: TrendPackStatus | None = None,
    limit: int = 200,
) -> list[TrendPackRecord]:
    statement = select(TrendPack).order_by(TrendPack.created_at.desc()).limit(limit)
    if pack_type is not None:
        statement = statement.where(TrendPack.pack_type == pack_type)
    if status is not None:
        statement = statement.where(TrendPack.status == status)

    packs = db.scalars(statement).all()
    for pack in packs:
        _refresh_fatigue(db, pack)
    db.commit()
    for pack in packs:
        db.refresh(pack)

    return [_to_record(pack) for pack in packs]


def set_trend_pack_status(
    db: Session,
    trend_pack_id: str,
    status: TrendPackStatus,
    retired_reason: str | None = None,
) -> TrendPackRecord:
    pack = db.scalar(select(TrendPack).where(TrendPack.id == trend_pack_id))
    if pack is None:
        raise ValueError(f"Trend pack not found: {trend_pack_id}")

    pack.status = status
    pack.retired_reason = retired_reason if status == TrendPackStatus.retired else None
    if status != TrendPackStatus.active:
        pack.promoted_to_default = False
    _refresh_fatigue(db, pack)
    db.add(pack)
    db.commit()
    db.refresh(pack)
    return _to_record(pack)


def promote_trend_pack(db: Session, trend_pack_id: str) -> TrendPackRecord:
    pack = db.scalar(select(TrendPack).where(TrendPack.id == trend_pack_id))
    if pack is None:
        raise ValueError(f"Trend pack not found: {trend_pack_id}")

    siblings = db.scalars(select(TrendPack).where(TrendPack.pack_type == pack.pack_type)).all()
    for sibling in siblings:
        if sibling.id == pack.id:
            sibling.status = TrendPackStatus.active
            sibling.promoted_to_default = True
        else:
            sibling.promoted_to_default = False
        db.add(sibling)

    _refresh_fatigue(db, pack)
    db.commit()
    db.refresh(pack)
    return _to_record(pack)