#!/usr/bin/env python3
"""Behavior check for YouTube video and vertical thumbnail uploads."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from publishing.common import PublishRequest  # noqa: E402
from publishing import youtube  # noqa: E402
import publish  # noqa: E402


def main() -> None:
    fixture = ROOT / "out" / "test-youtube-publishing"
    shutil.rmtree(fixture, ignore_errors=True)
    try:
        video = fixture / "episode.mp4"
        thumbnail = fixture / "episode.vertical.jpg"
        video.parent.mkdir(parents=True)
        video.write_bytes(b"video")
        thumbnail.write_bytes(b"vertical-jpeg")
        calls: list[tuple[str, dict, bytes]] = []
        original_access_token = youtube._access_token
        original_json_request = youtube.json_request
        original_request = youtube.request
        try:
            youtube._access_token = lambda: "test-token"
            youtube.json_request = lambda *_args, **_kwargs: ({}, {"Location": "https://upload.test/video"})

            def request(url: str, **kwargs):
                calls.append((url, kwargs.get("headers", {}), kwargs.get("data", b"")))
                if "thumbnails/set" in url:
                    return 200, {}, json.dumps({"items": [{"high": {"url": "https://img.test/thumb"}}]}).encode()
                return 200, {}, b'{"id":"video-1"}'

            youtube.request = request
            result = youtube.publish(PublishRequest("mc-01", video, thumbnail, "Title", "Caption", []))
            assert result["id"] == "video-1"
            assert result["thumbnail"] == thumbnail.name
            thumbnail_call = calls[-1]
            assert "thumbnails/set?videoId=video-1" in thumbnail_call[0]
            assert thumbnail_call[1]["Content-Type"] == "image/jpeg"
            assert thumbnail_call[2] == b"vertical-jpeg"
        finally:
            youtube._access_token = original_access_token
            youtube.json_request = original_json_request
            youtube.request = original_request
    finally:
        shutil.rmtree(fixture, ignore_errors=True)

    thumbnail = ROOT / "out" / "test-youtube-publishing" / "episode.vertical.jpg"
    calls: list[tuple[dict, str]] = []
    original_thumbnail_for = publish.thumbnail_for
    original_render = publish.render_thumbnails
    original_copy = publish.copy_thumbnail_config
    try:
        available = False

        def thumbnail_for(_episode):
            return thumbnail if available else None

        def render(config, stem):
            nonlocal available
            available = True
            calls.append((config, stem))
            return [thumbnail]

        publish.thumbnail_for = thumbnail_for
        publish.copy_thumbnail_config = lambda episode: {"episode": episode}
        publish.render_thumbnails = render
        episode = {"id": "mc-01", "target": {"id": "unknown"}}
        assert publish.ensure_thumbnail(episode) == thumbnail
        assert calls == [({"episode": episode}, "mc-01-unknown")]
    finally:
        publish.thumbnail_for = original_thumbnail_for
        publish.render_thumbnails = original_render
        publish.copy_thumbnail_config = original_copy

    print("ok: YouTube uploads, confirms, and backfills the vertical thumbnail")


if __name__ == "__main__":
    main()
