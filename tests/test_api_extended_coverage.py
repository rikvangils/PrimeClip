"""
API-hardening extension: success-path en fout-pad tests voor de nog niet-gedekte
endpoints in api.py, plus de schedule_clip_via_buffer BufferApiError-path in publishing.py.

Gedekte paden in dit bestand:
  - GET  /review/queue                         (success)
  - POST /review/clips/{id}/decision           (success + 404)
  - GET  /review/clips/{id}/schedule-recommendation (success + 404)
    - POST /review/publication-jobs/{id}/sync-status (success)
    - POST /review/publication-jobs/{id}/performance-snapshots (success)
    - GET  /review/performance-snapshots/{id}    (success)
  - GET  /review/exploration-policy            (success)
  - GET  /review/exploration-budget            (success)
    - GET  /review/experiments                   (success)
    - POST /review/experiments                   (success + 400)
    - POST /review/experiments/{id}/snapshots    (success)
    - POST /review/experiments/{id}/status       (success)
  - POST /review/experiments/{id}/extend       (success + 404)
  - POST /review/experiments/{id}/clone        (success + 404)
  - POST /review/experiments/{id}/stop         (success + 404)
  - POST /review/experiments/{id}/promote      (success + 404)
    - GET  /review/trend-packs                   (success)
    - POST /review/trend-packs                   (success + 400)
    - POST /review/trend-packs/{id}/status       (success)
    - POST /review/trend-packs/{id}/promote      (success)
  - publishing.schedule_clip_via_buffer        (BufferApiError foutpad)
"""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.db.models import Platform, PublishStatus, ReviewStatus
from app.review.schemas import ReviewQueueItem


def _override_db():
    yield None


def _fake_experiment(exp_id: str = "exp-1", status: str = "active"):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        experiment_id=exp_id,
        name="Test Exp",
        hypothesis="H",
        changed_variables=["hook_pattern"],
        baseline_reference=None,
        sample_size_target=10,
        sample_size_current=3,
        status=status,
        linked_snapshot_count=3,
        created_at=now,
    )


def _fake_policy_record():
    return SimpleNamespace(
        policy_id="pol-1",
        name="default",
        target_exploration_ratio=0.20,
        min_exploration_ratio=0.05,
        max_exploration_ratio=0.40,
        active=True,
    )


