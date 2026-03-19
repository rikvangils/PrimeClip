from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.responses import FileResponse


ROOT_DIR = Path(__file__).resolve().parents[3]
QUEUE_DIR = ROOT_DIR / "generated" / "publish_queue"

router = APIRouter(prefix="/manual-queue", tags=["manual-queue"])


@dataclass
class QueueJob:
    publication_job_id: str
    rendered_clip_id: str
    platform: str
    scheduled_at: str | None
    caption: str
    title: str
    description: str
    hashtags: list[str]
    render_path: str
    json_file: str


def _derive_title_description_hashtags(caption: str) -> tuple[str, str, list[str]]:
    tags = re.findall(r"#\w+", caption)
    description = re.sub(r"#\w+", "", caption).strip()
    title_source = description or caption or "Untitled clip"
    title = title_source[:80].strip() or "Untitled clip"
    return title, description, tags


def _resolve_video_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (ROOT_DIR / candidate).resolve()


def _read_job(path: Path) -> QueueJob:
    payload = json.loads(path.read_text(encoding="utf-8"))
    caption = str(payload.get("caption", ""))
    title = str(payload.get("title", "")).strip()
    description = str(payload.get("description", "")).strip()
    hashtags = payload.get("hashtags")

    if not title or not description or not isinstance(hashtags, list):
        derived_title, derived_description, derived_hashtags = _derive_title_description_hashtags(caption)
        if not title:
            title = derived_title
        if not description:
            description = derived_description
        if not isinstance(hashtags, list):
            hashtags = derived_hashtags

    publication_job_id = str(payload.get("publication_job_id", "")).strip() or path.stem
    rendered_clip_id = str(payload.get("rendered_clip_id", "")).strip()

    return QueueJob(
        publication_job_id=publication_job_id,
        rendered_clip_id=rendered_clip_id,
        platform=str(payload.get("platform", "")),
        scheduled_at=payload.get("scheduled_at"),
        caption=caption,
        title=title,
        description=description,
        hashtags=[str(tag) for tag in hashtags],
        render_path=str(payload.get("render_path", "")),
        json_file=str(path),
    )


