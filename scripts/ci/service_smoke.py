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
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()

    dashboard = args.dashboard.rstrip("/")
    media = args.media.rstrip("/")
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
    get(f"{media}/%2e%2e%2fdata%2fquiz-copy-episodes.json", {404})

    get(f"{dashboard}/videos/%2e%2e%2fdata%2fquiz-copy-episodes.json", {404})
    print("ok: dashboard/media service contract and path guard")


if __name__ == "__main__":
    main()
