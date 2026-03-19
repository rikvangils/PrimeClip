from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    ExperimentRegistry,
    ExperimentSnapshotLink,
    ExperimentStatus,
    ExplorationPolicy,
    PerformanceSnapshot,
    PublicationJob,
)


@dataclass(slots=True)
class ExperimentRecord:
    experiment_id: str
    name: str
    hypothesis: str
    changed_variables: list[str]
    baseline_reference: str | None
    sample_size_target: int
    sample_size_current: int
    status: str
    linked_snapshot_count: int
    created_at: object


@dataclass(slots=True)
class ExplorationPolicyRecord:
    policy_id: str
    name: str
    target_exploration_ratio: float
    min_exploration_ratio: float
    max_exploration_ratio: float
    active: bool


@dataclass(slots=True)
class ExplorationBudgetSummary:
    policy: ExplorationPolicyRecord
    experiment_publication_count: int
    total_publication_count: int
    current_exploration_ratio: float
    within_target_band: bool


@dataclass(slots=True)
class ExperimentWorkspaceRecord:
    experiment_id: str
    name: str
    status: str
    changed_variables: list[str]
    sample_size_target: int
    sample_size_current: int
    confidence: float
    uplift: float | None


def _linked_snapshot_count(db: Session, experiment_id: str) -> int:
    row = db.execute(
        select(func.count(ExperimentSnapshotLink.id)).where(ExperimentSnapshotLink.experiment_fk == experiment_id)
    ).first()
    return int(row[0] or 0) if row else 0


