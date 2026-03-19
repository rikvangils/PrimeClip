from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.db.models import ExperimentStatus, ObservationWindow, Platform, RecommendationDimension
from app.review.experiments import (
    _experiment_uplift_and_confidence,
    create_experiment,
    get_experiments_workspace,
    get_exploration_budget_summary,
    link_snapshot_to_experiment,
    upsert_exploration_policy,
)
from app.review.recommendation_engine import generate_recommendations, list_recommendations


class _ExecuteResult:
    def __init__(self, first_row=None, all_rows=None):
        self._first_row = first_row
        self._all_rows = all_rows or []

    def first(self):
        return self._first_row

    def all(self):
        return self._all_rows


class _ScalarsResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class _FakeDb:
    def __init__(self, *, scalar_values=None, scalars_values=None, execute_results=None):
        self.scalar_values = list(scalar_values or [])
        self.scalars_values = list(scalars_values or [])
        self.execute_results = list(execute_results or [])
        self.added = []

    def scalar(self, _statement):
        if self.scalar_values:
            return self.scalar_values.pop(0)
        return None

    def scalars(self, _statement):
        if self.scalars_values:
            return _ScalarsResult(self.scalars_values.pop(0))
        return _ScalarsResult([])

    def execute(self, _statement):
        if self.execute_results:
            return self.execute_results.pop(0)
        return _ExecuteResult()

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        return None

    def refresh(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = "generated-id"
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(timezone.utc)


def test_create_experiment_rejects_too_many_variables() -> None:
    db = _FakeDb()

    with pytest.raises(ValueError, match="at most 2 variables"):
        create_experiment(
            db=db,
            name="Too many",
            hypothesis="test",
            changed_variables=["a", "b", "c"],
            baseline_reference=None,
            sample_size_target=10,
        )


def test_create_experiment_defaults_to_draft() -> None:
    db = _FakeDb()

    result = create_experiment(
        db=db,
        name="Hook test",
        hypothesis="hook wins",
        changed_variables=["hook_pattern"],
        baseline_reference="base-1",
        sample_size_target=12,
    )

    assert result.status == "draft"
    assert result.sample_size_current in (0, None)
    assert result.linked_snapshot_count == 0


def test_link_snapshot_to_experiment_missing_experiment() -> None:
    db = _FakeDb(scalar_values=[None])

    with pytest.raises(ValueError, match="Experiment not found"):
        link_snapshot_to_experiment(db=db, experiment_id="exp-missing", performance_snapshot_id="snap-1")


def test_link_snapshot_to_experiment_completes_active_experiment() -> None:
    experiment = SimpleNamespace(
        id="exp-1",
        name="Exp",
        hypothesis="Hyp",
        changed_variables=["hook_pattern"],
        baseline_reference=None,
        sample_size_target=2,
        sample_size_current=1,
        status=ExperimentStatus.active,
        created_at=datetime.now(timezone.utc),
    )
    snapshot = SimpleNamespace(id="snap-1")
    db = _FakeDb(
        scalar_values=[experiment, snapshot, None],
        execute_results=[_ExecuteResult(first_row=(1,))],
    )

    result = link_snapshot_to_experiment(db=db, experiment_id="exp-1", performance_snapshot_id="snap-1")

    assert result.sample_size_current == 2
    assert result.status == "completed"
    assert result.linked_snapshot_count == 1


def test_upsert_exploration_policy_validation_error() -> None:
    db = _FakeDb()

    with pytest.raises(ValueError, match="within min/max band"):
        upsert_exploration_policy(
            db=db,
            name="default",
            target_exploration_ratio=0.5,
            min_exploration_ratio=0.8,
            max_exploration_ratio=0.9,
        )


def test_get_exploration_budget_summary_computes_ratio(monkeypatch) -> None:
    db = _FakeDb(
        execute_results=[
            _ExecuteResult(first_row=(3,)),
            _ExecuteResult(first_row=(10,)),
        ]
    )
    monkeypatch.setattr(
        "app.review.experiments.get_or_create_default_exploration_policy",
        lambda _db: SimpleNamespace(min_exploration_ratio=0.2, max_exploration_ratio=0.4),
    )

    summary = get_exploration_budget_summary(db=db)

    assert summary.current_exploration_ratio == 0.3
    assert summary.within_target_band is True


def test_experiment_uplift_and_confidence_defaults_when_no_links() -> None:
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[])])

    uplift, confidence = _experiment_uplift_and_confidence(db=db, experiment_id="exp-1")

    assert uplift is None
    assert confidence == 0.35


