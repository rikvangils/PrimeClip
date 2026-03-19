from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = ROOT / "generated" / "publish_queue"


def _read_job(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "file": str(path),
        "publication_job_id": str(payload.get("publication_job_id", "")),
        "platform": str(payload.get("platform", "")),
        "scheduled_at": str(payload.get("scheduled_at", "")),
        "caption": str(payload.get("caption", "")),
        "render_path": str(payload.get("render_path", "")),
    }


def main() -> None:
    print("PeanutClip - Manual Publish Checklist")
    print("=" * 40)

    if not QUEUE_DIR.exists():
        print(f"Queue map bestaat nog niet: {QUEUE_DIR}")
        print("Plan eerst een clip met PEANUTCLIP_PUBLISH_PROVIDER=manual.")
        return

    files = sorted(QUEUE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print("Geen pending publicaties gevonden.")
        print(f"Map: {QUEUE_DIR}")
        return

    for index, file in enumerate(files, start=1):
        try:
            job = _read_job(file)
        except Exception as exc:  # pragma: no cover
            print(f"\n[{index}] Kon bestand niet lezen: {file}")
            print(f"    Fout: {exc}")
            continue

        print(f"\n[{index}] Publication job: {job['publication_job_id']}")
        print(f"    Platform   : {job['platform']}")
        print(f"    Schedule   : {job['scheduled_at'] or '(none)'}")
        print(f"    Video path : {job['render_path']}")
        print(f"    Caption    : {job['caption']}")
        print(f"    JSON file  : {job['file']}")
        print("    Actie      : Upload video + caption handmatig in TikTok")


if __name__ == "__main__":
    main()
