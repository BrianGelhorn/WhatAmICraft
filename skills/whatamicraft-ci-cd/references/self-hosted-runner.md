# Self-hosted mini-PC runner contract

## Baseline

- Match jobs with `runs-on: [self-hosted, linux, x64]`; add custom labels only after confirming them on the registered runner.
- Verify runner service online, repository access, labels, free disk/RAM, Docker daemon, and concurrent-job capacity when jobs stay queued while the runner appears idle.
- Debian 13 may not have a cached `actions/setup-python` 3.12 build. Use `./.github/actions/runner-python`, which aliases installed `python3` and checks the supported minimum.
- Use `actions/setup-node` plus `npm ci`. Keep lint/TypeScript/Remotion versions compatible in `package.json` and lockfile.
- Prepare Remotion's browser with `npx remotion browser ensure`; do not require a globally installed Chrome.
- Check/install ffmpeg in the job/image that owns media fixture creation.

## Docker and staging

- Ensure the runner account belongs to the Docker group and restart the runner service after membership changes.
- Use unique compose project names containing `GITHUB_RUN_ID`.
- Set `STAGING_RUNTIME_DIR` below `RUNNER_TEMP`; make compose mounts use it and pass the same path to seed/smoke scripts.
- Allow destructive staging reset only below the repository staging test root or `RUNNER_TEMP`.
- Never bind writable container paths to the Git checkout. Root-owned runtime files otherwise break the next `actions/checkout` cleanup.
- On failure, print bounded `compose ps` and redacted tail logs; always run `down -v --remove-orphans`.

## Required checks and deployment

- Keep branch-protection names identical to emitted job names.
- Ensure every required workflow triggers for pull requests and protected `main`; remove stale required contexts only through authorized repository settings.
- Merge only after required checks pass. Successful `main` then deploys on the self-hosted runner through `sudo /usr/local/sbin/whatamicraft-up` without reading the env file.
- Before promotion verify backup/rollback; afterward verify commit/version and health of every required service.

## Verified production lessons

- The mini PC's video disk is `/srv/minecraft-videos`, configured through systemd `x-systemd.automount`. A deploy must wait for `/srv/minecraft-videos/episodes` before calling the root launcher; otherwise Docker can retain a stale bind mount that returns `Input/output error` even though the host and a fresh container read the files.
- When the stale mount occurs, recreate only the project containers after the volume is active; never delete volumes, runtime data, media, or secrets. Verify dashboard `/health`, `/api/state`, and MP4 reads from dashboard, publisher-worker, and media.
- `minecraft-quiz.service` is enabled and active at boot and starts the worker through the approved launcher. Do not add a second scheduler or treat a live worker container as proof that its durable job state is healthy.
- If a required check is expected but no run is attached, inspect workflow event/branch filters and runner state; do not bypass branch protection or merge on manually asserted success.

## Triage order

For queued jobs: event/branch filter → required context name → runner online/busy → labels → repository permission. For running jobs: exact failed command → installed runtime → permissions/ownership → disk/memory → service logs.

