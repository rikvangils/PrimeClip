from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.integrations.tiktok_oauth import TikTokOAuthError
from app.main import app


def _override_db():
    yield None


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_experiments_workspace_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.get_experiments_workspace",
        lambda db, limit=200: (
            [
                SimpleNamespace(
                    experiment_id="exp-1",
                    name="Hook Test",
                    status="active",
                    changed_variables=["hook_pattern"],
                    sample_size_target=20,
                    sample_size_current=8,
                    confidence=0.72,
                    uplift=4.5,
                )
            ],
            [],
        ),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/experiments/workspace")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert "active" in payload
    assert payload["active"][0]["name"] == "Hook Test"
    assert payload["active"][0]["confidence"] == 0.72


def test_trend_pack_create_contract(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        "app.review.api.create_trend_pack",
        lambda db, pack_type, name, version, status, pack_config: SimpleNamespace(
            trend_pack_id="pack-1",
            pack_type=pack_type.value,
            name=name,
            version=version,
            status=status.value,
            promoted_to_default=False,
            retired_reason=None,
            pack_config=pack_config,
            performance_score=None,
            fatigue_warning=False,
            fatigue_ratio_rolling_30=0.0,
            created_at=now,
        ),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/trend-packs",
            json={
                "pack_type": "caption",
                "name": "Caption Neon",
                "version": "captions-v3",
                "status": "experiment",
                "pack_config": {"style": "neon"},
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["pack_type"] == "caption"
    assert payload["version"] == "captions-v3"


def test_schedule_clip_contract_manual_provider(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.schedule_clip_for_distribution",
        lambda db, rendered_clip_id, platform, scheduled_at, caption: SimpleNamespace(
            id="pub-1",
            distribution_provider=SimpleNamespace(value="manual"),
            platform=SimpleNamespace(value=platform.value),
            publish_status=SimpleNamespace(value="scheduled"),
            external_post_ref="generated/publish_queue/pub-1.json",
            buffer_post_id=None,
        ),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/clips/clip-1/schedule",
            json={
                "platform": "instagram",
                "scheduled_at": "2026-03-18T20:00:00Z",
                "caption": "Test caption",
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["distribution_provider"] == "manual"
    assert payload["publish_status"] == "scheduled"


def test_schedule_clip_failure_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.schedule_clip_for_distribution",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Rendered clip not approved")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/clips/clip-404/schedule",
            json={
                "platform": "instagram",
                "scheduled_at": "2026-03-18T20:00:00Z",
                "caption": "Test caption",
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Rendered clip not approved"


def test_publication_status_sync_failure_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.sync_publication_job_status",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Publication job not found")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/publication-jobs/pub-missing/sync-status")

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Publication job not found"


def test_performance_snapshot_ingest_failure_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.ingest_performance_snapshot",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Publication job not found")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/publication-jobs/pub-missing/performance-snapshots",
            json={
                "source": "instagram",
                "observation_window": "24h",
                "observed_at": "2026-03-18T20:00:00Z",
                "views": 1000,
                "likes": 100,
                "comments": 10,
                "shares": 5,
                "saves": 2,
                "follows_lift": 1,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Publication job not found"


def test_performance_snapshot_detail_failure_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.get_performance_snapshot_detail",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Performance snapshot not found")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/performance-snapshots/snap-missing")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Performance snapshot not found"


def test_publication_jobs_list_contract(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        "app.review.api.list_publication_jobs",
        lambda db, status=None, platform=None, limit=100: [
            {
                "publication_job_id": "pub-1",
                "rendered_clip_id": "clip-1",
                "source_title": "Funny Source",
                "distribution_provider": "manual",
                "platform": "instagram",
                "publish_status": "scheduled",
                "scheduled_at": now,
                "external_post_ref": "generated/publish_queue/pub-1.json",
                "buffer_post_id": None,
                "performance_snapshot_count": 2,
                "last_snapshot_at": now,
            }
        ],
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/publication-jobs")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["distribution_provider"] == "manual"
    assert payload["items"][0]["platform"] == "instagram"


def test_publication_calendar_contract(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        "app.review.api.publication_calendar",
        lambda db, status=None, platform=None, limit=200: [
            {
                "date": now.date().isoformat(),
                "items": [
                    {
                        "publication_job_id": "pub-2",
                        "rendered_clip_id": "clip-2",
                        "source_title": "Another Source",
                        "distribution_provider": "manual",
                        "platform": "tiktok",
                        "publish_status": "scheduled",
                        "scheduled_at": now,
                        "external_post_ref": "generated/publish_queue/pub-2.json",
                        "buffer_post_id": None,
                        "performance_snapshot_count": 0,
                        "last_snapshot_at": None,
                    }
                ],
            }
        ],
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/publication-calendar")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["days"]) == 1
    assert payload["days"][0]["items"][0]["platform"] == "tiktok"


def test_publication_jobs_limit_validation_error() -> None:
    with TestClient(app) as client:
        response = client.get("/review/publication-jobs?limit=999")

    assert response.status_code == 422


def test_publication_calendar_platform_validation_error() -> None:
    with TestClient(app) as client:
        response = client.get("/review/publication-calendar?platform=linkedin")

    assert response.status_code == 422


def test_experiment_create_validation_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.create_experiment",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Experiments may change at most 2 variables")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/experiments",
            json={
                "name": "Too many changes",
                "hypothesis": "Changing too many variables will break attribution",
                "changed_variables": ["a", "b", "c"],
                "sample_size_target": 20,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 422


def test_experiment_link_snapshot_failure_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.link_snapshot_to_experiment",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Experiment not found")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/experiments/exp-missing/snapshots",
            json={"performance_snapshot_id": "snap-1"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment not found"


def test_experiment_status_update_failure_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.set_experiment_status",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Experiment not found")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/experiments/exp-missing/status?status=active")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment not found"


def test_exploration_policy_validation_failure_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.upsert_exploration_policy",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Invalid exploration ratio range")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.put(
            "/review/exploration-policy",
            json={
                "name": "default",
                "target_exploration_ratio": 0.5,
                "min_exploration_ratio": 0.8,
                "max_exploration_ratio": 0.7,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid exploration ratio range"


def test_trend_pack_status_update_failure_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.set_trend_pack_status",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Trend pack not found")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/trend-packs/pack-missing/status",
            json={"status": "retired", "retired_reason": "fatigue"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Trend pack not found"


def test_trend_pack_promote_failure_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.promote_trend_pack",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Trend pack not found")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post("/review/trend-packs/pack-missing/promote")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Trend pack not found"


def test_generate_recommendations_contract(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        "app.review.api.generate_recommendations",
        lambda db, observation_window, platform, minimum_samples: [
            SimpleNamespace(
                recommendation_id="rec-1",
                dimension="hook_pattern",
                recommended_value="cold_open_3s",
                platform="instagram",
                observation_window="24h",
                expected_uplift=7.5,
                confidence=0.81,
                rationale="Strong uplift in last 10 posts",
                evidence={"sample_size": 10, "delta": 7.5},
                created_at=now,
            )
        ],
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/recommendations/generate",
            json={
                "observation_window": "24h",
                "platform": "instagram",
                "minimum_samples": 3,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["dimension"] == "hook_pattern"
    assert payload["items"][0]["recommended_value"] == "cold_open_3s"


def test_generate_recommendations_validation_error() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/review/recommendations/generate",
            json={
                "observation_window": "24h",
                "platform": "instagram",
                "minimum_samples": 0,
            },
        )

    assert response.status_code == 422


def test_list_recommendations_contract(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        "app.review.api.list_recommendations",
        lambda db, observation_window=None, platform=None, limit=100: [
            SimpleNamespace(
                recommendation_id="rec-2",
                dimension="publish_time_slot",
                recommended_value="19:00",
                platform="tiktok",
                observation_window="24h",
                expected_uplift=4.2,
                confidence=0.74,
                rationale="Evening slot outperforms baseline",
                evidence={"sample_size": 12, "delta": 4.2},
                created_at=now,
            )
        ],
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/recommendations?platform=tiktok")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["platform"] == "tiktok"
    assert payload["items"][0]["dimension"] == "publish_time_slot"


def test_list_recommendations_limit_validation_error() -> None:
    with TestClient(app) as client:
        response = client.get("/review/recommendations?limit=999")

    assert response.status_code == 422


def test_insights_dashboard_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.get_insights_dashboard",
        lambda db, observation_window: SimpleNamespace(
            observation_window="24h",
            top_creative_winners=[
                {"label": "hook: cold open", "average_score": 78.3, "sample_count": 9}
            ],
            best_posting_windows=[
                {"label": "19:00", "average_score": 75.1, "sample_count": 11}
            ],
            platform_comparison=[
                {"platform": "instagram", "average_score": 73.5, "sample_count": 14}
            ],
            suggested_next_actions=["Test caption pack v4", "Increase evening slot volume"],
        ),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/insights")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["observation_window"] == "24h"
    assert payload["top_creative_winners"][0]["label"] == "hook: cold open"
    assert payload["best_posting_windows"][0]["label"] == "19:00"


def test_insights_observation_window_validation_error() -> None:
    with TestClient(app) as client:
        response = client.get("/review/insights?observation_window=7d")

    assert response.status_code == 422


def test_tiktok_oauth_start_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.build_tiktok_authorize_url",
        lambda state: f"https://www.tiktok.com/v2/auth/authorize/?state={state}",
    )

    with TestClient(app) as client:
        response = client.get("/review/integrations/tiktok/oauth/start?state=my-state")

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "my-state"
    assert "authorize" in payload["auth_url"]


def test_tiktok_oauth_callback_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.exchange_code_for_tokens",
        lambda code: SimpleNamespace(
            access_token="act-123",
            expires_in=86400,
            refresh_token="rft-123",
            refresh_expires_in=31536000,
            open_id="open-1",
            scope="video.upload",
            token_type="Bearer",
        ),
    )

    with TestClient(app) as client:
        response = client.get("/review/integrations/tiktok/oauth/callback?code=abc")

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"] == "act-123"
    assert payload["refresh_token"] == "rft-123"


def test_tiktok_refresh_token_error_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.refresh_tiktok_access_token",
        lambda refresh_token=None: (_ for _ in ()).throw(TikTokOAuthError("refresh failed")),
    )

    with TestClient(app) as client:
        response = client.post("/review/integrations/tiktok/token/refresh", json={"refresh_token": "bad"})

    assert response.status_code == 400
    assert response.json()["detail"] == "refresh failed"
