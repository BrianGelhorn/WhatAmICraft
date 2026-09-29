#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo: sudo bash scripts/linux/install-minecraft-quiz-service.sh"
  exit 1
fi
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != "--install-only" ]; }; then
  echo "Usage: $0 [--install-only]" >&2
  exit 2
fi

APP_DIR="${APP_DIR:-/home/brian/MinecraftQuizGuesser}"
APP_USER="${APP_USER:-brian}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install -m 0755 "${SCRIPT_DIR}/start-minecraft-quiz.sh" /usr/local/bin/start-minecraft-quiz.sh
install -m 0755 "${SCRIPT_DIR}/configure-tailscale-access.sh" /usr/local/bin/configure-tailscale-access.sh

cat >/etc/systemd/system/minecraft-quiz.service <<SERVICE
[Unit]
Description=Minecraft Quiz Guesser stack
Wants=network-online.target docker.service
After=network-online.target docker.service
StartLimitIntervalSec=0

[Service]
Type=oneshot
User=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment=APP_DIR=${APP_DIR}
ExecStart=/usr/local/bin/start-minecraft-quiz.sh
RemainAfterExit=yes
Restart=on-failure
RestartSec=30
TimeoutStartSec=420

[Install]
WantedBy=multi-user.target
SERVICE

cat >/etc/systemd/system/minecraft-quiz-access.service <<SERVICE
[Unit]
Description=Minecraft Quiz remote access
Wants=network-online.target tailscaled.service
After=network-online.target tailscaled.service
StartLimitIntervalSec=0

[Service]
Type=oneshot
User=${APP_USER}
ExecStart=/usr/local/bin/configure-tailscale-access.sh
RemainAfterExit=yes
Restart=on-failure
RestartSec=30
TimeoutStartSec=210

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable minecraft-quiz.service minecraft-quiz-access.service
# The launcher also installs these units during deploy; never launch it recursively.
systemctl --no-block start minecraft-quiz-access.service
if [ "${1:-}" != "--install-only" ]; then
  systemctl start minecraft-quiz.service
  systemctl --no-pager --full status minecraft-quiz.service
fi
