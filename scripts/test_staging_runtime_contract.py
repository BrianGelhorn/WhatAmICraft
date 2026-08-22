#!/usr/bin/env python3
"""Prove the staging CLI accepts only its isolated runtime roots."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "scripts/ci/prepare_staging.py"


def main() -> None:
    runner_temp = ROOT / "staging"
    runtime = runner_temp / ".test-runtime-contract"
    shutil.rmtree(runtime, ignore_errors=True)
    try:
        environment = os.environ.copy()
        environment["RUNNER_TEMP"] = str(runner_temp)
        allowed = subprocess.run(
            [sys.executable, str(PREPARE), "--runtime-root", str(runtime), "--reset"],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
        )
        assert allowed.returncode == 0, allowed.stderr
        assert (runtime / "out/episodes/mc-ci-test.mp4").is_file()

        rejected = subprocess.run(
            [sys.executable, str(PREPARE), "--runtime-root", str(ROOT / ".test-runtime-outside"), "--reset"],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
        )
        assert rejected.returncode != 0
        assert "RUNNER_TEMP" in rejected.stderr
    finally:
        shutil.rmtree(runtime, ignore_errors=True)
    print("ok: staging runtime is isolated to staging or RUNNER_TEMP")


if __name__ == "__main__":
    main()
