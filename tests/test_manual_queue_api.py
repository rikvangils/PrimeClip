from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _write_queue_job(queue_dir: Path, video_path: Path) -> None:
    payload = {
        "publication_job_id": "pub-1",
        "rendered_clip_id": "clip-1",
        "platform": "tiktok",
        "scheduled_at": "2026-03-19T20:00:00+00:00",
        "caption": "Quick dinner idea #food #easy",
        "render_path": str(video_path),
        "distribution_provider": "manual",
    }
    (queue_dir / "pub-1.json").write_text(json.dumps(payload), encoding="utf-8")


def test_manual_queue_lists_jobs_and_derives_caption_fields(tmp_path, monkeypatch) -> None:
    queue_dir = tmp_path / "publish_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    video_path = tmp_path / "demo.mp4"
    video_path.write_bytes(b"fake-video-data")
    _write_queue_job(queue_dir=queue_dir, video_path=video_path)

    monkeypatch.setattr("app.manual_queue.api.QUEUE_DIR", queue_dir)

    client = TestClient(app)
    response = client.get("/manual-queue/api/jobs")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    job = payload["items"][0]
    assert job["publication_job_id"] == "pub-1"
    assert job["title"] == "Quick dinner idea"
    assert job["description"] == "Quick dinner idea"
    assert job["hashtags"] == ["#food", "#easy"]


def test_manual_queue_details_page_includes_copyable_fields(tmp_path, monkeypatch) -> None:
    queue_dir = tmp_path / "publish_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    video_path = tmp_path / "demo.mp4"
    video_path.write_bytes(b"fake-video-data")
    _write_queue_job(queue_dir=queue_dir, video_path=video_path)

    monkeypatch.setattr("app.manual_queue.api.QUEUE_DIR", queue_dir)

    client = TestClient(app)
    response = client.get("/manual-queue/details/pub-1")

    assert response.status_code == 200
    assert "Quick dinner idea" in response.text
    assert "#food #easy" in response.text
    assert "Open TikTok Upload" in response.text


def test_manual_queue_media_endpoint_streams_video(tmp_path, monkeypatch) -> None:
    queue_dir = tmp_path / "publish_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    video_path = tmp_path / "demo.mp4"
    video_path.write_bytes(b"fake-video-data")
    _write_queue_job(queue_dir=queue_dir, video_path=video_path)

    monkeypatch.setattr("app.manual_queue.api.QUEUE_DIR", queue_dir)

    client = TestClient(app)
    response = client.get("/manual-queue/api/jobs/pub-1/media")

    assert response.status_code == 200
    assert response.content == b"fake-video-data"
    assert response.headers["content-type"].startswith("video/mp4")
