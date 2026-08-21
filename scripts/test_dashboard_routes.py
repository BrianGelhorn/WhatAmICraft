#!/usr/bin/env python3
"""Exercise every dashboard HTTP route against an isolated real server."""

import json
import os
import shutil
import sys
import threading
import uuid
from contextlib import contextmanager
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))
import app  # noqa: E402


@contextmanager
def isolated_directory():
    root = ROOT / ".tmp" / f"dashboard-routes-{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    try:
        yield root
    finally:
        shutil.rmtree(root)


def main() -> None:
    workflow = (ROOT / ".github/workflows/services-ci.yml").read_text(encoding="utf-8")
    assert "python scripts/test_dashboard_routes.py" in workflow
    assert "node scripts/ci/dashboard_ui.mjs" in workflow
    calls: list[tuple[str, object]] = []
    state = {"revision": 0}
    schedule = {"publishing": None, "generation": None}
    config = {
        "schedule": {"enabled": True, "intervalMinutes": 60},
        "generation": {"enabled": True, "intervalMinutes": 60},
    }

    def called(name, value=None):
        calls.append((name, value))

    with isolated_directory() as root:
        (root / "dashboard").mkdir()
        (root / "out/episodes").mkdir(parents=True)
        (root / "out/thumbnails/item").mkdir(parents=True)
        (root / "public/audio/voice").mkdir(parents=True)
        (root / "public/audio/music-library/test").mkdir(parents=True)
        (root / "dashboard/index.html").write_text("<main>dashboard fixture</main>", encoding="utf-8")
        (root / "out/episodes/mc-01-test.mp4").write_bytes(b"video-fixture")
        (root / "out/thumbnails/item/mc-01-test.jpg").write_bytes(b"image-fixture")
        (root / "public/audio/voice/test.mp3").write_bytes(b"voice-fixture")
        (root / "public/audio/music-library/test/clip.m4a").write_bytes(b"music-fixture")

        app.ROOT = root
        app.INDEX_PATH = root / "dashboard/index.html"
        app.OUTPUT_DIR = root / "out/episodes"
        app.LEGACY_OUTPUT_DIR = root / "legacy"
        app.THUMBNAIL_DIR = root / "out/thumbnails"
        app.LOG_DIR = root / "out/logs"
        app.dashboard_state = lambda: {"ok": True, "revision": state["revision"]}
        app.diagnostics_state = lambda: {"ok": True, "services": []}
        app.analytics_request = lambda path, **kwargs: (HTTPStatus.OK, {"ok": True, "path": path})
        app.analytics_text = lambda path: (HTTPStatus.OK, "# analytics")
        app.ANALYTICS_API_URL = "http://analytics.invalid"
        app.clues_request = lambda path: (HTTPStatus.OK, {"ok": True, "path": path})
        app.monitor_request = lambda path, **kwargs: (HTTPStatus.OK, {"ok": True, "path": path})
        app.load_library = lambda: {"tracks": [{"id": "test", "clips": [{"id": "clip", "publicSrc": "audio/music-library/test/clip.m4a"}]}]}

        app.cancel_active_job = lambda lane=None: called("cancel", lane)
        app.start_job = lambda episode_id, format_id=None, **kwargs: called("generate", (episode_id, format_id, kwargs))
        app.save_config = lambda value: called("config", value) or value
        app.load_schedule = lambda: {"nextRunAt": schedule["publishing"]}
        app.save_schedule = lambda value: schedule.update(publishing=value)
        app.load_generation_schedule = lambda: {"nextRunAt": schedule["generation"]}
        app.save_generation_schedule = lambda value: schedule.update(generation=value)
        app.save_secrets = lambda value: called("secrets", sorted(value))
        app.disconnect_tiktok = lambda: called("disconnect")
        app.start_analytics_sync = lambda: called("analytics")
        app.start_publish_job = lambda: called("publish-next")
        app.start_platform_publish = lambda episode, platform: called("publish-platform", (episode, platform))
        app.start_backup_job = lambda: called("backup")
        app.start_context_snapshot_job = lambda: called("snapshot")
        app.start_music_import = lambda value: called("music-import", value)
        app.read_job = lambda *args: {"status": "idle"}
        app.delete_track = lambda track_id: called("music-delete", track_id)
        app.set_original_starts = lambda filename, starts: called("music-starts", (filename, starts))
        app.queue_items = lambda: [{"episodeId": "mc-02", "status": "pending"}]
        app.queue_episode = lambda episode: (state.update(revision=state["revision"] + 1), called("approve", episode))
        app.remove_queue_item = lambda episode: called("unqueue", episode)
        app.reject_episode = lambda episode: called("reject", episode)
        app.pend_hints = lambda episode: called("hints", episode)
        app.clear_hints = lambda episode: called("clear-hints", episode)

        server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"

        def request(path: str, payload=None, expected=HTTPStatus.OK):
            body = json.dumps(payload).encode() if payload is not None else None
            headers = {"Content-Type": "application/json"} if body else {}
            try:
                with urlopen(Request(base + path, data=body, headers=headers, method="POST" if body is not None else "GET"), timeout=5) as response:
                    status, content_type, value = response.status, response.headers.get("Content-Type", ""), response.read()
            except HTTPError as error:
                status, content_type, value = error.code, error.headers.get("Content-Type", ""), error.read()
            assert status == expected, (path, status, value)
            return content_type, value

        try:
            assert request("/")[1] == b"<main>dashboard fixture</main>"
            assert json.loads(request("/api/state")[1]) == {"ok": True, "revision": 0}
            assert json.loads(request("/api/diagnostics")[1])["ok"] is True

            os.environ.pop("CLUES_API_URL", None)
            assert json.loads(request("/api/clues", expected=HTTPStatus.SERVICE_UNAVAILABLE)[1])["ok"] is False
            os.environ["CLUES_API_URL"] = "http://clues.invalid"
            assert json.loads(request("/api/clues?status=unused")[1])["path"].endswith("status=unused")

            app.MONITOR_API_URL = ""
            request("/api/monitor/status", expected=HTTPStatus.SERVICE_UNAVAILABLE)
            app.MONITOR_API_URL = "http://monitor.invalid"
            assert json.loads(request("/api/monitor/status")[1])["path"] == "/api/monitor/status"
            assert json.loads(request("/api/analytics/export.json")[1])["ok"] is True
            assert request("/api/analytics/export.md")[1] == b"# analytics"

            assert request("/videos/mc-01-test.mp4")[1] == b"video-fixture"
            assert request("/thumbnails/item/mc-01-test.jpg")[1] == b"image-fixture"
            assert request("/audio/voice/test.mp3")[1] == b"voice-fixture"
            assert request("/music/test/clip")[1] == b"music-fixture"
            for guarded in ("/videos/%2e%2e%2fsecret.mp4", "/thumbnails/%2e%2e%2fsecret.jpg", "/audio/%2e%2e%2fsecret.mp3", "/missing"):
                request(guarded, expected=HTTPStatus.NOT_FOUND)

            request("/api/job/cancel", {"lane": "generation"})
            request("/api/generate", {"episodeId": "mc-01", "formatId": "clues"})
            request("/api/publishing/config", {"config": config, "nextRunAt": "2026-08-21T12:00:00+00:00"})
            request("/api/publishing/secrets", {"YOUTUBE_CLIENT_ID": "fixture-client"})
            request("/api/tiktok/disconnect", {})
            request("/api/analytics/sync", {})
            request("/api/monitor/check", {})
            request("/api/monitor/events", {"limit": 2})
            request("/api/publish-now", {})
            request("/api/publish-platform", {"episodeId": "mc-01", "platform": "youtube"})
            request("/api/backup", {})
            request("/api/context-snapshot", {})
            request("/api/music/import", {"url": "https://youtu.be/fixture"})
            request("/api/music/delete", {"trackId": "test"})
            request("/api/music/original-starts", {"filename": "Cat.ogg", "starts": ["0:12"]})

            revision = state["revision"]
            for action in ("approve", "unqueue", "reject", "hints", "clear-hints", "audio", "video"):
                request("/api/action", {"episodeId": "mc-02", "action": action})
            assert json.loads(request("/api/state")[1])["revision"] == revision + 1
            unchanged = state["revision"]
            error = json.loads(request("/api/action", {"episodeId": "mc-02", "action": "invalid"}, HTTPStatus.CONFLICT)[1])
            assert error["ok"] is False and state["revision"] == unchanged

            names = {name for name, _value in calls}
            assert {
                "cancel", "generate", "config", "secrets", "disconnect", "analytics", "publish-next",
                "publish-platform", "backup", "snapshot", "music-import", "music-delete", "music-starts",
                "approve", "unqueue", "reject", "hints", "clear-hints",
            } <= names
            log = (app.LOG_DIR / "dashboard.log").read_text(encoding="utf-8")
            assert "fixture-client" not in log
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            os.environ.pop("CLUES_API_URL", None)

    print("ok: dashboard HTTP routes, actions, state transitions, media guards, and isolation")


if __name__ == "__main__":
    main()
