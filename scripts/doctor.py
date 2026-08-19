#!/usr/bin/env python3
import json
import os
import shutil
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from publishing.settings import credential_status, load_config, load_generation_schedule, load_schedule
from review.storage import pending_hints_items, publishing_state, queue_items, read_json, state_db_path

ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "data/quiz-copy-episodes.json"
LOG_DIR = ROOT / "out/logs"


def load_env_files() -> None:
    for path in (ROOT / ".env", ROOT / ".env.local"):
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def output_dir() -> Path:
    configured = os.getenv("VIDEO_STORAGE_PATH")
    return Path(configured) if configured else ROOT / "out/episodes"


def ok_socket(host: str, port: int, timeout: int = 3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def run(command: list[str], timeout: int = 10) -> str:
    try:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout, check=False)
        return (result.stdout or result.stderr).strip()
    except Exception as error:
        return f"{command[0]}: {error}"


def tail(path: Path, lines: int = 8) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:]


def main() -> int:
    load_env_files()
    output = output_dir()
    config = load_config()
    queue = queue_items()
    failed = [item for item in queue if item.get("status") == "failed"]
    pending = [item for item in queue if item.get("status") == "pending"]
    published = publishing_state()["videos"]
    episodes = read_json(BANK_PATH, {"episodes": []})["episodes"]
    videos = list(output.glob("*.mp4"))
    video_ids = {path.name.split("-", 2)[0] + "-" + path.name.split("-", 2)[1] for path in videos if path.name.startswith("mc-")}
    candidates = video_ids - set(published) - {item["episodeId"] for item in pending}
    disk = shutil.disk_usage(output if output.exists() else ROOT)
    credentials = credential_status(config)
    db = state_db_path()

    print("Minecraft Quiz Doctor")
    print(f"Checked: {datetime.now(timezone.utc).isoformat()}")
    print(f"Root: {ROOT}")
    print()
    print("Core")
    print(f"- Internet: {'ok' if ok_socket('1.1.1.1', 53) else 'fail'}")
    print(f"- Dashboard local: {'ok' if ok_socket('127.0.0.1', 8787) else 'fail'}")
    print(f"- Public media local: {'ok' if ok_socket('127.0.0.1', 8080) else 'fail'}")
    print(f"- Video path: {output}")
    print(f"- SQLite: {'ok' if db.exists() else 'missing'} ({db}, {round(db.stat().st_size / 1024, 1) if db.exists() else 0} KB)")
    print(f"- Disk: {round(disk.free / 1024**3, 1)} GB free / {round(disk.total / 1024**3, 1)} GB total")
    print()
    print("Content")
    print(f"- Episodes: {len(episodes)}")
    print(f"- Rendered videos: {len(videos)}")
    print(f"- Published videos: {len(published)}")
    print(f"- Queue: {len(queue)} total, {len(pending)} pending, {len(failed)} failed")
    print(f"- Review candidates: {len(candidates)}")
    print(f"- Pending hints: {len(pending_hints_items())}")
    print()
    print("Schedule")
    print(f"- Publishing enabled: {config['schedule']['enabled']} every {config['schedule']['intervalMinutes']} min")
    print(f"- Next publish: {load_schedule().get('nextRunAt')}")
    print(f"- Generation enabled: {config['generation']['enabled']} every {config['generation']['intervalMinutes']} min")
    print(f"- Next generation: {load_generation_schedule().get('nextRunAt')}")
    print()
    print("Credentials")
    for name, ready in credentials.items():
        print(f"- {name}: {'ok' if ready else 'missing'}")
    if failed:
        print()
        print("Failed queue")
        for item in failed[-8:]:
            print(f"- {item['episodeId']}: {item.get('error', item.get('status'))}")
    print()
    print("Docker")
    print(run(["docker", "compose", "ps"], timeout=15) or "docker compose ps: no output")
    print()
    print("Tailscale")
    print(run(["tailscale", "status", "--self"], timeout=10) or "tailscale: no output")
    print()
    print("Recent logs")
    paths = sorted(LOG_DIR.glob("*.log")) + sorted((LOG_DIR / "jobs").glob("*.log")) if LOG_DIR.exists() else []
    for path in paths[-6:]:
        print(f"[{path.relative_to(ROOT)}]")
        for line in tail(path):
            print(line)
        print()
    print(json.dumps({"ok": True, "pending": len(pending), "failed": len(failed), "freeGb": round(disk.free / 1024**3, 1)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
