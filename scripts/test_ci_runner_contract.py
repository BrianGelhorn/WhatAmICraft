#!/usr/bin/env python3
"""Ensure every GitHub Actions job uses the mini PC self-hosted runner."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "runs-on: [self-hosted, linux, x64]"


def main() -> None:
    workflows = sorted((ROOT / ".github/workflows").glob("*.yml"))
    runner_lines = []
    for workflow in workflows:
        content = workflow.read_text(encoding="utf-8")
        assert "actions/setup-python" not in content, workflow.name
        runner_lines.extend(
            f"{workflow.name}:{line.strip()}"
            for line in workflow.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("runs-on:")
        )
    assert workflows and runner_lines
    assert all(line.endswith(EXPECTED) for line in runner_lines), runner_lines
    action = (ROOT / ".github/actions/runner-python/action.yml").read_text(encoding="utf-8")
    assert "python3 --version" in action and "sys.version_info >= (3, 12)" in action
    print(f"ok: {len(runner_lines)} CI/CD jobs use the mini PC self-hosted runner")


if __name__ == "__main__":
    main()
