#!/usr/bin/env python3
"""Keep production deployment fail-closed and secret-free."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    workflow = (ROOT / ".github/workflows/deploy-production.yml").read_text(encoding="utf-8")
    staging = (ROOT / ".github/workflows/staging-smoke.yml").read_text(encoding="utf-8")
    script = (ROOT / "scripts/deploy_main_to_production.sh").read_text(encoding="utf-8")
    launcher = (ROOT / "ops/install-production-launcher.sh").read_text(encoding="utf-8")

    assert "workflow_run:" in workflow and 'workflows: ["Staging Smoke"]' in workflow
    assert "conclusion == 'success'" in workflow and "head_branch == 'main'" in workflow
    assert "workflow_run.event == 'push'" in workflow
    assert "head_sha" in workflow and "whatamicraft-mini-pc" in workflow
    assert "push:" in staging and "- main" in staging
    for required in (
        "archive --format=tar",
        "backup_state.py\" --quiet",
        "rsync -a --delete",
        "--exclude=/out/",
        "--exclude=/.secrets/",
        "--exclude=/.env",
        "sudo -n /usr/local/sbin/whatamicraft-up",
        "127.0.0.1:8787/api/state",
    ):
        assert required in script, required
    assert "ssh " not in script and "scp " not in script
    assert "--env-file" not in script
    assert "whatamicraft-up" in launcher and "config --services" in launcher
    assert "install-wifi-watchdog.sh" in launcher
    print("ok: production deploy waits for staging, preserves runtime state, and uses the root launcher")


if __name__ == "__main__":
    main()
