#!/usr/bin/env bash
set -u

WIFI_IFACE="${WIFI_IFACE:-wlan0}"
CHECK_INTERVAL="${CHECK_INTERVAL:-30}"
FAILS_BEFORE_RECOVERY="${FAILS_BEFORE_RECOVERY:-2}"
PING_TIMEOUT="${PING_TIMEOUT:-4}"
PING_TARGETS="${PING_TARGETS:-1.1.1.1 8.8.8.8}"

log() {
  logger -t wifi-watchdog "$*"
  printf '%s %s\n' "$(date -Is)" "$*"
}

has_internet() {
  local target

  for target in $PING_TARGETS; do
    if ping -I "$WIFI_IFACE" -c 1 -W "$PING_TIMEOUT" "$target" >/dev/null 2>&1; then
      return 0
    fi
  done

  for target in $PING_TARGETS; do
    if ping -c 1 -W "$PING_TIMEOUT" "$target" >/dev/null 2>&1; then
      return 0
    fi
  done

  return 1
}

restart_wpa() {
  if systemctl list-unit-files "wpa_supplicant@${WIFI_IFACE}.service" | grep -q "wpa_supplicant@${WIFI_IFACE}.service"; then
    systemctl restart "wpa_supplicant@${WIFI_IFACE}.service" || true
    return
  fi

  systemctl restart wpa_supplicant.service || true
}

renew_dhcp() {
  if command -v dhclient >/dev/null 2>&1; then
    dhclient -r "$WIFI_IFACE" >/dev/null 2>&1 || true
    dhclient "$WIFI_IFACE" >/dev/null 2>&1 || true
    return
  fi

  if systemctl is-active --quiet networking.service; then
    systemctl restart networking.service || true
  fi
}

recover_wifi() {
  log "Internet check failed. Recovering ${WIFI_IFACE}..."

  for attempt in 1 2 3; do
    log "Recovery attempt ${attempt}/3 for ${WIFI_IFACE}."

    if command -v ifdown >/dev/null 2>&1; then
      ifdown --force "$WIFI_IFACE" >/dev/null 2>&1 || true
    fi
    ip link set "$WIFI_IFACE" down || true
    sleep 2
    ip link set "$WIFI_IFACE" up || true

    if command -v ifup >/dev/null 2>&1; then
      ifup "$WIFI_IFACE" >/dev/null 2>&1 || true
    fi
    if command -v wpa_cli >/dev/null 2>&1; then
      wpa_cli -i "$WIFI_IFACE" reconfigure >/dev/null 2>&1 || true
      wpa_cli -i "$WIFI_IFACE" reconnect >/dev/null 2>&1 || true
    fi
    restart_wpa
    renew_dhcp
    sleep 8

    if has_internet; then
      log "Internet recovered on ${WIFI_IFACE} without reboot."
      return 0
    fi
  done

  log "Wi-Fi still unavailable after interface recovery; restarting networking.service."
  systemctl restart networking.service >/dev/null 2>&1 || true
  sleep 10
  if has_internet; then
    log "Internet recovered after networking.service restart."
  else
    log "Recovery exhausted; watchdog will retry on the next cycle."
  fi
}

log "Started. iface=${WIFI_IFACE} interval=${CHECK_INTERVAL}s"

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