def test_get_experiments_workspace_splits_lists(monkeypatch) -> None:
    active_experiment = SimpleNamespace(
        id="exp-a",
        name="Active",
        status=ExperimentStatus.active,
        changed_variables=["hook"],
        sample_size_target=10,
        sample_size_current=3,
    )
    completed_experiment = SimpleNamespace(
        id="exp-c",
        name="Completed",
        status=ExperimentStatus.completed,
        changed_variables=["caption"],
        sample_size_target=10,
        sample_size_current=10,
    )
    db = _FakeDb(scalars_values=[[active_experiment, completed_experiment]])

    monkeypatch.setattr(
        "app.review.experiments._experiment_uplift_and_confidence",
        lambda db, experiment_id: (2.5, 0.7) if experiment_id == "exp-a" else (1.0, 0.9),
    )

    active, completed = get_experiments_workspace(db=db)

    assert len(active) == 1
    assert len(completed) == 1
    assert active[0].name == "Active"
    assert completed[0].name == "Completed"


def test_generate_recommendations_returns_empty_when_no_rows() -> None:
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=[])])

    results = generate_recommendations(db=db, observation_window=ObservationWindow.twenty_four_hours)

    assert results == []


def test_generate_recommendations_creates_positive_uplift_records() -> None:
    rows = [
        (
            SimpleNamespace(performance_score=90.0),
            SimpleNamespace(platform=Platform.instagram),
            SimpleNamespace(),
            SimpleNamespace(
                hook_pattern="cold_open",
                caption_pack_version="cap-v1",
                font_pack_version="font-v1",
                publish_time_slot="19:00",
            ),
        ),
        (
            SimpleNamespace(performance_score=85.0),
            SimpleNamespace(platform=Platform.instagram),
            SimpleNamespace(),
            SimpleNamespace(
                hook_pattern="cold_open",
                caption_pack_version="cap-v1",
                font_pack_version="font-v1",
                publish_time_slot="19:00",
            ),
        ),
        (
            SimpleNamespace(performance_score=40.0),
            SimpleNamespace(platform=Platform.instagram),
            SimpleNamespace(),
            SimpleNamespace(
                hook_pattern="control",
                caption_pack_version="cap-v0",
                font_pack_version="font-v0",
                publish_time_slot="09:00",
            ),
        ),
    ]
    db = _FakeDb(execute_results=[_ExecuteResult(all_rows=rows), _ExecuteResult()])

    results = generate_recommendations(
        db=db,
        observation_window=ObservationWindow.twenty_four_hours,
        minimum_samples=2,
    )

    assert results
    assert any(result.dimension == RecommendationDimension.hook_pattern.value for result in results)
    assert all((result.expected_uplift or 0) > 0 for result in results)


def test_list_recommendations_maps_records() -> None:
    record = SimpleNamespace(
        id="rec-1",
        dimension=RecommendationDimension.platform,
        recommended_value="instagram",
        platform=Platform.instagram,
        observation_window=ObservationWindow.twenty_four_hours,
        expected_uplift=4.3,
        confidence=0.75,
        rationale="good",
        evidence={"sample_count": 5},
        created_at=datetime.now(timezone.utc),
    )
    db = _FakeDb(scalars_values=[[record]])

    results = list_recommendations(db=db)

    assert len(results) == 1
    assert results[0].platform == "instagram"
    assert results[0].dimension == "platform"
