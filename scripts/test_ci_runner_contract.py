#!/usr/bin/env python3
"""Keep production deployment on the mini PC and CI on GitHub-hosted runners."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELF_HOSTED = "runs-on: [self-hosted, linux, x64]"
GITHUB_HOSTED = "runs-on: ubuntu-latest"
DEPLOY_WORKFLOW = "deploy-production.yml"


def main() -> None:
    workflows = sorted((ROOT / ".github/workflows").glob("*.yml"))
    runner_lines = []
    for workflow in workflows:
        content = workflow.read_text(encoding="utf-8")
        lines = [line.strip() for line in content.splitlines() if line.strip().startswith("runs-on:")]
        assert lines, workflow.name
        if workflow.name == DEPLOY_WORKFLOW:
            assert set(lines) == {GITHUB_HOSTED, SELF_HOSTED}, f"{workflow.name}: {lines}"
        else:
            assert all(line == GITHUB_HOSTED for line in lines), f"{workflow.name}: {lines}"
        runner_lines.extend(f"{workflow.name}:{line}" for line in lines)
    assert workflows and runner_lines
    assert any(line == f"{DEPLOY_WORKFLOW}:{SELF_HOSTED}" for line in runner_lines)
    assert any(line.endswith(f":{GITHUB_HOSTED}") for line in runner_lines)
    action = (ROOT / ".github/actions/runner-python/action.yml").read_text(encoding="utf-8")
    assert "python3 --version" in action and "sys.version_info >= (3, 12)" in action
    print(f"ok: {len(runner_lines)} CI/CD jobs use the intended runner")


if __name__ == "__main__":
    main()
