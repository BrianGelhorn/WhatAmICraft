#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_WORKSPACE:?GitHub Actions workspace is required}"
: "${DEPLOY_SHA:?Verified main commit is required}"

app_dir=/home/brian/MinecraftQuizGuesser
release_dir="$(mktemp -d /tmp/whatamicraft-release.XXXXXX)"

cleanup() {
  rm -rf "$release_dir"
}
trap cleanup EXIT

[ -d "$app_dir" ] || { echo "Production directory is missing" >&2; exit 1; }
[ "$GITHUB_WORKSPACE" != "$app_dir" ] || { echo "Runner workspace must not be production" >&2; exit 1; }
command -v rsync >/dev/null || { echo "rsync is required on the runner" >&2; exit 1; }

python3 "$GITHUB_WORKSPACE/scripts/backup_state.py" --quiet \
  --root "$app_dir" --backup-dir "$app_dir/backups/ops"
git -C "$GITHUB_WORKSPACE" archive --format=tar "$DEPLOY_SHA" | tar -xf - -C "$release_dir"

[ -f "$release_dir/data/quiz-copy-episodes.json" ] || {
  echo "Verified commit has no episode bank" >&2
  exit 1
}

# Keep production state, generated media, caches, and root-only secrets outside the release.
rsync -a --delete \
  --exclude=/data/ \
  --exclude=/out/ \
  --exclude=/backups/ \
  --exclude=/.secrets/ \
  --exclude=/.env \
  --exclude=/.env.local \
  --exclude=/public/audio/ \
  --exclude=/public/images/ \
  --exclude=/public/fonts/ \
  --exclude=/public/mc-assets/ \
  --exclude=/.git/ \
  "$release_dir/" "$app_dir/"

# The episode bank and validated clue catalog are versioned inputs; runtime state is not.
rsync -a "$release_dir/data/quiz-copy-episodes.json" "$app_dir/data/quiz-copy-episodes.json"
if [ -d "$release_dir/data/new-clues-20260815" ]; then
  rsync -a --delete "$release_dir/data/new-clues-20260815/" \
    "$app_dir/data/new-clues-20260815/"
fi

# Trigger the Debian automount before Docker creates bind mounts into it.
video_path="${VIDEO_STORAGE_PATH:-/srv/minecraft-videos/episodes}"
for attempt in $(seq 1 36); do
  [ -d "$video_path" ] && break
  sleep 5
done
[ -d "$video_path" ] || {
  echo "Production video storage is unavailable: $video_path" >&2
  exit 1
}

sudo -n /usr/local/sbin/whatamicraft-up

for attempt in $(seq 1 60); do
  if curl --fail --silent --show-error --max-time 10 \
    http://127.0.0.1:8787/health >/dev/null; then
    echo "Production deployed: $DEPLOY_SHA"
    exit 0
  fi
  sleep 5
done

echo "Production dashboard did not become healthy" >&2
exit 1
