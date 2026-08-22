#!/usr/bin/env python3
"""Ensure every GitHub Actions job uses the mini PC self-hosted runner."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "runs-on: [self-hosted, linux, x64, whatamicraft-mini-pc]"


def main() -> None:
    workflows = sorted((ROOT / ".github/workflows").glob("*.yml"))
    runner_lines = []
    for workflow in workflows:
        runner_lines.extend(
            f"{workflow.name}:{line.strip()}"
            for line in workflow.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("runs-on:")
        )
    assert workflows and runner_lines
    assert all(line.endswith(EXPECTED) for line in runner_lines), runner_lines
    print(f"ok: {len(runner_lines)} CI/CD jobs use the mini PC self-hosted runner")


if __name__ == "__main__":
    main()
