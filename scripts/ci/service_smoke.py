#!/usr/bin/env python3
"""Small black-box smoke test for the isolated dashboard/media deployment."""

import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def get(url: str, expected: set[int] | None = None) -> tuple[int, dict[str, str], bytes]:
    expected = expected or {200}
    try:
        with urlopen(Request(url, headers={"User-Agent": "whatamicraft-ci"}), timeout=10) as response:
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

    expected_body = b"whatamicraft-ci-video"
    require_video(f"{dashboard}/videos/{fixture}", expected_body)
    require_video(f"{media}/{fixture}", expected_body)

    get(f"{dashboard}/videos/%2e%2e%2fdata%2fquiz-copy-episodes.json", {404})
    print("ok: dashboard/media service contract and path guard")


if __name__ == "__main__":
    main()
