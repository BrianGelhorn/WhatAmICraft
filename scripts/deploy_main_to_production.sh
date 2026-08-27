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

previous_release=""
if [ -f "$app_dir/.release-version" ]; then
  previous_release="$(<"$app_dir/.release-version")"
fi

drain_timeout="${DEPLOY_DRAIN_TIMEOUT_SECONDS:-1800}"
started_at="$(date +%s)"
while [ -e "$app_dir/out/production.lock" ] || [ -e "$app_dir/out/publishing.lock" ]; do
  if [ "$(( $(date +%s) - started_at ))" -ge "$drain_timeout" ]; then
    echo "Timed out waiting for generation/publication tasks to finish" >&2
    exit 1
  fi
  sleep 5
done

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
  --exclude=/.release-version \
  --exclude=/.git/ \
  "$release_dir/" "$app_dir/"

# The episode bank and validated clue catalog are versioned inputs; runtime state is not.
rsync -a "$release_dir/data/quiz-copy-episodes.json" "$app_dir/data/quiz-copy-episodes.json"
if [ -d "$release_dir/data/new-clues-20260815" ]; then
  rsync -a --delete "$release_dir/data/new-clues-20260815/" \
    "$app_dir/data/new-clues-20260815/"
fi

release_marker="$app_dir/.release-version"
release_marker_tmp="$release_marker.tmp"
printf '%s\n' "$DEPLOY_SHA" > "$release_marker_tmp"
mv -f "$release_marker_tmp" "$release_marker"

active_marker="$app_dir/out/.active-template-version"
if [ ! -f "$active_marker" ]; then
  active_marker_tmp="$active_marker.tmp"
  printf '%s\n' "${previous_release:-legacy}" > "$active_marker_tmp"
  mv -f "$active_marker_tmp" "$active_marker"
fi

# Keep the user-level maintenance timer under the same GitHub-controlled release.
user_systemd_dir=/home/brian/.config/systemd/user
install -d -m 700 "$user_systemd_dir"
install -m 0644 \
  "$release_dir/scripts/linux/docker-disk-cleanup.service" \
  "$user_systemd_dir/docker-disk-cleanup.service"
install -m 0644 \
  "$release_dir/scripts/linux/docker-disk-cleanup.timer" \
  "$user_systemd_dir/docker-disk-cleanup.timer"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}"
systemctl --user daemon-reload
systemctl --user enable --now docker-disk-cleanup.timer

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
