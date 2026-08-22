#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/brian/MinecraftQuizGuesser}"
SERVICES="${SERVICES:-dashboard bot publisher-worker backup-rollback media clues-api analytics-api monitor}"
WAIT_SECONDS="${WAIT_SECONDS:-180}"
LOG_DIR="${APP_DIR}/out/logs"
LOG_FILE="${LOG_DIR}/minecraft-quiz-service.log"

mkdir -p "$LOG_DIR"

log() {
  printf '%s %s\n' "$(date -Is)" "$*" | tee -a "$LOG_FILE"
}

env_value() {
  local key="$1"
  local file
  for file in "${APP_DIR}/.env" "${APP_DIR}/.env.local"; do
    [ -f "$file" ] || continue
    awk -F= -v key="$key" '$1 == key {print $2}' "$file"
  done | tail -n 1 | tr -d '"'\'' '
}

wait_for() {
  local label="$1"
  local command="$2"
  local deadline=$((SECONDS + WAIT_SECONDS))

  until bash -lc "$command" >/dev/null 2>&1; do
    if [ "$SECONDS" -ge "$deadline" ]; then
      log "timeout waiting for ${label}"
      return 1
    fi
    sleep 5
  done
}

video_path="$(env_value VIDEO_STORAGE_PATH)"
video_path="${video_path:-${APP_DIR}/out/episodes}"

log "starting minecraft quiz services"
wait_for "network" "ping -c 1 -W 3 1.1.1.1"
wait_for "docker" "docker info"
wait_for "video storage" "test -d '${video_path}'"

cd "$APP_DIR"
python3 scripts/backup_state.py --quiet >>"$LOG_FILE" 2>&1 || true
python3 scripts/context_snapshot.py >>"$LOG_FILE" 2>&1 || true
python3 scripts/migrate_state.py >>"$LOG_FILE" 2>&1 || true
docker compose up -d $SERVICES >>"$LOG_FILE" 2>&1
log "services requested: ${SERVICES}"
