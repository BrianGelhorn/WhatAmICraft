#!/usr/bin/env python3
"""Keep production deployment fail-closed and secret-free."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def check_active_template_baseline(script: str) -> None:
    # Execute the real promotion boundary without running the production launcher.
    block = script.split('active_marker="$app_dir/out/.active-template-version"', 1)[1]
    block = 'active_marker="$app_dir/out/.active-template-version"' + block.split(
        "# Keep the user-level maintenance timer", 1
    )[0]
    with tempfile.TemporaryDirectory(prefix="whatamicraft-deploy-test-") as temporary:
        repo = Path(temporary) / "repo"
        app = Path(temporary) / "runtime"
        (repo / "src").mkdir(parents=True)
        (repo / "scripts").mkdir()
        (app / "out/episodes").mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/migrate_compatible_artifacts.py", repo / "scripts")

        def git(*args: str) -> str:
            return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

        git("init", "--quiet")
        git("config", "user.name", "Deployment regression")
        git("config", "user.email", "deploy-test@example.invalid")
        git("config", "commit.gpgsign", "false")

        def commit(template: str, operation: str) -> str:
            (repo / "src/template.txt").write_text(template, encoding="utf-8")
            (repo / "scripts/worker.txt").write_text(operation, encoding="utf-8")
            git("add", ".")
            git("commit", "--quiet", "-m", operation)
            return git("rev-parse", "HEAD")

        old = commit("old", "initial")
        active = commit("active", "promoted")
        previous = commit("unpromoted", "template change")
        restored = commit("active", "restore active template")
        marker = app / "out/.active-template-version"
        marker.write_text(active + "\n", encoding="utf-8")
        manifests = {
            "current": {"templateVersion": active, "videoSha256": "unchanged"},
            "old": {"templateVersion": old},
            "legacy": {"templateVersion": active, "legacy": True},
        }
        for name, manifest in manifests.items():
            (app / f"out/episodes/{name}.artifact.json").write_text(json.dumps(manifest), encoding="utf-8")

        def deploy(previous_release: str, release: str) -> None:
            subprocess.run(["bash", "-euo", "pipefail", "-c", block], check=True, env={
                **os.environ,
                "app_dir": str(app),
                "GITHUB_WORKSPACE": str(repo),
                "previous_release": previous_release,
                "DEPLOY_SHA": release,
            })

        def read_manifests() -> dict:
            return {name: json.loads((app / f"out/episodes/{name}.artifact.json").read_text())
                    for name in manifests}

        deploy(previous, restored)
        assert marker.read_text().strip() == restored, "restoring the active template must unblock generation"
        manifests["current"]["templateVersion"] = restored
        assert read_manifests() == manifests, "only compatible, non-legacy artifacts may migrate"

        changed = commit("different", "new template awaiting promotion")
        operational = commit("different", "operational fix only")
        deploy(changed, operational)
        assert marker.read_text().strip() == restored, "an operational update must not promote a pending template"
        assert read_manifests() == manifests

        for unknown in ("legacy", "", "0" * 40):
            marker.write_text(unknown + "\n", encoding="utf-8")
            deploy(changed, operational)
            assert marker.read_text().strip() == unknown, "unknown active templates must fail closed"
            assert read_manifests() == manifests


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
    check_active_template_baseline(script)
    print("ok: production deploy waits for staging, preserves runtime state, and uses the root launcher")


if __name__ == "__main__":
    main()
