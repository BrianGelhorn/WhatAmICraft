#!/usr/bin/env python3
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from target_inventory import video_directories

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out/context-snapshot.md"


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def env_value(key: str) -> str:
    for name in (".env", ".env.local"):
        path = ROOT / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return os.getenv(key, "")


def main() -> int:
    bank = read_json(ROOT / "data/quiz-copy-episodes.json", {"episodes": []})
    used_targets = read_json(ROOT / "data/used-targets.json", {"target_ids": [], "targets": []})
    queue = read_json(ROOT / "out/publishing-queue.json", {"items": []}).get("items", [])
    state = read_json(ROOT / "out/publishing-state.json", {"videos": {}}).get("videos", {})
    config = read_json(ROOT / "data/publishing.json", {})
    videos = sorted({path for directory in video_directories() for path in directory.glob("*.mp4")})
    audio_manifests = sorted((ROOT / "public/audio/quiz-copy").glob("*/manifest.json"))
    pending = [item for item in queue if item.get("status") == "pending"]
    failed = [item for item in queue if item.get("status") == "failed"]
    generation = config.get("generation", {})
    schedule = config.get("schedule", {})
    public_url = config.get("platforms", {}).get("instagram", {}).get("publicVideoBaseUrl", "")
    lines = [
        "# MinecraftQuizGuesser snapshot",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Server",
        "",
        "- Debian path: `/home/brian/MinecraftQuizGuesser`",
        "- SSH: `brian@192.168.0.106`",
        "- Dashboard: `https://what-am-i-craft.tail6cc348.ts.net:8443/`",
        f"- Public videos: `{public_url or env_value('PUBLIC_VIDEO_BASE_URL') or 'not configured'}`",
        "- Docker services: `dashboard`, `bot`, `publisher-worker`, `media`",
        "",
        "## Current counts",
        "",
        f"- Episodes in JSON: {len(bank.get('episodes', []))}",
        f"- Rendered MP4s: {len(videos)}",
        f"- Audio cache manifests: {len(audio_manifests)}",
        f"- Approved queue: {len(pending)}",
        f"- Published records: {len(state)}",
        f"- Failed queue items: {len(failed)}",
        f"- Reserved target objects: {len(used_targets.get('target_ids', []))}",
        "- Never reuse a target listed in `data/used-targets.json`.",
        "",
        "## Rules",
        "",
        f"- Publishing enabled: {schedule.get('enabled')}",
        f"- Publish interval minutes: {schedule.get('intervalMinutes')}",
        f"- Generation enabled: {generation.get('enabled')}",
        f"- Target approved/candidate stock: {generation.get('targetStock')}",
        f"- Low stock alert threshold: {generation.get('lowStockThreshold')}",
        "- Publisher should post max 1 video per interval.",
        "- Producer should not generate while publishing is active.",
        "",
        "## Useful commands",
        "",
        "```bash",
        "cd /home/brian/MinecraftQuizGuesser",
        "python3 scripts/doctor.py",
        "python3 scripts/backup_state.py",
        "python3 scripts/context_snapshot.py",
        "docker compose ps",
        "docker compose logs --tail=80 dashboard bot publisher-worker",
        "docker compose run --rm producer --all --dry-run",
        "sudo systemctl restart minecraft-quiz.service",
        "```",
        "",
        "## Notes for Codex",
        "",
        "- First read `docs/ai-context/current-architecture.md`, `operations.md`, `clue-rules.md`, and `dashboard-map.md`.",
        "- Before generating clues, read `data/used-targets.json`; its `target_ids` list contains every object already used by the quiz bank or a rendered video.",
        "- Refresh that list with `python3 scripts/target_inventory.py` after changing episode data.",
        "- Prefer edits locally, then copy touched files to Debian and rebuild `minecraft-quiz-guesser:local`.",
        "- Do not run long Remotion renders unless explicitly asked.",
        "- Secrets live in `.env.local`, Docker secrets, or `data/publishing-secrets.json`; never print them.",
        "- Generated videos live on the USB disk through the Docker mount at `/app/out/episodes`.",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"snapshot: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
