#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/brian/MinecraftQuizGuesser}"
WAIT_SECONDS="${WAIT_SECONDS:-180}"
LOG_DIR="${APP_DIR}/out/logs"
LOG_FILE="${LOG_DIR}/minecraft-quiz-service.log"

mkdir -p "$LOG_DIR"

log() {
  printf '%s %s\n' "$(date -Is)" "$*" | tee -a "$LOG_FILE"
}

wait_for() {
  local label="$1"
  shift
  local deadline=$((SECONDS + WAIT_SECONDS))

  until "$@" >/dev/null 2>&1; do
    if [ "$SECONDS" -ge "$deadline" ]; then
      log "timeout waiting for ${label}"
      return 1
    fi
    sleep 5
  done
}

video_path="${VIDEO_STORAGE_PATH:-/srv/minecraft-videos/episodes}"

log "starting minecraft quiz services"
wait_for "docker" docker info
wait_for "video storage" test -d "$video_path"

cd "$APP_DIR"
python3 scripts/backup_state.py --quiet >>"$LOG_FILE" 2>&1
python3 scripts/context_snapshot.py >>"$LOG_FILE" 2>&1
python3 scripts/migrate_state.py >>"$LOG_FILE" 2>&1
exec sudo -n /usr/local/sbin/whatamicraft-up >>"$LOG_FILE" 2>&1
