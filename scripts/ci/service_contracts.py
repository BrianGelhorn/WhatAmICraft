#!/usr/bin/env python3
"""Behavior contracts for services that must stay offline in CI."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

from template_artifacts import render_props_path, write_artifact


TEST_ROOT = Path(__file__).resolve().parents[2] / "out" / "ci-service-contracts"


class FakeTelegramHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return

    def do_POST(self) -> None:
        size = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(size)
        self.server.requests.append((self.path, dict(self.headers), body))  # type: ignore[attr-defined]
        reply = self.server.replies.pop(0) if self.server.replies else {  # type: ignore[attr-defined]
            "ok": True,
            "result": {"message_id": 1},
        }
        encoded = json.dumps(reply).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def fake_telegram_server() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeTelegramHandler)
    server.requests = []  # type: ignore[attr-defined]
    server.replies = []  # type: ignore[attr-defined]
    return server


def bot_contract() -> None:
    import review.bot as bot
    import review.telegram as telegram

    server = fake_telegram_server()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        os.environ["TELEGRAM_BOT_TOKEN"] = "ci-token"
        os.environ["TELEGRAM_REVIEW_CHAT_ID"] = "42"
        os.environ["WHATAMICRAFT_TEST_TELEGRAM"] = "1"
        os.environ["TELEGRAM_API_BASE_URL"] = f"http://127.0.0.1:{server.server_port}"
        telegram.send_message(42, "estado", [[{"text": "Abrir", "callback_data": "status"}]])
        video = TEST_ROOT / "bot" / "mc-ci-test.mp4"
        video.parent.mkdir(parents=True, exist_ok=True)
        video.write_bytes(b"valid-ci-video")
        telegram.send_for_review("mc-01", "Stone", video)

        bot.send_message = telegram.send_message
        bot.handle_message({"chat": {"id": 42}, "text": "/ayuda"})
        requests = server.requests  # type: ignore[attr-defined]
        assert [path.rsplit("/", 1)[-1] for path, _headers, _body in requests] == [
            "sendMessage", "sendVideo", "sendMessage"
        ]
        assert b"estado" in requests[0][2]
        assert b"valid-ci-video" in requests[1][2]
        assert b"/generar mc-11" in requests[2][2]
        assert b"ci-token" not in requests[2][2]

        server.replies.append({"ok": False, "description": "synthetic failure"})  # type: ignore[attr-defined]
        try:
            telegram.send_message(42, "should fail")
        except RuntimeError as error:
            assert "synthetic failure" in str(error)
            assert "ci-token" not in str(error)
        else:
            raise AssertionError("Telegram failure response was accepted")
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        shutil.rmtree(TEST_ROOT / "bot", ignore_errors=True)

    print("ok: bot command routing, Telegram payloads, and failure handling")


def publisher_contract() -> None:
    import publish as publisher
    import publish_worker as worker

    root = TEST_ROOT / "publisher"
    shutil.rmtree(root, ignore_errors=True)
    try:
        output = root / "out" / "episodes"
        output.mkdir(parents=True)
        video = output / "mc-01-stone.mp4"
        video.write_bytes(b"publisher-fixture")
        thumbnail = root / "out" / "thumbnails" / "item" / "default" / "mc-01-stone.vertical.jpg"
        thumbnail.parent.mkdir(parents=True)
        thumbnail.write_bytes(b"publisher-thumbnail")
        props = render_props_path(video.stem, "video", root)
        props.parent.mkdir(parents=True, exist_ok=True)
        props.write_text(json.dumps({"config": {}}), encoding="utf-8")
        write_artifact(
            episode_id="mc-01",
            video=video,
            config={},
            thumbnail=thumbnail,
            root=root,
        )
        episode = {
            "id": "mc-01",
            "target": {"id": "stone", "kind": "item", "display_name": "Stone"},
        }
        config = {
            "title": "Guess {kind}",
            "caption": "Guess it",
            "hashtags": ["minecraft"],
            "platforms": {"fake": {"enabled": True}},
        }
        state = {"videos": {}}
        queue = {"ids": ["mc-01"], "status": None, "error": None}
        calls = []

        original = {
            "output": publisher.OUTPUT_DIR,
            "root": publisher.ROOT,
            "lock": publisher.PUBLISH_LOCK,
            "episodes": publisher.episodes,
            "config": publisher.load_config,
            "runtime": publisher.apply_runtime,
            "platforms": publisher.enabled_platforms,
            "queue_ids": publisher.pending_queue_ids,
            "state": publisher.publishing_state,
            "save": publisher.save_published_platform,
            "queue_status": publisher.set_queue_status,
            "publishers": publisher.PUBLISHERS,
        }
        try:
            publisher.OUTPUT_DIR = output
            publisher.ROOT = root
            publisher.PUBLISH_LOCK = root / "out" / "publishing.lock"
            publisher.episodes = lambda: [episode]
            publisher.load_config = lambda: config
            publisher.apply_runtime = lambda _config: None
            publisher.enabled_platforms = lambda _config: ["fake"]
            publisher.pending_queue_ids = lambda: list(queue["ids"])
            publisher.publishing_state = lambda: state
            publisher.save_published_platform = lambda episode_id, fingerprint, platform, payload: state["videos"].setdefault(episode_id, {"sha256": fingerprint, "platforms": {}})["platforms"].update({platform: payload})
            publisher.set_queue_status = lambda _episode_id, status, error=None: queue.update(status=status, error=error)

            def provider(item):
                calls.append((item.title, item.description, item.video.read_bytes()))
                return {"id": "fake-1"}

            publisher.PUBLISHERS = {"fake": provider}
            args = argparse.Namespace(
                episode=None, queue=True, all=False, platform=None, limit=1, force=False, dry_run=False
            )
            assert publisher.run(args) == 0
            assert calls == [("Guess Item", "Guess it\n\n#minecraft", b"publisher-fixture")]
            assert state["videos"]["mc-01"]["platforms"]["fake"]["id"] == "fake-1"
            assert queue["status"] == "completed"

            state["videos"] = {}
            queue.update(status=None, error=None)

            def broken_provider(_item):
                raise RuntimeError("provider unavailable")

            publisher.PUBLISHERS = {"fake": broken_provider}
            assert publisher.run(args) == 1
            assert queue["status"] == "failed"
            assert "provider unavailable" in queue["error"]
            assert state["videos"]["mc-01"]["platforms"] == {}

            worker_original = {
                "episodes": worker.episodes,
                "video_for": worker.video_for,
                "names": worker.current_template_video_names,
                "state": worker.publishing_state,
                "queue_ids": worker.pending_queue_ids,
                "run_logged": worker.run_logged,
                "notify": worker.notify,
            }
            try:
                worker.episodes = lambda: [episode]
                worker.video_for = lambda _episode: video
                worker.current_template_video_names = lambda: {video.name}
                worker.publishing_state = lambda: {"videos": {}}
                worker.pending_queue_ids = lambda: []
                inventory = worker.inventory()
                assert inventory["candidates"] == ["mc-01"]
                commands = []
                worker.run_logged = lambda command, *_args: commands.append(command) or SimpleNamespace(returncode=0)
                worker.notify = lambda _text: None
                assert worker.publish_or_repost(config, {"pending": ["mc-01"]})
                assert "--queue" in commands[0] and "--limit" in commands[0]
            finally:
                for name, value in worker_original.items():
                    setattr(worker, name, value)
        finally:
            for name, value in original.items():
                setattr(publisher, {"output": "OUTPUT_DIR", "root": "ROOT", "lock": "PUBLISH_LOCK", "episodes": "episodes", "config": "load_config", "runtime": "apply_runtime", "platforms": "enabled_platforms", "queue_ids": "pending_queue_ids", "state": "publishing_state", "save": "save_published_platform", "queue_status": "set_queue_status", "publishers": "PUBLISHERS"}[name], value)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("ok: publisher queue, provider payload, completion, and failure state")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bot", action="store_true")
    parser.add_argument("--publisher", action="store_true")
    args = parser.parse_args()
    if not args.bot and not args.publisher:
        parser.error("choose --bot or --publisher")
    if args.bot:
        bot_contract()
    if args.publisher:
        publisher_contract()


if __name__ == "__main__":
    main()
