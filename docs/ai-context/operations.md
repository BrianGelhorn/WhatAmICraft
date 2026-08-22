# Operations

Use ponytail: prefer the smallest safe change. Edit locally, copy only touched files to Debian, rebuild the Docker image, restart affected services.

## Common commands on Debian

```bash
cd /home/brian/MinecraftQuizGuesser
python3 scripts/doctor.py
python3 scripts/context_snapshot.py
python3 scripts/backup_state.py
docker compose ps
docker compose logs --tail=80 dashboard bot publisher-worker
docker compose run --rm producer --all --dry-run
sudo systemctl restart minecraft-quiz.service
```

## Publishing rules

- Do not publish more than one video per interval.
- Do not generate while publishing is active.
- Keep 7-8 approved/candidate videos ready.
- Generate only if approved stock drops below 5.
- Alert Telegram when stock is low or empty.
- If empty when publishing time arrives, repost the oldest already-published video and alert Telegram.

## Backup rules

Backups must stay small. Include:

- `data/`
- `out/*.json`
- `out/*.sqlite3`
- configuration files
- recent log excerpts

Do not include MP4s, full logs, node modules, textures, or audio caches.
Never include `.env`, `.env.local`, or `data/publishing-secrets.json`.

## Secrets

Never print secrets. They may live in:

- `.env.local`
- Docker secrets
- `data/publishing-secrets.json`

If a command could expose secrets, summarize status instead.

## Automatic production deployment

After a successful merge to `main`, `Staging Smoke` runs first. The `Deploy production` workflow then runs on the self-hosted GitHub Actions runner installed on the mini PC. It archives the exact verified commit, backs up the current state, updates only versioned code and the episode bank, preserves runtime data/media/secrets, and runs `sudo -n /usr/local/sbin/whatamicraft-up`.

One-time mini PC setup:

1. In GitHub, open `Settings > Actions > Runners > New self-hosted runner`, choose Linux x64, and run GitHub's displayed setup commands on the mini PC. Do not paste the runner token into the repository or chat. The workflows use the standard `self-hosted`, `linux`, and `x64` labels.
2. From the deployed repository, run `sudo sh ops/install-production-launcher.sh` once so the root-owned launcher recognizes optional services added to `main`.
3. Keep the runner service enabled. It needs no Docker group membership; it only needs the existing exact sudo permission for the launcher.

The deploy job intentionally fails if the runner, launcher, backup, or dashboard health check is unavailable. It never copies `.env`, `.secrets`, generated media, or runtime state from GitHub.
