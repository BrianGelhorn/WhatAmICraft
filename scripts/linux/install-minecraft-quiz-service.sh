#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo: sudo bash scripts/linux/install-minecraft-quiz-service.sh"
  exit 1
fi

APP_DIR="${APP_DIR:-/home/brian/MinecraftQuizGuesser}"
APP_USER="${APP_USER:-brian}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install -m 0755 "${SCRIPT_DIR}/start-minecraft-quiz.sh" /usr/local/bin/start-minecraft-quiz.sh
install -m 0755 "${SCRIPT_DIR}/configure-tailscale-access.sh" /usr/local/bin/configure-tailscale-access.sh

cat >/etc/systemd/system/minecraft-quiz.service <<SERVICE
[Unit]
Description=Minecraft Quiz Guesser stack
Wants=network-online.target docker.service tailscaled.service
After=network-online.target docker.service tailscaled.service

[Service]
Type=oneshot
User=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment=APP_DIR=${APP_DIR}
ExecStartPre=/usr/local/bin/configure-tailscale-access.sh
ExecStart=/usr/local/bin/start-minecraft-quiz.sh
RemainAfterExit=yes
TimeoutStartSec=420

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now minecraft-quiz.service
systemctl --no-pager --full status minecraft-quiz.service
