#!/usr/bin/env bash
set -euo pipefail

DASHBOARD_TARGET="${DASHBOARD_TARGET:-http://127.0.0.1:8787}"
MEDIA_TARGET="${MEDIA_TARGET:-http://127.0.0.1:8080}"
TAILSCALE_WAIT_SECONDS="${TAILSCALE_WAIT_SECONDS:-180}"
TAILSCALE_RETRY_SECONDS="${TAILSCALE_RETRY_SECONDS:-5}"

deadline=$((SECONDS + TAILSCALE_WAIT_SECONDS))

tailscale_ready() {
  tailscale status --json 2>/dev/null | python3 -c 'import json, sys; data = json.load(sys.stdin); raise SystemExit(0 if data.get("BackendState") == "Running" else 1)'
}

while ! tailscale_ready; do
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo "Tailscale no estuvo listo dentro de ${TAILSCALE_WAIT_SECONDS}s" >&2
    exit 1
  fi
  sleep "$TAILSCALE_RETRY_SECONDS"
done

configure() {
  tailscale serve --bg --https=8443 "$DASHBOARD_TARGET" || return
  tailscale funnel --bg --https=443 "$MEDIA_TARGET" || return
  tailscale serve status
}

while ! configure; do
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo "No se pudo configurar Tailscale dentro de ${TAILSCALE_WAIT_SECONDS}s" >&2
    exit 1
  fi
  sleep "$TAILSCALE_RETRY_SECONDS"
done