def _load_jobs() -> list[QueueJob]:
    if not QUEUE_DIR.exists():
        return []

    jobs: list[QueueJob] = []
    for file in sorted(QUEUE_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            jobs.append(_read_job(file))
        except Exception:
            continue
    return jobs


def _find_job_or_404(publication_job_id: str) -> QueueJob:
    for job in _load_jobs():
        if job.publication_job_id == publication_job_id:
            return job
    raise HTTPException(status_code=404, detail=f"Manual queue job not found: {publication_job_id}")


@router.get("", response_class=HTMLResponse)
def manual_queue_home() -> HTMLResponse:
    html = """
<!doctype html>
<html lang="nl">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>PeanutClip Manual Queue</title>
    <style>
      :root {
        --bg: #f4f7fb;
        --bg-alt: #eef4fb;
        --bg-grid: rgba(34, 104, 255, 0.07);
        --surface: rgba(255, 255, 255, 0.9);
        --surface-solid: #ffffff;
        --text: #1f2a37;
        --muted: #6b7b90;
        --accent: #2268ff;
        --accent-soft: rgba(34, 104, 255, 0.2);
        --border: rgba(31, 42, 55, 0.12);
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        font-family: "Trebuchet MS", "Segoe UI", Tahoma, sans-serif;
        color: var(--text);
        background:
          linear-gradient(var(--bg-grid) 1px, transparent 1px),
          linear-gradient(90deg, var(--bg-grid) 1px, transparent 1px),
          radial-gradient(circle at 8% 8%, rgba(34, 104, 255, 0.16), transparent 23%),
          radial-gradient(circle at 87% 11%, rgba(125, 163, 255, 0.12), transparent 21%),
          linear-gradient(145deg, var(--bg) 0%, var(--bg-alt) 62%, #f8fbff 100%);
        background-size: 24px 24px, 24px 24px, auto, auto, auto;
      }
      .app {
        width: min(1240px, calc(100% - 24px));
        margin: 0 auto;
        padding: 18px 0 30px;
      }
      .hero {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        gap: 14px;
        margin-bottom: 14px;
      }
      h1 {
        margin: 8px 0 6px;
        font-size: clamp(1.7rem, 3.5vw, 2.8rem);
        letter-spacing: 0.02em;
      }
      .sub {
        margin: 0;
        color: var(--muted);
        max-width: 56ch;
      }
      .status-pill {
        border: 1px solid rgba(22, 179, 127, 0.35);
        color: #0c8d64;
        background: rgba(22, 179, 127, 0.1);
        border-radius: 999px;
        padding: 8px 13px;
        font-size: 0.86rem;
        white-space: nowrap;
        box-shadow: 0 0 0 1px rgba(22, 179, 127, 0.14) inset;
      }
      .layout {
        display: grid;
        grid-template-columns: 350px 1fr;
        gap: 16px;
      }
      .card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 15px;
        backdrop-filter: blur(12px);
        box-shadow:
          0 14px 28px rgba(32, 64, 116, 0.1),
          0 0 0 1px rgba(34, 104, 255, 0.05) inset;
      }
      .card h2 {
        margin: 0 0 10px;
        font-size: 1.15rem;
      }
      .job-list {
        display: grid;
        gap: 10px;
        max-height: calc(100vh - 210px);
        overflow: auto;
        padding-right: 4px;
      }
      .job-btn {
        width: 100%;
        text-align: left;
        border: 1px solid var(--border);
        background: var(--surface-solid);
        border-radius: 13px;
        padding: 11px;
        cursor: pointer;
        transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
      }
      .job-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 18px rgba(34, 104, 255, 0.14);
        border-color: rgba(34, 104, 255, 0.38);
      }
      .job-btn.active {
        border-color: var(--accent);
        box-shadow: 0 0 0 2px var(--accent-soft), 0 10px 20px rgba(34, 104, 255, 0.16);
      }
      .meta {
        color: var(--muted);
        font-size: 0.9rem;
      }
      .player-wrap {
        border-radius: 14px;
        border: 1px solid rgba(34, 104, 255, 0.26);
        padding: 8px;
        background: linear-gradient(145deg, rgba(34, 104, 255, 0.09), rgba(125, 163, 255, 0.06));
        box-shadow: 0 8px 20px rgba(34, 104, 255, 0.1);
      }
      video {
        width: 100%;
        background: #111;
        border-radius: 12px;
      }
      .controls {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
        margin-top: 11px;
      }
      .controls button,
      .actions a {
        border: 1px solid var(--border);
        border-radius: 11px;
        background: var(--surface-solid);
        padding: 8px 11px;
        cursor: pointer;
        text-decoration: none;
        color: var(--text);
        text-align: center;
        transition: transform 130ms ease, border-color 130ms ease, box-shadow 130ms ease;
      }
      .controls button:hover,
      .actions a:hover {
        transform: translateY(-1px);
        border-color: rgba(34, 104, 255, 0.46);
        box-shadow: 0 6px 16px rgba(34, 104, 255, 0.16);
      }
      .actions {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 15px;
      }
      .primary {
        background: linear-gradient(90deg, var(--accent) 0%, #4f87ff 100%);
        color: #ffffff;
        border-color: transparent;
        font-weight: 700;
      }
      .empty {
        color: var(--muted);
        padding: 11px 0;
      }
      @media (max-width: 900px) {
        .hero {
          flex-direction: column;
          align-items: flex-start;
        }
        .layout { grid-template-columns: 1fr; }
        .job-list { max-height: 300px; }
        .controls { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      }

      @keyframes fadeSlide {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }

      .hero,
      .card {
        animation: fadeSlide 420ms ease both;
      }
    </style>
  </head>
  <body>
        --bg: #f4f7fb;
        --bg-alt: #eef4fb;
        --line: rgba(34, 104, 255, 0.08);
        --panel: rgba(255, 255, 255, 0.9);
        --text: #1f2a37;
        --muted: #6b7b90;
        --accent: #2268ff;
      </section>
      <section class="layout">
        <aside class="card">
          <h2>Queue Radar</h2>
          <div id="jobList" class="job-list"></div>
          <p id="emptyNotice" class="empty" style="display:none">Geen clips gevonden in generated/publish_queue.</p>
        </aside>
        <section class="card">
          radial-gradient(circle at 8% 8%, rgba(34, 104, 255, 0.18), transparent 26%),
          radial-gradient(circle at 88% 12%, rgba(125, 163, 255, 0.12), transparent 24%),
          linear-gradient(145deg, var(--bg) 0%, var(--bg-alt) 58%, #f8fbff 100%);
            <video id="clipPlayer" preload="metadata"></video>
          </div>
          <div class="controls">
            <button id="playPauseBtn" type="button">Play</button>
            <button id="volDownBtn" type="button">Volume -</button>
            <button id="volUpBtn" type="button">Volume +</button>
            <button id="muteBtn" type="button">Mute</button>
          </div>
          <div class="actions">
            <a id="detailsBtn" class="primary" href="#">Open titel / beschrijving / hashtags</a>
            <a id="tiktokUploadBtn" target="_blank" rel="noreferrer" href="https://www.tiktok.com/upload">Open TikTok Upload</a>
          </div>
        </section>
      </section>
    </main>
    <script>
      const player = document.getElementById('clipPlayer');
      const listRoot = document.getElementById('jobList');
      const titleEl = document.getElementById('clipTitle');
      const metaEl = document.getElementById('clipMeta');
      const emptyNotice = document.getElementById('emptyNotice');
      const detailsBtn = document.getElementById('detailsBtn');
      const playPauseBtn = document.getElementById('playPauseBtn');
      const volDownBtn = document.getElementById('volDownBtn');
      const volUpBtn = document.getElementById('volUpBtn');
      const muteBtn = document.getElementById('muteBtn');
      let jobs = [];
      let currentId = null;

      function renderList() {
        listRoot.innerHTML = '';
        if (!jobs.length) {
          emptyNotice.style.display = 'block';
          return;
        }
        emptyNotice.style.display = 'none';
        for (const job of jobs) {
          const btn = document.createElement('button');
          btn.className = 'job-btn' + (job.publication_job_id === currentId ? ' active' : '');
          btn.innerHTML = '<strong>' + job.title + '</strong><br><span class="meta">' +
            job.publication_job_id + ' | ' + (job.platform || 'unknown') + '</span>';
          btn.addEventListener('click', () => selectJob(job.publication_job_id));
          listRoot.appendChild(btn);
        }
      }

      function selectJob(publicationJobId) {
        const job = jobs.find((item) => item.publication_job_id === publicationJobId);
        if (!job) return;
        currentId = publicationJobId;
        titleEl.textContent = job.title;
        metaEl.textContent = 'Job: ' + job.publication_job_id + ' | Platform: ' + (job.platform || '-') +
          ' | Schedule: ' + (job.scheduled_at || '-');
        player.src = '/manual-queue/api/jobs/' + encodeURIComponent(job.publication_job_id) + '/media';
        detailsBtn.href = '/manual-queue/details/' + encodeURIComponent(job.publication_job_id);
        renderList();
      }

      async function loadJobs() {
        const response = await fetch('/manual-queue/api/jobs');
        const payload = await response.json();
        jobs = payload.items || [];
        if (jobs.length && !currentId) {
          currentId = jobs[0].publication_job_id;
          selectJob(currentId);
        }
        renderList();
      }

      playPauseBtn.addEventListener('click', () => {
        if (!player.src) return;
        if (player.paused) {
          player.play();
          playPauseBtn.textContent = 'Pause';
        } else {
          player.pause();
          playPauseBtn.textContent = 'Play';
        }
      });

      player.addEventListener('pause', () => { playPauseBtn.textContent = 'Play'; });
      player.addEventListener('play', () => { playPauseBtn.textContent = 'Pause'; });

      volDownBtn.addEventListener('click', () => {
        player.volume = Math.max(0, Number((player.volume - 0.1).toFixed(2)));
        if (player.volume === 0) player.muted = true;
      });
      volUpBtn.addEventListener('click', () => {
        player.muted = false;
        player.volume = Math.min(1, Number((player.volume + 0.1).toFixed(2)));
      });
      muteBtn.addEventListener('click', () => {
        player.muted = !player.muted;
        muteBtn.textContent = player.muted ? 'Unmute' : 'Mute';
      });

      loadJobs();
    </script>
  </body>
</html>
"""
    return HTMLResponse(content=html)


@router.get("/details/{publication_job_id}", response_class=HTMLResponse)
def manual_queue_details(publication_job_id: str) -> HTMLResponse:
    job = _find_job_or_404(publication_job_id)
    hashtags_text = " ".join(job.hashtags)
    combined_caption = (job.description + " " + hashtags_text).strip() or job.caption
    tiktok_web_upload = "https://www.tiktok.com/upload"

    html = f"""
<!doctype html>
<html lang="nl">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Clip details - {job.publication_job_id}</title>
    <style>
      :root {{
        --bg: #060d17;
        --bg-alt: #0c172b;
        --line: rgba(110, 184, 255, 0.08);
        --panel: rgba(12, 24, 40, 0.7);
        --text: #e8f4ff;
        --muted: #9fbbd8;
        --accent: #54c7ff;
      }}
      body {{
        margin: 0;
        color: var(--text);
        font-family: \"Trebuchet MS\", \"Segoe UI\", Tahoma, sans-serif;
        background:
          linear-gradient(var(--line) 1px, transparent 1px),
          linear-gradient(90deg, var(--line) 1px, transparent 1px),
          radial-gradient(circle at 8% 8%, rgba(84, 199, 255, 0.2), transparent 26%),
          radial-gradient(circle at 88% 12%, rgba(102, 255, 214, 0.16), transparent 24%),
          linear-gradient(145deg, var(--bg) 0%, var(--bg-alt) 58%, #091221 100%);
        background-size: 24px 24px, 24px 24px, auto, auto;
      }}
      .wrap {{ width: min(980px, calc(100% - 24px)); margin: 0 auto; padding: 20px 0 30px; }}
      .card {{
        background: var(--panel);
        border: 1px solid rgba(31, 42, 55, 0.12);
        border-radius: 18px;
        padding: 17px;
        backdrop-filter: blur(10px);
        box-shadow:
          0 14px 28px rgba(32, 64, 116, 0.1),
          0 0 0 1px rgba(34, 104, 255, 0.05) inset;
      }}
      h1 {{ margin: 0 0 8px; letter-spacing: 0.02em; }}
      .muted {{ color: var(--muted); }}
      textarea {{
        width: 100%;
        min-height: 126px;
        font-family: Consolas, \"Courier New\", monospace;
        font-size: 0.92rem;
        border: 1px solid rgba(31, 42, 55, 0.16);
        border-radius: 12px;
        padding: 10px;
        background: #f8fbff;
        color: var(--text);
      }}
      .row {{ display: grid; gap: 12px; grid-template-columns: 1fr 1fr; }}
      .actions {{ margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap; }}
      button, a {{
        border: 1px solid rgba(31, 42, 55, 0.16);
        border-radius: 11px;
        padding: 8px 12px;
        background: #ffffff;
        text-decoration: none;
        color: var(--text);
        cursor: pointer;
      }}
      .primary {{
        background: linear-gradient(90deg, var(--accent) 0%, #4f87ff 100%);
        color: #ffffff;
        border-color: transparent;
        font-weight: 700;
      }}
      .back {{ color: var(--accent); text-decoration: none; font-weight: 600; }}
      @media (max-width: 800px) {{ .row {{ grid-template-columns: 1fr; }} }}
    </style>
  </head>
  <body>
    <main class="wrap">
      <a class="back" href="/manual-queue">Terug naar queue</a>
      <section class="card" style="margin-top:10px">
        <h1>{job.title}</h1>
        <p class="muted">Job: {job.publication_job_id} | Platform: {job.platform or '-'} | Video: {job.render_path}</p>
        <div class="row">
          <div>
            <h3>Titel</h3>
            <textarea id="titleText" readonly>{job.title}</textarea>
          </div>
          <div>
            <h3>Hashtags</h3>
            <textarea id="hashtagsText" readonly>{hashtags_text}</textarea>
          </div>
        </div>
        <div style="margin-top:12px">
          <h3>Beschrijving + hashtags (klaar om te plakken)</h3>
          <textarea id="captionText" readonly>{combined_caption}</textarea>
        </div>
        <div class="actions">
          <button type="button" onclick="copyField('titleText')">Kopieer titel</button>
          <button type="button" onclick="copyField('captionText')">Kopieer beschrijving + hashtags</button>
          <a class="primary" href="{tiktok_web_upload}" target="_blank" rel="noreferrer">Open TikTok Upload</a>
        </div>
      </section>
    </main>
    <script>
      async function copyField(id) {{
        const text = document.getElementById(id).value;
        await navigator.clipboard.writeText(text);
      }}
    </script>
  </body>
</html>
"""
    return HTMLResponse(content=html)


@router.get("/api/jobs", response_class=JSONResponse)
def manual_queue_jobs() -> JSONResponse:
    items = []
    for job in _load_jobs():
        items.append(
            {
                "publication_job_id": job.publication_job_id,
                "rendered_clip_id": job.rendered_clip_id,
                "platform": job.platform,
                "scheduled_at": job.scheduled_at,
                "title": job.title,
                "description": job.description,
                "hashtags": job.hashtags,
                "caption": job.caption,
                "render_path": job.render_path,
                "details_url": f"/manual-queue/details/{quote(job.publication_job_id)}",
            }
        )
    return JSONResponse({"items": items})


@router.get("/api/jobs/{publication_job_id}", response_class=JSONResponse)
def manual_queue_job(publication_job_id: str) -> JSONResponse:
    job = _find_job_or_404(publication_job_id)
    payload = {
        "publication_job_id": job.publication_job_id,
        "rendered_clip_id": job.rendered_clip_id,
        "platform": job.platform,
        "scheduled_at": job.scheduled_at,
        "title": job.title,
        "description": job.description,
        "hashtags": job.hashtags,
        "caption": job.caption,
        "render_path": job.render_path,
        "details_url": f"/manual-queue/details/{quote(job.publication_job_id)}",
        "media_url": f"/manual-queue/api/jobs/{quote(job.publication_job_id)}/media",
    }
    return JSONResponse(payload)


@router.get("/api/jobs/{publication_job_id}/media")
def manual_queue_media(publication_job_id: str) -> FileResponse:
    job = _find_job_or_404(publication_job_id)
    video_path = _resolve_video_path(job.render_path)
    if not video_path.exists() or not video_path.is_file():
        raise HTTPException(status_code=404, detail=f"Video file not found: {video_path}")

    return FileResponse(path=video_path, media_type="video/mp4", filename=video_path.name)
