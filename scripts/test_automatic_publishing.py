#!/usr/bin/env python3
"""Black-box checks for one automatic publish tick and its retry path."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import publish  # noqa: E402
import publish_worker as worker  # noqa: E402


def check_generation_lane_guard() -> None:
    fixture = ROOT / "out/test-generation-schedule"
    shutil.rmtree(fixture, ignore_errors=True)
    fixture.mkdir(parents=True)
    config = {
        "schedule": {"enabled": False},
        "generation": {
            "enabled": True,
            "intervalMinutes": 180,
            "targetStock": 8,
            "lowStockThreshold": 5,
            "publishGuardMinutes": 90,
        },
    }
    saved: list[str] = []
    original = {
        "log_dir": worker.LOG_DIR,
        "load_generation_schedule": worker.load_generation_schedule,
        "save_generation_schedule": worker.save_generation_schedule,
        "read_job": worker.read_job,
    }
    try:
        worker.LOG_DIR = fixture
        worker.load_generation_schedule = lambda: {"nextRunAt": "2026-01-01T00:00:00+00:00"}
        worker.save_generation_schedule = saved.append
        worker.read_job = lambda _lane: {"status": "running"}
        worker.maybe_generate(config, {"pending": [], "candidates": [], "formats": {}})
        assert len(saved) == 1
        assert datetime.fromisoformat(saved[0]) > datetime.now(timezone.utc)
    finally:
        worker.LOG_DIR = original["log_dir"]
        worker.load_generation_schedule = original["load_generation_schedule"]
        worker.save_generation_schedule = original["save_generation_schedule"]
        worker.read_job = original["read_job"]
        shutil.rmtree(fixture, ignore_errors=True)


def main() -> None:
    check_generation_lane_guard()
    fixture = ROOT / "out/test-automatic-publishing"
    shutil.rmtree(fixture, ignore_errors=True)
    output = fixture / "out/episodes"
    output.mkdir(parents=True)
    video = output / "mc-01-stone.mp4"
    video.write_bytes(b"automatic-publish-video")
    episode = {
        "id": "mc-01",
        "target": {"id": "stone", "kind": "item", "display_name": "Stone"},
    }
    config = {
        "title": "Guess {kind}",
        "caption": "Can you guess it?",
        "hashtags": ["minecraft", "shorts"],
        "schedule": {"enabled": True, "intervalMinutes": 30},
        "generation": {"enabled": False, "lowStockThreshold": 5},
    }
    queue = {"ids": ["mc-01"], "status": "pending", "error": None}
    state = {"videos": {}}
    provider_calls: list[tuple[str, str, bytes]] = []
    saved_schedules: list[str] = []
    commands: list[list[str]] = []
    notifications: list[str] = []
    original_publish = {
        "output": publish.OUTPUT_DIR,
        "episodes": publish.episodes,
        "config": publish.load_config,
        "runtime": publish.apply_runtime,
        "platforms": publish.enabled_platforms,
        "queue_ids": publish.pending_queue_ids,
        "state": publish.publishing_state,
        "save": publish.save_published_platform,
        "queue_status": publish.set_queue_status,
        "publishers": publish.PUBLISHERS,
    }
    original_worker = {
        "config": worker.load_config,
        "runtime": worker.apply_runtime,
        "schedule": worker.load_schedule,
        "save_schedule": worker.save_schedule,
        "generation_schedule": worker.load_generation_schedule,
        "episodes": worker.episodes,
        "video_for": worker.video_for,
        "names": worker.current_template_video_names,
        "state": worker.publishing_state,
        "queue_ids": worker.pending_queue_ids,
        "run_logged": worker.run_logged,
        "alert": worker.alert_low_stock,
        "maybe_generate": worker.maybe_generate,
        "notify": worker.notify,
    }
    original_sleep = worker.time.sleep

    def set_queue_status(_episode_id: str, status: str, error: str | None = None) -> None:
        queue.update(status=status, error=error)
        if status == "pending":
            queue["ids"] = ["mc-01"]
        else:
            queue["ids"] = []

    def save_platform(episode_id: str, fingerprint: str, platform: str, payload: dict) -> None:
        state["videos"].setdefault(episode_id, {"sha256": fingerprint, "platforms": {}})["platforms"][platform] = payload

    def run_logged(command: list[str], *_args: object) -> SimpleNamespace:
        commands.append(command)
        args = argparse.Namespace(episode=None, queue=True, all=False, platform=None, limit=1, force=False, dry_run=False)
        return SimpleNamespace(returncode=publish.run(args))

    def stop_after_tick(_seconds: float) -> None:
        raise KeyboardInterrupt

    try:
        publish.OUTPUT_DIR = output
        publish.episodes = lambda: [episode]
        publish.load_config = lambda: {**config, "platforms": {"fake": {"enabled": True}}}
        publish.apply_runtime = lambda _config: None
        publish.enabled_platforms = lambda _config: ["fake"]
        publish.pending_queue_ids = lambda: list(queue["ids"])
        publish.publishing_state = lambda: state
        publish.save_published_platform = save_platform
        publish.set_queue_status = set_queue_status

        def provider(item: publish.PublishRequest) -> dict:
            provider_calls.append((item.title, item.description, item.video.read_bytes()))
            return {"id": "fake-post-01", "url": "https://example.test/fake-post-01"}

        publish.PUBLISHERS = {"fake": provider}
        worker.load_config = lambda: config
        worker.apply_runtime = lambda _config: None
        worker.load_schedule = lambda: {"nextRunAt": datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat()}
        worker.save_schedule = lambda value: saved_schedules.append(value)
        worker.load_generation_schedule = lambda: {"nextRunAt": None}
        worker.episodes = lambda: [episode]
        worker.video_for = lambda _episode: video
        worker.current_template_video_names = lambda: {video.name}
        worker.publishing_state = lambda: state
        worker.pending_queue_ids = lambda: list(queue["ids"])
        worker.run_logged = run_logged
        worker.alert_low_stock = lambda *_args: None
        worker.maybe_generate = lambda *_args: None
        worker.notify = notifications.append
        worker.time.sleep = stop_after_tick

        try:
            worker.main()
        except KeyboardInterrupt:
            pass

        assert commands and "--queue" in commands[0] and "--limit" in commands[0]
        assert provider_calls == [("Guess Item", "Can you guess it?\n\n#minecraft #shorts", b"automatic-publish-video")]
        assert state["videos"]["mc-01"]["platforms"]["fake"]["id"] == "fake-post-01"
        assert queue == {"ids": [], "status": "completed", "error": None}
        assert saved_schedules and saved_schedules[0]

        queue.update(ids=["mc-01"], status="pending", error=None)
        state["videos"] = {}
        provider_calls.clear()
        commands.clear()

        def failing_provider(_item: publish.PublishRequest) -> dict:
            raise RuntimeError("fake provider unavailable")

        publish.PUBLISHERS = {"fake": failing_provider}
        try:
            worker.main()
        except KeyboardInterrupt:
            pass
        assert queue["status"] == "failed"
        assert "fake provider unavailable" in (queue["error"] or "")
        assert len(saved_schedules) == 2
    finally:
        for name, value in original_publish.items():
            setattr(publish, {"output": "OUTPUT_DIR", "episodes": "episodes", "config": "load_config", "runtime": "apply_runtime", "platforms": "enabled_platforms", "queue_ids": "pending_queue_ids", "state": "publishing_state", "save": "save_published_platform", "queue_status": "set_queue_status", "publishers": "PUBLISHERS"}[name], value)
        for name, value in original_worker.items():
            setattr(worker, {"config": "load_config", "runtime": "apply_runtime", "schedule": "load_schedule", "save_schedule": "save_schedule", "generation_schedule": "load_generation_schedule", "episodes": "episodes", "video_for": "video_for", "names": "current_template_video_names", "state": "publishing_state", "queue_ids": "pending_queue_ids", "run_logged": "run_logged", "alert": "alert_low_stock", "maybe_generate": "maybe_generate", "notify": "notify"}[name], value)
        worker.time.sleep = original_sleep
        shutil.rmtree(fixture, ignore_errors=True)

    print("ok: automatic publishing completes and retries failed provider calls")


if __name__ == "__main__":
    main()
