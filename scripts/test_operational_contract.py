#!/usr/bin/env python3
"""Guard the restart, backup, staging, and CI contracts used by the mini PC."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    start = (ROOT / "scripts/linux/start-minecraft-quiz.sh").read_text(encoding="utf-8")
    watchdog = (ROOT / "scripts/linux/wifi-watchdog.sh").read_text(encoding="utf-8")
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    media_dockerfile = (ROOT / "Dockerfile.media").read_text(encoding="utf-8")
    staging = (ROOT / "staging/compose.yaml").read_text(encoding="utf-8")
    services_ci = (ROOT / ".github/workflows/services-ci.yml").read_text(encoding="utf-8")
    staging_ci = (ROOT / ".github/workflows/staging-smoke.yml").read_text(encoding="utf-8")

    assert "scripts/backup_state.py --quiet" in start
    assert "docker compose up -d" in start
    assert "ip link" in watchdog and "ifdown" in watchdog and "ifup" in watchdog and "systemctl" in watchdog
    for service in ("dashboard:", "bot:", "publisher-worker:", "backup-rollback:", "media:"):
        section = compose.split(f"\n  {service}", 1)[1]
        assert "restart: unless-stopped" in section.split("\n  ", 1)[0] or "restart: unless-stopped" in section[:300]
    assert "backup-rollback:" in staging
    assert "BACKUP_ADMIN_TOKEN" in staging
    assert "dockerfile: Dockerfile.media" in compose
    assert "dockerfile: Dockerfile.media" in staging
    assert "RUN mkdir -p /usr/share/nginx/html/thumbnails" in media_dockerfile
    assert "./runtime/data:/app/data" in staging
    assert "./runtime/out:/app/out" in staging
    assert "STAGING_DASHBOARD_PORT" in staging
    assert "STAGING_MEDIA_PORT" in staging
    assert "../data:/app/data" not in staging
    assert "../out:/app/out" not in staging
    assert 'profiles: ["integrations"]' in staging
    assert "prepare_staging.py --reset" in staging_ci
    assert "--runtime-root staging/runtime" in staging_ci
    assert "pull_request:" in staging_ci
    assert "inputs.ref || github.sha" in staging_ci
    assert "whatamicraft-ci-${GITHUB_RUN_ID}" in services_ci
    assert "down -v --remove-orphans" in services_ci
    assert "whatamicraft-staging-${GITHUB_RUN_ID}" in staging_ci
    assert "down -v --remove-orphans" in staging_ci
    assert "production" not in staging_ci.lower()
    print("ok: mini PC restart, Wi-Fi recovery, backup, isolated staging, and CI cleanup contracts")


if __name__ == "__main__":
    main()
