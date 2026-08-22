#!/usr/bin/env python3
"""Behavior check for automatic format selection and render command recovery."""

from __future__ import annotations

import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import publish_worker as worker
import produce_quiz_copy as producer

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    fixture = ROOT / "out/test-automatic-rendering"
    shutil.rmtree(fixture, ignore_errors=True)
    fixture.mkdir(parents=True)
    now = datetime.now(timezone.utc)
    config = {
        "schedule": {"enabled": True},
        "generation": {
            "enabled": True,
            "intervalMinutes": 30,
            "publishGuardMinutes": 90,
            "lowStockThreshold": 5,
            "targetStock": 8,
            "formats": {"clues": {"enabled": True, "priority": 1}},
        },
    }
    stock = {
        "pending": [],
        "candidates": [],
        "stock": [],
        "formats": {
            "clues": {
                "pending": [],
                "candidates": [],
                "missing": ["mc-02", "mc-03"],
            },
        },
    }
    commands: list[list[str]] = []
    schedules: list[str] = []
    original = {
        "log_dir": worker.LOG_DIR,
        "generation_schedule": worker.load_generation_schedule,
        "publish_schedule": worker.load_schedule,
        "inventory": worker.inventory,
        "run_logged": worker.run_logged,
        "save_schedule": worker.save_generation_schedule,
        "active_template_version": worker.active_template_version,
        "release_version": worker.release_version,
    }

    def run_logged(command: list[str], *_args: object) -> SimpleNamespace:
        commands.append(command)
        return SimpleNamespace(returncode=1 if len(commands) == 1 else 0)

    try:
        worker.LOG_DIR = fixture / "logs"
        worker.load_generation_schedule = lambda: {"nextRunAt": (now - timedelta(minutes=1)).isoformat()}
        worker.load_schedule = lambda: {"nextRunAt": (now + timedelta(hours=2)).isoformat()}
        worker.inventory = lambda: {"stock": []}
        worker.run_logged = run_logged
        worker.save_generation_schedule = schedules.append

        worker.maybe_generate(config, stock)

        assert len(commands) == 2
        assert all(str(ROOT / "scripts/produce_quiz_copy.py") in command for command in commands)
        assert all("--render" in command and "--generate-audio" in command for command in commands)
        assert commands[0][-1] == "mc-02"
        assert commands[1][-1] == "mc-03"
        assert schedules and schedules[0]
        commands.clear()
        worker.active_template_version = lambda: "old-release"
        worker.release_version = lambda: "new-release"
        worker.maybe_generate(config, stock)
        assert not commands
        assert schedules[-1]
    finally:
        for name, value in original.items():
            setattr(worker, {
                "log_dir": "LOG_DIR",
                "generation_schedule": "load_generation_schedule",
                "publish_schedule": "load_schedule",
                "inventory": "inventory",
                "run_logged": "run_logged",
                "save_schedule": "save_generation_schedule",
                "active_template_version": "active_template_version",
                "release_version": "release_version",
            }[name], value)
        shutil.rmtree(fixture, ignore_errors=True)

    render_calls: list[tuple[list[str], dict]] = []
    original_render_run = producer.subprocess.run
    original_render_env = {
        key: os.environ.pop(key, None)
        for key in ("REMOTION_CONCURRENCY", "REMOTION_RENDER_TIMEOUT_SECONDS")
    }
    try:
        producer.subprocess.run = lambda command, **kwargs: render_calls.append((command, kwargs))  # type: ignore[assignment]
        producer.render({"id": "mc-test", "answer": {"id": "stone"}})
        command, options = render_calls[0]
        assert "--concurrency=1" in command
        props = next(argument for argument in command if argument.startswith("--props="))
        assert props.startswith("--props=out/render-jobs/mc-test-stone/")
        assert (ROOT / props.removeprefix("--props=")).is_file()
        assert options["timeout"] == 1800
    finally:
        producer.subprocess.run = original_render_run
        for key, value in original_render_env.items():
            if value is not None:
                os.environ[key] = value
        shutil.rmtree(ROOT / "out/render-jobs/mc-test-stone", ignore_errors=True)

    print("ok: automatic rendering selects missing episodes and continues after a failed render")


if __name__ == "__main__":
    main()