def _fake_trend_pack_record():
    return SimpleNamespace(
        trend_pack_id="pack-1",
        pack_type="hook",
        name="Hook Pack",
        version="v1",
        status="active",
        promoted_to_default=False,
        retired_reason=None,
        pack_config=None,
        performance_score=None,
        fatigue_warning=False,
        fatigue_ratio_rolling_30=0.0,
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# GET /review/queue
# ---------------------------------------------------------------------------

def test_get_review_queue_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.list_review_queue",
        lambda db, status=None, risk_only=False, platform=None, limit=50: [
            ReviewQueueItem(
                rendered_clip_id="clip-1",
                review_status="review_ready",
                authenticity_score=85.0,
                render_path="out/clip-1.mp4",
                source_video_id="vid-1",
                source_title="My Video",
                source_url="https://yt.test/v/1",
                ranking_score=0.8,
                start_ts=10.0,
                end_ts=40.0,
                hook_pattern="cold_open",
                caption_pack_version="cap-v1",
                font_pack_version=None,
                transition_pack_version=None,
                animation_pack_version=None,
                distribution_provider=None,
                external_post_ref=None,
                publish_status=None,
                buffer_post_id=None,
                risk_flags=[],
            )
        ],
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/queue")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["rendered_clip_id"] == "clip-1"
    assert payload["items"][0]["hook_pattern"] == "cold_open"


# ---------------------------------------------------------------------------
# POST /review/clips/{id}/decision
# ---------------------------------------------------------------------------

def test_post_review_decision_approve_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.apply_review_decision",
        lambda db, rendered_clip_id, action: SimpleNamespace(
            id=rendered_clip_id,
            review_status=SimpleNamespace(value="approved"),
        ),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/clips/clip-1/decision",
            json={"action": "approve"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["review_status"] == "approved"


def test_post_review_decision_not_found(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.apply_review_decision",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Rendered clip not found")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/clips/missing/decision", json={"action": "approve"})

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# GET /review/clips/{id}/schedule-recommendation
# ---------------------------------------------------------------------------

def test_get_clip_schedule_recommendation_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.get_scheduling_recommendation",
        lambda db, rendered_clip_id: SimpleNamespace(
            rendered_clip_id=rendered_clip_id,
            recommended_platform=SimpleNamespace(value="tiktok"),
            recommended_time_slot="18:00-21:00",
            confidence=0.78,
            rationale=["High score suggests TikTok discovery feed"],
        ),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/clips/clip-1/schedule-recommendation")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommended_platform"] == "tiktok"
    assert payload["recommended_time_slot"] == "18:00-21:00"
    assert payload["confidence"] == pytest.approx(0.78)


def test_get_clip_schedule_recommendation_not_found(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.get_scheduling_recommendation",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Rendered clip not found")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/clips/missing/schedule-recommendation")

    app.dependency_overrides.clear()

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /review/publication-jobs/{id}/sync-status
# ---------------------------------------------------------------------------

def test_sync_publication_status_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.sync_publication_job_status",
        lambda db, publication_job_id: SimpleNamespace(
            id=publication_job_id,
            publish_status=SimpleNamespace(value="published"),
        ),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/publication-jobs/pub-1/sync-status")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["publish_status"] == "published"


# ---------------------------------------------------------------------------
# POST /review/publication-jobs/{id}/performance-snapshots
# ---------------------------------------------------------------------------

def test_post_performance_snapshot_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.ingest_performance_snapshot",
        lambda db, publication_job_id, payload: SimpleNamespace(
            snapshot_id="snap-1",
            publication_job_id=publication_job_id,
            source="instagram",
            observation_window="24h",
            performance_score=42.5,
            normalized_metrics={"view_velocity": 0.3},
            score_components={"base": 20.0},
            adapter_warning=None,
        ),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/publication-jobs/pub-1/performance-snapshots",
            json={
                "source": "instagram",
                "observation_window": "24h",
                "mode": "manual",
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["performance_snapshot_id"] == "snap-1"


# ---------------------------------------------------------------------------
# GET /review/performance-snapshots/{id}
# ---------------------------------------------------------------------------

def test_get_performance_snapshot_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.get_performance_snapshot_detail",
        lambda db, performance_snapshot_id: SimpleNamespace(
            performance_snapshot_id=performance_snapshot_id,
            publication_job_id="pub-1",
            source="instagram",
            observation_window="24h",
            observed_at=datetime.now(timezone.utc),
            views=5000,
            likes=300,
            comments=20,
            shares=10,
            saves=8,
            follows_lift=2,
            normalized_metrics={"view_velocity": 0.3},
            score_components={"base": 20.0},
            performance_score=42.5,
        ),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/performance-snapshots/snap-1")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["performance_snapshot_id"] == "snap-1"


# ---------------------------------------------------------------------------
# GET /review/exploration-policy
# ---------------------------------------------------------------------------

def test_get_exploration_policy_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.get_or_create_default_exploration_policy",
        lambda db: SimpleNamespace(
            policy_id="pol-1",
            name="default",
            target_exploration_ratio=0.25,
            min_exploration_ratio=0.20,
            max_exploration_ratio=0.30,
            active=True,
        ),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/exploration-policy")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "default"
    assert payload["target_exploration_ratio"] == pytest.approx(0.25)


# ---------------------------------------------------------------------------
# GET /review/exploration-budget
# ---------------------------------------------------------------------------

def test_get_exploration_budget_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.get_exploration_budget_summary",
        lambda db: SimpleNamespace(
            policy=SimpleNamespace(
                policy_id="pol-1",
                name="default",
                target_exploration_ratio=0.25,
                min_exploration_ratio=0.20,
                max_exploration_ratio=0.30,
                active=True,
            ),
            experiment_publication_count=3,
            total_publication_count=12,
            current_exploration_ratio=0.25,
            within_target_band=True,
        ),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/exploration-budget")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["within_target_band"] is True
    assert payload["current_exploration_ratio"] == pytest.approx(0.25)


def test_put_exploration_policy_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.upsert_exploration_policy",
        lambda db, name, target_exploration_ratio, min_exploration_ratio, max_exploration_ratio:
            _fake_policy_record(),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.put(
            "/review/exploration-policy",
            json={
                "name": "default",
                "target_exploration_ratio": 0.20,
                "min_exploration_ratio": 0.05,
                "max_exploration_ratio": 0.40,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["policy_id"] == "pol-1"


# ---------------------------------------------------------------------------
# GET /review/experiments
# ---------------------------------------------------------------------------

def test_get_experiments_list_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.list_experiments",
        lambda db, status=None, limit=100: [_fake_experiment("exp-1", "active")],
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/experiments")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["status"] == "active"


def test_post_create_experiment_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.create_experiment",
        lambda db, name, hypothesis, changed_variables, baseline_reference, sample_size_target:
            _fake_experiment("exp-new", "active"),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/experiments",
            json={
                "name": "New Experiment",
                "hypothesis": "This will improve engagement significantly",
                "changed_variables": ["hook_pattern"],
                "baseline_reference": None,
                "sample_size_target": 20,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["experiment_id"] == "exp-new"


def test_post_create_experiment_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.create_experiment",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Experiment already exists")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/experiments",
            json={
                "name": "New Experiment",
                "hypothesis": "This will improve engagement significantly",
                "changed_variables": ["hook_pattern"],
                "baseline_reference": None,
                "sample_size_target": 20,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Experiment already exists"


def test_post_link_snapshot_to_experiment_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.link_snapshot_to_experiment",
        lambda db, experiment_id, performance_snapshot_id: _fake_experiment(experiment_id, "active"),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/experiments/exp-1/snapshots",
            json={"performance_snapshot_id": "snap-1"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["experiment_id"] == "exp-1"


def test_post_set_experiment_status_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.set_experiment_status",
        lambda db, experiment_id, status: _fake_experiment(experiment_id, status.value),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/experiments/exp-1/status?status=active")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["experiment_id"] == "exp-1"


# ---------------------------------------------------------------------------
# POST /review/experiments/{id}/extend
# ---------------------------------------------------------------------------

def test_post_extend_experiment_success(monkeypatch) -> None:
    result = _fake_experiment(status="active")
    result.sample_size_target = 15
    monkeypatch.setattr(
        "app.review.api.extend_experiment",
        lambda db, experiment_id, additional_samples: result,
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/experiments/exp-1/extend", json={"additional_samples": 5})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["experiment"]["sample_size_target"] == 15
    assert response.json()["action"] == "extend"


def test_post_extend_experiment_not_found(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.extend_experiment",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Experiment not found")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/experiments/missing/extend", json={"additional_samples": 5})

    app.dependency_overrides.clear()

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /review/experiments/{id}/clone
# ---------------------------------------------------------------------------

def test_post_clone_experiment_success(monkeypatch) -> None:
    cloned = _fake_experiment("clone-1", "draft")
    cloned.name = "Clone Hook Test"
    monkeypatch.setattr(
        "app.review.api.clone_experiment",
        lambda db, experiment_id, name: cloned,
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/experiments/exp-1/clone", json={"name": "Clone Hook Test"})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["experiment"]["name"] == "Clone Hook Test"
    assert response.json()["action"] == "clone"


def test_post_clone_experiment_not_found(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.clone_experiment",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Experiment not found")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/experiments/missing/clone", json={"name": "My Clone Experiment"})

    app.dependency_overrides.clear()

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /review/experiments/{id}/stop
# ---------------------------------------------------------------------------

def test_post_stop_experiment_success(monkeypatch) -> None:
    result = _fake_experiment(status="stopped")
    monkeypatch.setattr("app.review.api.stop_experiment", lambda db, experiment_id: result)
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/experiments/exp-1/stop")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["action"] == "stop"
    assert response.json()["experiment"]["status"] == "stopped"


def test_post_stop_experiment_not_found(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.stop_experiment",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Experiment not found")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/experiments/missing/stop")

    app.dependency_overrides.clear()

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /review/experiments/{id}/promote
# ---------------------------------------------------------------------------

def test_post_promote_experiment_success(monkeypatch) -> None:
    result = _fake_experiment(status="completed")
    monkeypatch.setattr("app.review.api.promote_experiment", lambda db, experiment_id: result)
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/experiments/exp-1/promote")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["action"] == "promote"
    assert response.json()["experiment"]["status"] == "completed"


def test_post_promote_experiment_not_found(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.promote_experiment",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Experiment not found")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/experiments/missing/promote")

    app.dependency_overrides.clear()

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /review/trend-packs
# ---------------------------------------------------------------------------

def test_get_trend_packs_list_success(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        "app.review.api.list_trend_packs",
        lambda db, pack_type=None, status=None, limit=200: [
            SimpleNamespace(
                trend_pack_id="pack-1",
                pack_type="hook",
                name="Cold Open V2",
                version="hook-v2",
                status="active",
                promoted_to_default=True,
                retired_reason=None,
                pack_config=None,
                performance_score=0.81,
                fatigue_warning=False,
                fatigue_ratio_rolling_30=0.10,
                created_at=now,
            )
        ],
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/trend-packs")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["promoted_to_default"] is True


def test_post_create_trend_pack_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.create_trend_pack",
        lambda db, pack_type, name, version, status, pack_config: _fake_trend_pack_record(),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/trend-packs",
            json={
                "pack_type": "hook",
                "name": "New Hook Pack",
                "version": "v1",
                "status": "experiment",
                "pack_config": None,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["trend_pack_id"] == "pack-1"


def test_post_create_trend_pack_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.create_trend_pack",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Trend pack already exists")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/trend-packs",
            json={
                "pack_type": "hook",
                "name": "New Hook Pack",
                "version": "v1",
                "status": "experiment",
                "pack_config": None,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Trend pack already exists"


def test_post_trend_pack_status_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.set_trend_pack_status",
        lambda db, trend_pack_id, status, retired_reason: _fake_trend_pack_record(),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/trend-packs/pack-1/status",
            json={"status": "active", "retired_reason": None},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["trend_pack_id"] == "pack-1"


def test_post_promote_trend_pack_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.promote_trend_pack",
        lambda db, trend_pack_id: _fake_trend_pack_record(),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/trend-packs/pack-1/promote")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["trend_pack_id"] == "pack-1"


# ---------------------------------------------------------------------------
# publishing.schedule_clip_via_buffer — BufferApiError foutpad
# ---------------------------------------------------------------------------

def test_schedule_clip_via_buffer_api_error_marks_publication_failed(monkeypatch) -> None:
    from app.integrations.buffer_client import BufferApiError
    from app.review.publishing import schedule_clip_via_buffer

    clip = SimpleNamespace(
        id="clip-buf",
        review_status=ReviewStatus.approved,
        render_path="out/buf.mp4",
        last_error=None,
    )
    publication = SimpleNamespace(
        id="pub-buf",
        buffer_post_id=None,
        publish_status=PublishStatus.pending,
    )

    class _FakeDb:
        def __init__(self):
            self.added = []

        def scalar(self, _s):
            return clip

        def add(self, obj):
            self.added.append(obj)

        def commit(self):
            pass

        def refresh(self, obj):
            if obj is publication:
                pass

    class _FakeClient:
        def schedule_post(self, **kwargs):
            raise BufferApiError("upstream timeout")

    monkeypatch.setattr("app.review.publishing.get_settings", lambda: SimpleNamespace(
        buffer_access_token="tok",
        buffer_api_base_url="https://api.buffer.test",
        buffer_profile_id_instagram="prof-ig",
        buffer_profile_id_tiktok="prof-tt",
    ))
    monkeypatch.setattr("app.review.publishing.BufferClient", lambda **kwargs: _FakeClient())
    monkeypatch.setattr("app.review.publishing.PublicationJob", lambda **kwargs: publication)

    db = _FakeDb()
    result = schedule_clip_via_buffer(
        db=db,
        rendered_clip_id="clip-buf",
        platform=Platform.instagram,
        scheduled_at=datetime(2026, 3, 18, 20, 0, tzinfo=timezone.utc),
        caption="Test caption",
    )

    assert result.publish_status == PublishStatus.failed
    assert clip.last_error is not None
    assert "upstream timeout" in clip.last_error


def test_schedule_clip_via_buffer_success(monkeypatch) -> None:
    from app.review.publishing import schedule_clip_via_buffer

    clip = SimpleNamespace(
        id="clip-ok",
        review_status=ReviewStatus.approved,
        render_path="out/ok.mp4",
        last_error="old error",
    )
    publication = SimpleNamespace(
        id="pub-ok",
        buffer_post_id=None,
        publish_status=PublishStatus.pending,
    )

    class _FakeDb:
        def __init__(self):
            self.added = []

        def scalar(self, _s):
            return clip

        def add(self, obj):
            self.added.append(obj)

        def commit(self):
            pass

        def refresh(self, obj):
            pass

    class _FakeClient:
        def schedule_post(self, **kwargs):
            return "buf-post-1", "sent"

    monkeypatch.setattr("app.review.publishing.get_settings", lambda: SimpleNamespace(
        buffer_access_token="tok",
        buffer_api_base_url="https://api.buffer.test",
        buffer_profile_id_instagram="prof-ig",
        buffer_profile_id_tiktok="prof-tt",
    ))
    monkeypatch.setattr("app.review.publishing.BufferClient", lambda **kwargs: _FakeClient())
    monkeypatch.setattr("app.review.publishing.PublicationJob", lambda **kwargs: publication)

    db = _FakeDb()
    result = schedule_clip_via_buffer(
        db=db,
        rendered_clip_id="clip-ok",
        platform=Platform.tiktok,
        scheduled_at=datetime(2026, 3, 18, 20, 0, tzinfo=timezone.utc),
        caption="Test",
    )

    assert result.buffer_post_id == "buf-post-1"
    assert result.publish_status == PublishStatus.published
    assert clip.last_error is None
