#!/usr/bin/env python3
"""Keep a readable, persistent list of targets already used by the project."""

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/used-targets.json"


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def add_target(records, target_id, display_name=None, kind=None, source=None, episode_id=None, video_file=None):
    record = records[target_id]
    record["id"] = target_id
    if display_name:
        record["display_name"] = display_name
    if kind:
        record["kind"] = kind
    if source:
        record["sources"].add(source)
    if episode_id:
        record["episode_ids"].add(episode_id)
    if video_file:
        record["video_files"].add(video_file)


def video_directories() -> list[Path]:
    directories = [ROOT / "out/episodes"]
    configured = os.getenv("VIDEO_STORAGE_PATH", "")
    for path in (ROOT / ".env", ROOT / ".env.local"):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("VIDEO_STORAGE_PATH="):
                configured = line.split("=", 1)[1].strip().strip("'\"")
    if configured:
        directories.append(Path(configured).expanduser())
    return list(dict.fromkeys(directories))


def refresh() -> dict:
    records = defaultdict(lambda: {
        "id": "",
        "display_name": "",
        "kind": "",
        "sources": set(),
        "episode_ids": set(),
        "video_files": set(),
    })

    # Keep history even when old videos live on a different mounted disk.
    previous = read_json(OUTPUT, {"targets": []})
    for item in previous.get("targets", []):
        add_target(
            records,
            item.get("id"),
            item.get("display_name"),
            item.get("kind"),
        )
        record = records[item.get("id")]
        record["sources"].update(item.get("sources", []))
        record["episode_ids"].update(item.get("episode_ids", []))
        record["video_files"].update(item.get("video_files", []))

    bank = read_json(ROOT / "data/quiz-copy-episodes.json", {"episodes": []})
    for episode in bank.get("episodes", []):
        answer = episode.get("answer", {})
        add_target(
            records,
            answer.get("id"),
            answer.get("displayName"),
            answer.get("guessType", "").lower(),
            "quiz_bank",
            episode.get("id"),
        )

    for video_dir in video_directories():
        for path in video_dir.glob("*.mp4"):
            parts = path.stem.split("-", 2)
            if len(parts) == 3:
                add_target(records, parts[2], source="rendered_video", video_file=path.name)

    targets = []
    for target_id in sorted(records):
        record = records[target_id]
        targets.append({
            "id": target_id,
            "display_name": record["display_name"] or target_id.replace("_", " ").title(),
            "kind": record["kind"] or "unknown",
            "sources": sorted(record["sources"]),
            "episode_ids": sorted(record["episode_ids"]),
            "video_files": sorted(record["video_files"]),
        })

    result = {
        "schema_version": 1,
        "edition": bank.get("episodes", [{}])[0].get("answer", {}).get("edition", "java"),
        "version": bank.get("episodes", [{}])[0].get("answer", {}).get("version", "1.21.5"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_ids": [item["id"] for item in targets],
        "targets": targets,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = refresh()
    print(f"used targets: {len(result['target_ids'])}")
    print(OUTPUT)
