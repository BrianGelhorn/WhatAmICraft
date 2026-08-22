#!/usr/bin/env bash
set -u

WIFI_IFACE="${WIFI_IFACE:-wlan0}"
CHECK_INTERVAL="${CHECK_INTERVAL:-30}"
FAILS_BEFORE_RECOVERY="${FAILS_BEFORE_RECOVERY:-6}"
PING_TIMEOUT="${PING_TIMEOUT:-3}"
DNS_TARGET="${DNS_TARGET:-example.com}"
HTTPS_TIMEOUT="${HTTPS_TIMEOUT:-5}"
HTTPS_TARGETS="${HTTPS_TARGETS:-https://www.google.com/generate_204 https://github.com/robots.txt}"

log() {
  logger -t wifi-watchdog "$*"
  printf '%s %s\n' "$(date -Is)" "$*"
}

gateway() {
  ip -4 route show default dev "$WIFI_IFACE" | awk 'NR == 1 {print $3}'
}

has_gateway() {
  local current_gateway
  current_gateway="$(gateway)"
  [ -n "$current_gateway" ] || return 1
  ping -I "$WIFI_IFACE" -c 1 -W "$PING_TIMEOUT" "$current_gateway" >/dev/null 2>&1
}

has_dns() {
  getent ahostsv4 "$DNS_TARGET" >/dev/null 2>&1
}

has_https() {
  command -v curl >/dev/null 2>&1 || return 1
  local target
  for target in $HTTPS_TARGETS; do
    if curl --ipv4 --interface "$WIFI_IFACE" --fail --silent \
      --output /dev/null --max-time "$HTTPS_TIMEOUT" "$target"; then
      return 0
    fi
  done
  return 1
}

has_local_network() {
  has_gateway && has_dns
}

has_internet() {
  has_local_network && has_https
}

recover_wifi() {
  log "Local network check failed. Recovering ${WIFI_IFACE}..."

  ip link set "$WIFI_IFACE" down || true
  sleep 2
  ip link set "$WIFI_IFACE" up || true
  sleep 8

  if has_internet; then
    log "Internet recovered on ${WIFI_IFACE} without restarting networking.service."
    return 0
  fi

  if has_local_network; then
    log "Gateway and DNS are healthy; external HTTPS checks remain unavailable. Keeping ${WIFI_IFACE} up."
    return 0
  fi

  if systemctl is-active --quiet networking.service; then
    log "Local network is still unavailable; restarting networking.service."
    systemctl restart networking.service || true
    sleep 10
  fi

  if has_internet; then
    log "Internet recovered after networking.service restart."
  else
    log "Recovery exhausted; watchdog will retry on the next cycle."
  fi
}

log "Started. iface=${WIFI_IFACE} interval=${CHECK_INTERVAL}s failures-before-recovery=${FAILS_BEFORE_RECOVERY}"

if [ "${WIFI_WATCHDOG_ONCE:-0}" = "1" ]; then
  if has_internet; then
    log "One-shot network check passed."
    exit 0
  fi
  log "One-shot network check failed."
  exit 1
fi

fail_count=0

while true; do
  if has_internet; then
    if [ "$fail_count" -gt 0 ]; then
      log "Internet is back after ${fail_count} failed check(s)."
    fi
    fail_count=0
  else
    fail_count=$((fail_count + 1))
    log "Internet check failed ${fail_count}/${FAILS_BEFORE_RECOVERY}."

    if [ "$fail_count" -ge "$FAILS_BEFORE_RECOVERY" ]; then
      recover_wifi
      fail_count=0
    fi
  fi

  sleep "$CHECK_INTERVAL"
done
