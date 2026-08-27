#!/usr/bin/env bash
set -euo pipefail

# Conservative policy: dangling images older than 7d, build cache older than 14d.
min_used_pct="${DOCKER_CLEANUP_MIN_USED_PCT:-80}"
image_until="${DOCKER_CLEANUP_IMAGE_UNTIL:-168h}"
cache_until="${DOCKER_CLEANUP_CACHE_UNTIL:-336h}"
lock_dir="${XDG_RUNTIME_DIR:-${HOME}/.cache}/whatamicraft"

mkdir -p "$lock_dir"
exec 9>"$lock_dir/docker-disk-cleanup.lock"
flock -n 9 || exit 0

used_pct="$(df --output=pcent / | tail -n 1 | tr -dc '0-9')"
if (( used_pct < min_used_pct )); then
  printf 'disk-cleanup: skip, root usage %s%% (threshold %s%%)\n' "$used_pct" "$min_used_pct"
  exit 0
fi

printf 'disk-cleanup: root usage %s%%, pruning dangling images older than %s\n' "$used_pct" "$image_until"
docker image prune --force --filter "until=${image_until}"

used_pct="$(df --output=pcent / | tail -n 1 | tr -dc '0-9')"
if (( used_pct >= min_used_pct )); then
  printf 'disk-cleanup: root usage still %s%%, pruning build cache older than %s\n' "$used_pct" "$cache_until"
  docker builder prune --force --filter "until=${cache_until}"
fi
