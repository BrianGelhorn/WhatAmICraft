#!/bin/sh
set -eu

interface="wlan0"

if ! /usr/sbin/ip link show "$interface" | /usr/bin/grep -q 'state UP'; then
  /sbin/ifdown --force "$interface" >/dev/null 2>&1 || true
  /sbin/ifup "$interface" >/dev/null 2>&1 || true
  exit 0
fi

gateway=$(/usr/sbin/ip -4 route show default dev "$interface" | /usr/bin/awk 'NR == 1 {print $3}')
if [ -n "$gateway" ] && /usr/bin/ping -c 1 -W 2 "$gateway" >/dev/null 2>&1; then
  exit 0
fi

/usr/bin/logger -t minecraft-quiz-wifi "wlan0 lost gateway connectivity; cycling interface"
/sbin/ifdown --force "$interface" >/dev/null 2>&1 || true
/bin/sleep 2
/sbin/ifup "$interface" >/dev/null 2>&1 || /usr/bin/logger -t minecraft-quiz-wifi "wlan0 reconnection failed"
