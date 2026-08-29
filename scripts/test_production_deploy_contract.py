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
    assert "runs-on: ubuntu-latest" in workflow and "ref: main" in workflow
    assert "Reject stale deployment" in workflow
    assert "current_sha" in workflow and "current=false" in workflow
    assert "needs: gate" in workflow
    assert "head_sha" in workflow and "runs-on: [self-hosted, linux, x64]" in workflow
    assert "fetch-depth: 0" in workflow
    assert "group: whatamicraft-production" in workflow and "cancel-in-progress: false" in workflow
    assert "push:" in staging and "- main" in staging
    assert '"$GITHUB_WORKSPACE/scripts/backup_state.py" --quiet' in script
    assert '--root "$app_dir" --backup-dir "$app_dir/backups/ops"' in script
    assert "production.lock" in script and "publishing.lock" in script
    assert "DEPLOY_DRAIN_TIMEOUT_SECONDS" in script
    assert "PRODUCTION_LOCK_STALE_SECONDS" in script
    assert "PUBLISH_LOCK_STALE_SECONDS" in script
    assert "clear_stale_lock" in script and "rmdir" in script
    assert "release_marker" in script and "DEPLOY_SHA" in script
    assert "runtime_release_marker" in script and "out/.release-version" in script
    assert "active-template-version" in script and "previous_release" in script
    assert 'git -C "$GITHUB_WORKSPACE" diff --quiet' in script
    assert 'scripts/migrate_compatible_artifacts.py' in script
    assert "templates/" in script and "scripts/video_formats.py" in script
    assert "video storage" in script and "/srv/minecraft-videos/episodes" in script
    for required in (
        "archive --format=tar",
        "rsync -a --delete",
        "--exclude=/out/",
        "--exclude=/.secrets/",
        "--exclude=/.env",
        "sudo -n /usr/local/sbin/whatamicraft-up",
        "127.0.0.1:8787/health",
        "docker-disk-cleanup.service",
        "docker-disk-cleanup.timer",
        "systemctl --user daemon-reload",
    ):
        assert required in script, required
    assert "ssh " not in script and "scp " not in script
    assert "--env-file" not in script
    assert "whatamicraft-up" in launcher and "config --services" in launcher
    assert "install-wifi-watchdog.sh" in launcher
    print("ok: production deploy waits for staging, preserves runtime state, and uses the root launcher")


if __name__ == "__main__":
    main()
