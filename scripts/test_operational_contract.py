#!/usr/bin/env python3
"""Guard the restart, backup, staging, and CI contracts used by the mini PC."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

from test_linux_recovery import main as check_linux_recovery


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    start = (ROOT / "scripts/linux/start-minecraft-quiz.sh").read_text(encoding="utf-8")
    watchdog = (ROOT / "scripts/linux/wifi-watchdog.sh").read_text(encoding="utf-8")
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    media_dockerfile = (ROOT / "Dockerfile.media").read_text(encoding="utf-8")
    staging = (ROOT / "staging/compose.yaml").read_text(encoding="utf-8")
    services_ci = (ROOT / ".github/workflows/services-ci.yml").read_text(encoding="utf-8")
    staging_ci = (ROOT / ".github/workflows/staging-smoke.yml").read_text(encoding="utf-8")
    deploy_ci = (ROOT / ".github/workflows/deploy-production.yml").read_text(encoding="utf-8")
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True).stdout.split(b"\0")
    media_pattern = re.compile(rb"(?i)(^out/|^public/(audio|images|fonts)/|^references/|\.(mp4|mp3|m4a|wav|ogg|flac|aac|png|jpe?g|webp|gif|bmp|svg|mov|webm|avi|mkv|ttf|otf|woff2?)$)")
    assert not [path for path in tracked if path and media_pattern.search(path)]

    assert "scripts/backup_state.py --quiet" in start
    assert "sudo -n /usr/local/sbin/whatamicraft-up" in start
    assert "docker compose" not in start
    assert "ip link" in watchdog and "getent ahostsv4" in watchdog and "curl --ipv4" in watchdog
    assert "FAILS_BEFORE_RECOVERY:-6" in watchdog
    assert "has_local_network" in watchdog and "systemctl restart networking.service" in watchdog
    assert "ifdown" not in watchdog and "ifup" not in watchdog
    for service in ("dashboard:", "bot:", "publisher-worker:", "backup-rollback:", "media:"):
        section = compose.split(f"\n  {service}", 1)[1]
        assert "restart: unless-stopped" in section.split("\n  ", 1)[0] or "restart: unless-stopped" in section[:300]
    assert "CLUES_API_URL: http://clues-api:8790" in compose
    assert "CLUES_SOURCE_DIR: /app/data/new-clues-20260815" in compose
    assert "MONITOR_CLUES_URL: http://clues-api:8790" in compose
    assert "backup-rollback:" in staging
    assert "BACKUP_ADMIN_TOKEN" in staging
    assert "dockerfile: Dockerfile.media" in compose
    assert "dockerfile: Dockerfile.media" in staging
    assert "COPY nginx.media.conf /etc/nginx/conf.d/default.conf" in media_dockerfile
    nginx_media = (ROOT / "nginx.media.conf").read_text(encoding="utf-8")
    assert "root /mnt/out/episodes;" in nginx_media
    assert "location /videos/" in nginx_media
    assert "alias /mnt/out/episodes/;" in nginx_media
    assert "alias /mnt/out/thumbnails/;" in nginx_media
    assert "${STAGING_RUNTIME_DIR:-./runtime}/data:/app/data" in staging
    assert "${STAGING_RUNTIME_DIR:-./runtime}/out:/app/out" in staging
    assert "STAGING_DASHBOARD_PORT" in staging
    assert "STAGING_MEDIA_PORT" in staging
    assert "../data:/app/data" not in staging
    assert "../out:/app/out" not in staging
    assert 'profiles: ["integrations"]' in staging
    for workflow in (services_ci, staging_ci):
        assert 'STAGING_RUNTIME_DIR="${RUNNER_TEMP}/whatamicraft-staging-${GITHUB_RUN_ID}"' in workflow
        assert '--runtime-root "$STAGING_RUNTIME_DIR" --reset' in workflow
        assert '--runtime-root "$STAGING_RUNTIME_DIR"' in workflow
    assert "pull_request:" in staging_ci
    assert "push:" in staging_ci and "- main" in staging_ci
    assert "inputs.ref || github.sha" in staging_ci
    assert "workflow_run:" in deploy_ci and "head_sha" in deploy_ci
    assert "whatamicraft-ci-${GITHUB_RUN_ID}" in services_ci
    assert "down -v --remove-orphans" in services_ci
    assert "whatamicraft-staging-${GITHUB_RUN_ID}" in staging_ci
    assert "down -v --remove-orphans" in staging_ci
    assert "production" not in staging_ci.lower()
    check_linux_recovery()
    print("ok: mini PC restart, Wi-Fi recovery, backup, isolated staging, and CI cleanup contracts")


if __name__ == "__main__":
    main()
