#!/usr/bin/env python3
"""Prove staging can be seeded without using repository runtime state."""

from __future__ import annotations

import shutil
from pathlib import Path

from ci.prepare_staging import ROOT, prepare_runtime


def main() -> None:
    runtime = ROOT / "staging/.test-runtime"
    shutil.rmtree(runtime, ignore_errors=True)
    try:
        prepared = prepare_runtime(runtime)
        assert prepared == runtime.resolve()
        assert (runtime / "data/quiz-copy-episodes.json").is_file()
        assert (runtime / "data/new-clues-20260815/manifest.json").is_file()
        fixture = runtime / "out/episodes/mc-ci-test.mp4"
        assert fixture.read_bytes() == b"whatamicraft-ci-video"
        assert not (runtime / "out/app-state.sqlite3").exists()
    finally:
        shutil.rmtree(runtime, ignore_errors=True)
    print("ok: staging runtime is seeded in an isolated directory")


if __name__ == "__main__":
    main()
