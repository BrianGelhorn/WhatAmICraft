# Operations

Use ponytail: prefer the smallest safe change. Edit locally, copy only touched files to Debian, rebuild the Docker image, restart affected services.

## Common commands on Debian

```bash
cd /home/brian/MinecraftQuizGuesser
python3 scripts/doctor.py
python3 scripts/context_snapshot.py
python3 scripts/backup_state.py
sudo docker compose --env-file /etc/whatamicraft/production.env ps
sudo docker compose --env-file /etc/whatamicraft/production.env logs --tail=80 dashboard bot publisher-worker
sudo docker compose --env-file /etc/whatamicraft/production.env run --rm producer --all --dry-run
sudo systemctl restart minecraft-quiz.service
```

## Production secrets

- Production variables live in `/etc/whatamicraft/production.env`, owned by `root:root` with mode `600`.
- The project `.env` is not used in production and must not be copied from the repository.
- `.secrets/` stays outside version control and is readable only by root; deployment archives exclude it.
- `brian` must not belong to the `docker` group. Reconnect after changing group membership.
- Install the root-owned launcher once from a checked-out release:

```bash
sudo sh ops/install-production-launcher.sh
```

The installer creates `/usr/local/sbin/whatamicraft-up` with owner `root:root`, mode `700`, and a sudoers rule that permits only that exact command without arguments. The launcher cannot be read or modified by `brian`, does not accept user-supplied Docker arguments, and never prints the environment file.

Rebuild or start the production services through the launcher:

```bash
sudo /usr/local/sbin/whatamicraft-up
```

The environment file survives code deployments and image rebuilds. Rotating a secret is a one-time edit of `/etc/whatamicraft/production.env`, followed by this command; values must never be printed in logs or chat.

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
