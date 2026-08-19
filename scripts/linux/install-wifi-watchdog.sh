#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo: sudo bash scripts/linux/install-wifi-watchdog.sh"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WATCHDOG_SRC="${SCRIPT_DIR}/wifi-watchdog.sh"
WATCHDOG_DST="/usr/local/sbin/wifi-watchdog.sh"
SERVICE_DST="/etc/systemd/system/wifi-watchdog.service"

if [ ! -f "$WATCHDOG_SRC" ]; then
  echo "Missing ${WATCHDOG_SRC}"
  exit 1
fi

install -m 0755 "$WATCHDOG_SRC" "$WATCHDOG_DST"

cat >"$SERVICE_DST" <<'SERVICE'
[Unit]
Description=Reconnect WiFi automatically when internet is down
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
Environment=WIFI_IFACE=wlan0
Environment=CHECK_INTERVAL=30
Environment=FAILS_BEFORE_RECOVERY=2
ExecStart=/usr/local/sbin/wifi-watchdog.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now wifi-watchdog.service
systemctl --no-pager --full status wifi-watchdog.service