def create_experiment(
    db: Session,
    name: str,
    hypothesis: str,
    changed_variables: list[str],
    baseline_reference: str | None,
    sample_size_target: int,
) -> ExperimentRecord:
    if len(changed_variables) > 2:
        raise ValueError("Experiments may change at most 2 variables")

    experiment = ExperimentRegistry(
        name=name,
        hypothesis=hypothesis,
        changed_variables=changed_variables,
        baseline_reference=baseline_reference,
        sample_size_target=sample_size_target,
        status=ExperimentStatus.draft,
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    return ExperimentRecord(
        experiment_id=str(experiment.id),
        name=experiment.name,
        hypothesis=experiment.hypothesis,
        changed_variables=experiment.changed_variables,
        baseline_reference=experiment.baseline_reference,
        sample_size_target=experiment.sample_size_target,
        sample_size_current=experiment.sample_size_current,
        status=experiment.status.value,
        linked_snapshot_count=0,
        created_at=experiment.created_at,
    )


def link_snapshot_to_experiment(db: Session, experiment_id: str, performance_snapshot_id: str) -> ExperimentRecord:
    experiment = db.scalar(select(ExperimentRegistry).where(ExperimentRegistry.id == experiment_id))
    if experiment is None:
        raise ValueError(f"Experiment not found: {experiment_id}")

    snapshot = db.scalar(select(PerformanceSnapshot).where(PerformanceSnapshot.id == performance_snapshot_id))
    if snapshot is None:
        raise ValueError(f"Performance snapshot not found: {performance_snapshot_id}")

    existing = db.scalar(
        select(ExperimentSnapshotLink).where(
            ExperimentSnapshotLink.experiment_fk == experiment_id,
            ExperimentSnapshotLink.performance_snapshot_fk == performance_snapshot_id,
        )
    )
    if existing is None:
        link = ExperimentSnapshotLink(
            experiment_fk=experiment.id,
            performance_snapshot_fk=snapshot.id,
        )
        db.add(link)
        experiment.sample_size_current += 1
        if experiment.sample_size_current >= experiment.sample_size_target and experiment.status == ExperimentStatus.active:
            experiment.status = ExperimentStatus.completed
        db.add(experiment)
        db.commit()
        db.refresh(experiment)

    return ExperimentRecord(
        experiment_id=str(experiment.id),
        name=experiment.name,
        hypothesis=experiment.hypothesis,
        changed_variables=experiment.changed_variables,
        baseline_reference=experiment.baseline_reference,
        sample_size_target=experiment.sample_size_target,
        sample_size_current=experiment.sample_size_current,
        status=experiment.status.value,
        linked_snapshot_count=_linked_snapshot_count(db, str(experiment.id)),
        created_at=experiment.created_at,
    )


def set_experiment_status(db: Session, experiment_id: str, status: ExperimentStatus) -> ExperimentRecord:
    experiment = db.scalar(select(ExperimentRegistry).where(ExperimentRegistry.id == experiment_id))
    if experiment is None:
        raise ValueError(f"Experiment not found: {experiment_id}")

    experiment.status = status
    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    return ExperimentRecord(
        experiment_id=str(experiment.id),
        name=experiment.name,
        hypothesis=experiment.hypothesis,
        changed_variables=experiment.changed_variables,
        baseline_reference=experiment.baseline_reference,
        sample_size_target=experiment.sample_size_target,
        sample_size_current=experiment.sample_size_current,
        status=experiment.status.value,
        linked_snapshot_count=_linked_snapshot_count(db, str(experiment.id)),
        created_at=experiment.created_at,
    )


def list_experiments(db: Session, status: ExperimentStatus | None = None, limit: int = 100) -> list[ExperimentRecord]:
    statement = select(ExperimentRegistry).order_by(ExperimentRegistry.created_at.desc()).limit(limit)
    if status is not None:
        statement = statement.where(ExperimentRegistry.status == status)

    experiments = db.scalars(statement).all()
    return [
        ExperimentRecord(
            experiment_id=str(experiment.id),
            name=experiment.name,
            hypothesis=experiment.hypothesis,
            changed_variables=experiment.changed_variables,
            baseline_reference=experiment.baseline_reference,
            sample_size_target=experiment.sample_size_target,
            sample_size_current=experiment.sample_size_current,
            status=experiment.status.value,
            linked_snapshot_count=_linked_snapshot_count(db, str(experiment.id)),
            created_at=experiment.created_at,
        )
        for experiment in experiments
    ]


def upsert_exploration_policy(
    db: Session,
    name: str,
    target_exploration_ratio: float,
    min_exploration_ratio: float,
    max_exploration_ratio: float,
) -> ExplorationPolicyRecord:
    if not (min_exploration_ratio <= target_exploration_ratio <= max_exploration_ratio):
        raise ValueError("target_exploration_ratio must be within min/max band")

    policy = db.scalar(select(ExplorationPolicy).where(ExplorationPolicy.name == name))
    if policy is None:
        policy = ExplorationPolicy(
            name=name,
            target_exploration_ratio=target_exploration_ratio,
            min_exploration_ratio=min_exploration_ratio,
            max_exploration_ratio=max_exploration_ratio,
            active=True,
        )
    else:
        policy.target_exploration_ratio = target_exploration_ratio
        policy.min_exploration_ratio = min_exploration_ratio
        policy.max_exploration_ratio = max_exploration_ratio
        policy.active = True

    db.add(policy)
    db.commit()
    db.refresh(policy)
    return ExplorationPolicyRecord(
        policy_id=str(policy.id),
        name=policy.name,
        target_exploration_ratio=policy.target_exploration_ratio,
        min_exploration_ratio=policy.min_exploration_ratio,
        max_exploration_ratio=policy.max_exploration_ratio,
        active=policy.active,
    )


def get_or_create_default_exploration_policy(db: Session) -> ExplorationPolicyRecord:
    policy = db.scalar(select(ExplorationPolicy).where(ExplorationPolicy.name == "default"))
    if policy is None:
        return upsert_exploration_policy(db=db, name="default", target_exploration_ratio=0.25, min_exploration_ratio=0.20, max_exploration_ratio=0.30)

    return ExplorationPolicyRecord(
        policy_id=str(policy.id),
        name=policy.name,
        target_exploration_ratio=policy.target_exploration_ratio,
        min_exploration_ratio=policy.min_exploration_ratio,
        max_exploration_ratio=policy.max_exploration_ratio,
        active=policy.active,
    )


def get_exploration_budget_summary(db: Session) -> ExplorationBudgetSummary:
    policy = get_or_create_default_exploration_policy(db)
    experiment_publications = db.execute(
        select(func.count(func.distinct(PerformanceSnapshot.publication_job_fk)))
        .join(ExperimentSnapshotLink, ExperimentSnapshotLink.performance_snapshot_fk == PerformanceSnapshot.id)
    ).first()
    total_publications = db.execute(select(func.count(PublicationJob.id))).first()

    experiment_count = int(experiment_publications[0] or 0) if experiment_publications else 0
    total_count = int(total_publications[0] or 0) if total_publications else 0
    ratio = round(experiment_count / total_count, 4) if total_count else 0.0
    within_band = policy.min_exploration_ratio <= ratio <= policy.max_exploration_ratio if total_count else False

    return ExplorationBudgetSummary(
        policy=policy,
        experiment_publication_count=experiment_count,
        total_publication_count=total_count,
        current_exploration_ratio=ratio,
        within_target_band=within_band,
    )


def _experiment_uplift_and_confidence(db: Session, experiment_id: str) -> tuple[float | None, float]:
    linked_rows = db.execute(
        select(PerformanceSnapshot.performance_score)
        .join(ExperimentSnapshotLink, ExperimentSnapshotLink.performance_snapshot_fk == PerformanceSnapshot.id)
        .where(ExperimentSnapshotLink.experiment_fk == experiment_id)
    ).all()
    linked_scores = [float(row[0]) for row in linked_rows if row[0] is not None]
    if not linked_scores:
        return None, 0.35

    baseline_rows = db.execute(select(PerformanceSnapshot.performance_score)).all()
    baseline_scores = [float(row[0]) for row in baseline_rows if row[0] is not None]
    if not baseline_scores:
        uplift = None
    else:
        uplift = round((sum(linked_scores) / len(linked_scores)) - (sum(baseline_scores) / len(baseline_scores)), 4)

    confidence = round(min(0.95, 0.40 + 0.08 * len(linked_scores)), 2)
    return uplift, confidence


def get_experiments_workspace(db: Session, limit: int = 200) -> tuple[list[ExperimentWorkspaceRecord], list[ExperimentWorkspaceRecord]]:
    experiments = db.scalars(select(ExperimentRegistry).order_by(ExperimentRegistry.created_at.desc()).limit(limit)).all()

    active: list[ExperimentWorkspaceRecord] = []
    completed: list[ExperimentWorkspaceRecord] = []
    for experiment in experiments:
        uplift, confidence = _experiment_uplift_and_confidence(db, str(experiment.id))
        record = ExperimentWorkspaceRecord(
            experiment_id=str(experiment.id),
            name=experiment.name,
            status=experiment.status.value,
            changed_variables=experiment.changed_variables,
            sample_size_target=experiment.sample_size_target,
            sample_size_current=experiment.sample_size_current,
            confidence=confidence,
            uplift=uplift,
        )

        if experiment.status in {ExperimentStatus.active, ExperimentStatus.paused, ExperimentStatus.draft}:
            active.append(record)
        else:
            completed.append(record)

    return active, completed


def extend_experiment(db: Session, experiment_id: str, additional_samples: int) -> ExperimentRecord:
    experiment = db.scalar(select(ExperimentRegistry).where(ExperimentRegistry.id == experiment_id))
    if experiment is None:
        raise ValueError(f"Experiment not found: {experiment_id}")

    experiment.sample_size_target += additional_samples
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return ExperimentRecord(
        experiment_id=str(experiment.id),
        name=experiment.name,
        hypothesis=experiment.hypothesis,
        changed_variables=experiment.changed_variables,
        baseline_reference=experiment.baseline_reference,
        sample_size_target=experiment.sample_size_target,
        sample_size_current=experiment.sample_size_current,
        status=experiment.status.value,
        linked_snapshot_count=_linked_snapshot_count(db, str(experiment.id)),
        created_at=experiment.created_at,
    )


def stop_experiment(db: Session, experiment_id: str) -> ExperimentRecord:
    return set_experiment_status(db=db, experiment_id=experiment_id, status=ExperimentStatus.stopped)


def promote_experiment(db: Session, experiment_id: str) -> ExperimentRecord:
    experiment = db.scalar(select(ExperimentRegistry).where(ExperimentRegistry.id == experiment_id))
    if experiment is None:
        raise ValueError(f"Experiment not found: {experiment_id}")

    # Marking as completed indicates winner promotion decision at workspace level.
    experiment.status = ExperimentStatus.completed
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return ExperimentRecord(
        experiment_id=str(experiment.id),
        name=experiment.name,
        hypothesis=experiment.hypothesis,
        changed_variables=experiment.changed_variables,
        baseline_reference=experiment.baseline_reference,
        sample_size_target=experiment.sample_size_target,
        sample_size_current=experiment.sample_size_current,
        status=experiment.status.value,
        linked_snapshot_count=_linked_snapshot_count(db, str(experiment.id)),
        created_at=experiment.created_at,
    )


def clone_experiment(db: Session, experiment_id: str, name: str) -> ExperimentRecord:
    experiment = db.scalar(select(ExperimentRegistry).where(ExperimentRegistry.id == experiment_id))
    if experiment is None:
        raise ValueError(f"Experiment not found: {experiment_id}")

    clone = ExperimentRegistry(
        name=name,
        hypothesis=experiment.hypothesis,
        changed_variables=experiment.changed_variables,
        baseline_reference=experiment.baseline_reference,
        sample_size_target=experiment.sample_size_target,
        sample_size_current=0,
        status=ExperimentStatus.draft,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return ExperimentRecord(
        experiment_id=str(clone.id),
        name=clone.name,
        hypothesis=clone.hypothesis,
        changed_variables=clone.changed_variables,
        baseline_reference=clone.baseline_reference,
        sample_size_target=clone.sample_size_target,
        sample_size_current=clone.sample_size_current,
        status=clone.status.value,
        linked_snapshot_count=0,
        created_at=clone.created_at,
    )