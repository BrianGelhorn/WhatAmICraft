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

## Secrets

Never print secrets. They may live in:

- `.env.local`
- Docker secrets
- `data/publishing-secrets.json`

If a command could expose secrets, summarize status instead.
