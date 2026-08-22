#!/usr/bin/env python3
"""Create the isolated, persistent filesystem used by staging."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGING_ROOT = ROOT / "staging"
DEFAULT_RUNTIME = STAGING_ROOT / "runtime"
STATE_FILES = (
    "quiz-copy-episodes.json",
    "used-targets.json",
    "publishing.json",
    "pending-hint-regenerations.json",
    "music-library.json",
)


def prepare_runtime(runtime: Path, *, reset: bool = False) -> Path:
    runtime = runtime.resolve()
    if reset and runtime.exists():
        shutil.rmtree(runtime)

    data = runtime / "data"
    out = runtime / "out"
    (data / "new-clues-20260815").mkdir(parents=True, exist_ok=True)
    (data / "clues/inbox").mkdir(parents=True, exist_ok=True)
    (out / "episodes").mkdir(parents=True, exist_ok=True)
    (out / "thumbnails").mkdir(parents=True, exist_ok=True)
    (out / "analytics").mkdir(parents=True, exist_ok=True)
    (out / "monitor").mkdir(parents=True, exist_ok=True)
    (runtime / "backups").mkdir(parents=True, exist_ok=True)

    for name in STATE_FILES:
        source = ROOT / "data" / name
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = data / name
        if reset or not destination.exists():
            shutil.copy2(source, destination)

    source_clues = ROOT / "data/new-clues-20260815"
    destination_clues = data / "new-clues-20260815"
    shutil.copytree(source_clues, destination_clues, dirs_exist_ok=True)

    fixture = out / "episodes/mc-ci-test.mp4"
    if reset or not fixture.exists():
        fixture.write_bytes(b"whatamicraft-ci-video")
    return runtime


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    runtime_path = args.runtime_root.resolve()
    allowed_roots = [STAGING_ROOT.resolve()]
    if runner_temp := os.environ.get("RUNNER_TEMP"):
        allowed_roots.append(Path(runner_temp).resolve())
    if not any(root == runtime_path or root in runtime_path.parents for root in allowed_roots):
        raise SystemExit("staging runtime must live below staging/ or RUNNER_TEMP")
    runtime = prepare_runtime(runtime_path, reset=args.reset)
    print(f"prepared isolated staging runtime: {runtime}")


if __name__ == "__main__":
    main()
