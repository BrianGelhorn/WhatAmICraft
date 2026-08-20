#!/usr/bin/env python3
"""Small black-box smoke test for the isolated dashboard/media deployment."""

import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request(
    url: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
    expected: set[int] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    expected = expected or {200}
    request_headers = {"User-Agent": "whatamicraft-ci", **(headers or {})}
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    try:
        with urlopen(Request(url, data=body, headers=request_headers, method=method), timeout=10) as response:
            status = response.status
            headers = {key.lower(): value for key, value in response.headers.items()}
            body = response.read()
    except HTTPError as error:
        if error.code in expected:
            return error.code, {key.lower(): value for key, value in error.headers.items()}, error.read()
        raise RuntimeError(f"HTTP {error.code} from {url}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach service for {url}: {error.reason}") from error
    if status not in expected:
        raise RuntimeError(f"Unexpected HTTP {status} from {url}")
    return status, headers, body


def get(url: str, expected: set[int] | None = None, headers: dict[str, str] | None = None):
    return request(url, headers=headers, expected=expected)


def require_video(url: str, expected_body: bytes) -> None:
    status, headers, body = get(url)
    if not headers.get("content-type", "").startswith("video/mp4"):
        raise RuntimeError(f"{url} did not return video/mp4")
    if body != expected_body:
        raise RuntimeError(f"{url} returned unexpected fixture bytes")
    if status != 200:
        raise RuntimeError(f"{url} did not return HTTP 200")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dashboard", required=True)
    parser.add_argument("--media", required=True)
    parser.add_argument("--analytics", required=True)
    parser.add_argument("--monitor", required=True)
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()

    dashboard = args.dashboard.rstrip("/")
    media = args.media.rstrip("/")
    analytics = args.analytics.rstrip("/")
    monitor = args.monitor.rstrip("/")
    fixture = args.fixture.lstrip("/")

    status, headers, _ = get(f"{dashboard}/")
    if status != 200 or not headers.get("content-type", "").startswith("text/html"):
        raise RuntimeError("dashboard root is not serving HTML")

    _, state_headers, state_body = get(f"{dashboard}/api/state")
    if not state_headers.get("content-type", "").startswith("application/json"):
        raise RuntimeError("dashboard state is not JSON")
    state = json.loads(state_body)
    if not isinstance(state.get("episodes"), list):
        raise RuntimeError("dashboard state has no episode list")

    _, analytics_headers, analytics_health_body = get(f"{analytics}/health")
    if not analytics_headers.get("content-type", "").startswith("application/json"):
        raise RuntimeError("analytics service health is not JSON")
    analytics_health = json.loads(analytics_health_body)
    if analytics_health.get("service") != "analytics-api":
        raise RuntimeError("analytics service health returned the wrong service")
    _, analytics_headers, analytics_body = get(f"{analytics}/api/analytics")
    if not analytics_headers.get("content-type", "").startswith("application/json"):
        raise RuntimeError("analytics service snapshot is not JSON")
    analytics_snapshot = json.loads(analytics_body)
    if not isinstance(analytics_snapshot.get("platforms"), list) or not isinstance(analytics_snapshot.get("summary"), dict):
        raise RuntimeError("analytics service returned an invalid snapshot")
    if state.get("analytics", {}).get("schemaVersion") != analytics_snapshot.get("schemaVersion"):
        raise RuntimeError("dashboard is not receiving analytics from the service")

    _, monitor_headers, monitor_health_body = get(f"{monitor}/health")
    if not monitor_headers.get("content-type", "").startswith("application/json"):
        raise RuntimeError("monitor service health is not JSON")
    monitor_health = json.loads(monitor_health_body)
    if monitor_health.get("service") != "monitor":
        raise RuntimeError("monitor service health returned the wrong service")
    _, _, monitor_status_body = request(f"{monitor}/api/monitor/check", method="POST")
    monitor_status = json.loads(monitor_status_body)
    monitored = {item.get("service"): item.get("status") for item in monitor_status.get("services", [])}
    if not {"dashboard", "clues-api", "analytics-api", "media"}.issubset(monitored):
        raise RuntimeError("monitor service did not check every staging dependency")
    if any(monitored[name] != "up" for name in ("dashboard", "clues-api", "analytics-api", "media")):
        raise RuntimeError(f"monitor service found a staging dependency down: {monitored}")
    _, _, proxied_monitor_body = get(f"{dashboard}/api/monitor/status")
    if not isinstance(json.loads(proxied_monitor_body).get("services"), list):
        raise RuntimeError("dashboard monitor proxy returned an invalid status")
    _, _, monitor_events_body = get(f"{monitor}/api/monitor/events?limit=10")
    if not isinstance(json.loads(monitor_events_body).get("items"), list):
        raise RuntimeError("monitor service returned an invalid event list")

    _, clues_headers, clues_body = get(f"{dashboard}/api/clues?status=unused")
    if not clues_headers.get("content-type", "").startswith("application/json"):
        raise RuntimeError("dashboard clues proxy is not JSON")
    clues = json.loads(clues_body)
    if not isinstance(clues.get("items"), list) or clues.get("status") != "unused":
        raise RuntimeError("dashboard clues proxy returned an invalid catalog")

    original_config = state.get("publishing", {}).get("config")
    if not isinstance(original_config, dict):
        raise RuntimeError("dashboard state has no publishing config")
    changed_config = json.loads(json.dumps(original_config))
    changed_config["title"] = "CI {kind}"
    request(
        f"{dashboard}/api/publishing/config",
        method="POST",
        payload={"config": changed_config},
    )
    _, _, changed_state_body = get(f"{dashboard}/api/state")
    changed_state = json.loads(changed_state_body)
    if changed_state["publishing"]["config"]["title"] != "CI {kind}":
        raise RuntimeError("dashboard did not persist the configuration change")
    _status, _headers, invalid_body = request(
        f"{dashboard}/api/action",
        method="POST",
        payload={"episodeId": "mc-999", "action": "invalid"},
        expected={409},
    )
    if json.loads(invalid_body).get("ok") is not False:
        raise RuntimeError("dashboard accepted an invalid action")
    request(
        f"{dashboard}/api/publishing/config",
        method="POST",
        payload={"config": original_config},
    )

    expected_body = b"whatamicraft-ci-video"
    require_video(f"{dashboard}/videos/{fixture}", expected_body)
    require_video(f"{media}/{fixture}", expected_body)

    range_status, range_headers, range_body = get(
        f"{media}/{fixture}",
        expected={206},
        headers={"Range": "bytes=0-4"},
    )
    if range_status != 206 or range_body != expected_body[:5] or "bytes 0-4/" not in range_headers.get("content-range", ""):
        raise RuntimeError("media service did not honor a byte range")
    get(f"{media}/missing.mp4", {404})
    get(f"{media}/%2e%2e%2fdata%2fquiz-copy-episodes.json", {400, 404})

    get(f"{dashboard}/videos/%2e%2e%2fdata%2fquiz-copy-episodes.json", {404})
    print("ok: dashboard/media/analytics/monitor service contract and path guard")


if __name__ == "__main__":
    main()
