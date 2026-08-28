#!/usr/bin/env python3
"""End-to-end offline checks for Telegram bot commands, callbacks, and alerts."""

from __future__ import annotations

import json
import os
import shutil
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import review.bot as bot
import review.telegram as telegram

ROOT = Path(__file__).resolve().parents[1]


class FakeTelegramHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return

    def do_POST(self) -> None:
        size = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(size)
        self.server.requests.append((self.path, body))  # type: ignore[attr-defined]
        reply = self.server.replies.pop(0) if self.server.replies else {"ok": True, "result": {"message_id": 1}}  # type: ignore[attr-defined]
        encoded = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class FakeDashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return

    def do_POST(self) -> None:
        size = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(size)
        self.server.requests.append((self.path, json.loads(body or b"{}")))  # type: ignore[attr-defined]
        encoded = b'{"ok": true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def server_for(handler: type[BaseHTTPRequestHandler]) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.requests = []  # type: ignore[attr-defined]
    server.replies = []  # type: ignore[attr-defined]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def telegram_messages(server: ThreadingHTTPServer) -> list[dict]:
    return [json.loads(body) for path, body in server.requests if path.endswith("/sendMessage")]


def main() -> None:
    fixture = ROOT / "out/test-telegram-bot"
    shutil.rmtree(fixture, ignore_errors=True)
    (fixture / "videos").mkdir(parents=True)
    video = fixture / "videos/mc-03-stone.mp4"
    video.write_bytes(b"telegram-review-video")
    published_video = fixture / "videos/mc-04-apple.mp4"
    published_video.write_bytes(b"telegram-published-video")
    legacy_video = fixture / "videos/mc-05-dirt.mp4"
    legacy_video.write_bytes(b"telegram-legacy-video")
    episodes = [
        {"id": "mc-02", "target": {"id": "diamond", "kind": "item", "display_name": "Diamond"}},
        {"id": "mc-03", "target": {"id": "stone", "kind": "block", "display_name": "Stone"}},
        {"id": "mc-04", "target": {"id": "apple", "kind": "food", "display_name": "Apple"}},
        {"id": "mc-05", "target": {"id": "dirt", "kind": "block", "display_name": "Dirt"}},
    ]
    queue: list[dict] = []
    hints: list[dict] = []
    jobs = {
        "main": {"status": "idle", "label": "", "lines": []},
        "generation": {"status": "idle", "label": "", "lines": []},
        "publishing": {"status": "idle", "label": "", "lines": []},
    }
    state = {
        "videos": {
            "mc-04": {
                "sha256": bot.sha256(published_video),
                "platforms": {"youtube": {"id": "yt-04", "url": "https://youtube.test/yt-04"}},
            },
        },
    }
    telegram_server = server_for(FakeTelegramHandler)
    dashboard_server = server_for(FakeDashboardHandler)
    original = {
        "root": bot.ROOT,
        "offset": bot.OFFSET_PATH,
        "log_path": bot.LOG_PATH,
        "alert_state": bot.ALERT_STATE_PATH,
        "dashboard": bot.DASHBOARD_URL,
        "logs": bot.MONITORED_LOGS,
        "episodes": bot.all_episodes,
        "video_path": bot.video_path,
        "current_template_video_names": bot.current_template_video_names,
        "queue_items": bot.queue_items,
        "queue_episode": bot.queue_episode,
        "remove_queue_item": bot.remove_queue_item,
        "pending_hints": bot.pending_hints_items,
        "pend_hints": bot.pend_hints,
        "clear_hints": bot.clear_hints,
        "published": bot.publishing_state,
        "read_job": bot.read_job,
        "generation_schedule": bot.load_generation_schedule,
        "publish_schedule": bot.load_schedule,
    }

    def queue_episode(episode_id: str) -> None:
        if not any(item["episodeId"] == episode_id for item in queue):
            queue.append({"episodeId": episode_id, "status": "pending", "updatedAt": "now"})

    def remove_queue_item(episode_id: str) -> None:
        queue[:] = [item for item in queue if item["episodeId"] != episode_id]

    def pend_hints(episode_id: str) -> None:
        if not any(item["episodeId"] == episode_id for item in hints):
            hints.append({"episodeId": episode_id})

    def clear_hints(episode_id: str) -> None:
        hints[:] = [item for item in hints if item["episodeId"] != episode_id]

    try:
        os.environ.update({
            "TELEGRAM_BOT_TOKEN": "ci-token",
            "TELEGRAM_REVIEW_CHAT_ID": "42",
            "WHATAMICRAFT_TEST_TELEGRAM": "1",
            "TELEGRAM_API_BASE_URL": f"http://127.0.0.1:{telegram_server.server_port}",
        })
        bot.ROOT = fixture
        bot.OFFSET_PATH = fixture / "telegram-offset.txt"
        bot.LOG_PATH = fixture / "logs/bot.log"
        bot.ALERT_STATE_PATH = fixture / "telegram-alert-state.json"
        bot.DASHBOARD_URL = f"http://127.0.0.1:{dashboard_server.server_port}"
        bot.MONITORED_LOGS = (fixture / "logs/generator.log",)
        bot.all_episodes = lambda: episodes
        bot.video_path = lambda episode, _root: fixture / "videos" / f"{episode['id']}-{episode['target']['id']}.mp4"
        bot.current_template_video_names = lambda _root: {"mc-02-diamond.mp4", "mc-03-stone.mp4", "mc-04-apple.mp4"}
        bot.queue_items = lambda: list(queue)
        bot.queue_episode = queue_episode
        bot.remove_queue_item = remove_queue_item
        bot.pending_hints_items = lambda: list(hints)
        bot.pend_hints = pend_hints
        bot.clear_hints = clear_hints
        bot.publishing_state = lambda: state
        bot.read_job = lambda lane="main": jobs[lane]
        bot.load_generation_schedule = lambda: {"nextRunAt": "tomorrow"}
        bot.load_schedule = lambda: {"nextRunAt": "later"}

        bot.handle_message({"chat": {"id": 42}, "text": "/estado"})
        assert "ESTADO DE PRODUCCIÓN" in telegram_messages(telegram_server)[-1]["text"]

        bot.handle_message({"chat": {"id": 42}, "text": "/disponibles"})
        available = telegram_messages(telegram_server)[-1]
        assert "mc-02" in available["text"] and "generate:mc-02" in json.dumps(available)
        bot.handle_callback({"id": "cb-generate", "message": {"chat": {"id": 42}}, "data": "generate:mc-02"})
        assert ("/api/action", {"episodeId": "mc-02", "action": "audio"}) in dashboard_server.requests

        bot.handle_message({"chat": {"id": 42}, "text": "/por_aprobar"})
        assert "mc-03" in telegram_messages(telegram_server)[-1]["text"]
        assert "mc-05" not in telegram_messages(telegram_server)[-1]["text"]
        bot.handle_callback({"id": "cb-send", "message": {"chat": {"id": 42}}, "data": "sendvideo:mc-03"})
        assert any(path.endswith("/sendVideo") and b"telegram-review-video" in body for path, body in telegram_server.requests)
        bot.handle_callback({"id": "cb-accept", "message": {"chat": {"id": 42}}, "data": "accept:mc-03"})
        assert queue and queue[0]["status"] == "pending"

        bot.handle_message({"chat": {"id": 42}, "text": "/cola"})
        assert "mc-03" in telegram_messages(telegram_server)[-1]["text"]
        bot.handle_message({"chat": {"id": 42}, "text": "/sacar mc-03"})
        assert not queue
        bot.handle_message({"chat": {"id": 42}, "text": "/aprobar mc-03"})
        bot.handle_message({"chat": {"id": 42}, "text": "/pistas mc-03"})
        assert hints == [{"episodeId": "mc-03"}]
        bot.handle_message({"chat": {"id": 42}, "text": "/limpiar_pistas mc-03"})
        assert not hints
        bot.handle_message({"chat": {"id": 42}, "text": "/regenerar mc-03 video"})
        assert ("/api/action", {"episodeId": "mc-03", "action": "video"}) in dashboard_server.requests
        bot.handle_message({"chat": {"id": 42}, "text": "/publicar"})
        bot.handle_message({"chat": {"id": 42}, "text": "/cancelar"})
        assert ("/api/publish-now", {}) in dashboard_server.requests
        assert ("/api/job/cancel", {}) in dashboard_server.requests

        bot.handle_message({"chat": {"id": 42}, "text": "/publicados"})
        assert "mc-04" in telegram_messages(telegram_server)[-1]["text"] and "youtube.test" in telegram_messages(telegram_server)[-1]["text"]
        generated = fixture / "videos/mc-02-diamond.mp4"
        generated.write_bytes(b"telegram-generated-video")
        jobs["generation"] = {"status": "completed", "label": "Generación automática mc-02", "lines": []}
        bot.notify_generation_done(jobs["generation"], {})
        assert any(path.endswith("/sendVideo") and b"mc-02" in body for path, body in telegram_server.requests)
        assert "Terminó Generación automática mc-02" in telegram_messages(telegram_server)[-1]["text"]
        bot.handle_message({"chat": {"id": 99}, "text": "/start"})
        assert "no está autorizado" in telegram_messages(telegram_server)[-1]["text"]
        before = len(telegram_server.requests)
        bot.handle_message({"chat": {"id": 99}, "text": "/estado"})
        assert len(telegram_server.requests) == before

        error_log = fixture / "logs/generator.log"
        error_log.parent.mkdir(parents=True, exist_ok=True)
        bot.monitor_errors()
        error_log.write_text("ERROR render synthetic failure\n", encoding="utf-8")
        bot.monitor_errors()
        assert "ERROR DETECTADO" in telegram_messages(telegram_server)[-1]["text"]

        bot.handle_callback({"id": "cb-unknown", "message": {"chat": {"id": 42}}, "data": "unknown:value"})
        assert "Error:" in telegram_messages(telegram_server)[-1]["text"]

        sent = []
        original_tell = bot.tell
        original_log = bot.log
        bot.tell = lambda chat_id, text, keyboard=None: sent.append((chat_id, text))
        bot.log = lambda _text: None
        try:
            outage = {}
            bot.notify_telegram_failure(RuntimeError("dns"), outage)
            bot.notify_telegram_failure(RuntimeError("dns"), outage)
            assert len(sent) == 1
            bot.notify_telegram_recovery(outage)
            assert len(sent) == 2 and "restaurada" in sent[-1][1]
            bot.notify_telegram_recovery(outage)
            assert len(sent) == 2
            assert [bot.next_retry_delay(delay) for delay in (5, 10, 20, 40, 60)] == [10, 20, 40, 60, 60]
        finally:
            bot.tell = original_tell
            bot.log = original_log
    finally:
        telegram_server.shutdown()
        dashboard_server.shutdown()
        telegram_server.server_close()
        dashboard_server.server_close()
        for name, value in original.items():
            setattr(bot, {
                "root": "ROOT", "offset": "OFFSET_PATH", "log_path": "LOG_PATH", "alert_state": "ALERT_STATE_PATH",
                "dashboard": "DASHBOARD_URL", "logs": "MONITORED_LOGS", "episodes": "all_episodes", "video_path": "video_path", "current_template_video_names": "current_template_video_names",
                "queue_items": "queue_items", "queue_episode": "queue_episode", "remove_queue_item": "remove_queue_item",
                "pending_hints": "pending_hints_items", "pend_hints": "pend_hints", "clear_hints": "clear_hints",
                "published": "publishing_state", "read_job": "read_job", "generation_schedule": "load_generation_schedule",
                "publish_schedule": "load_schedule",
            }[name], value)
        shutil.rmtree(fixture, ignore_errors=True)

    print("ok: Telegram commands, approvals, video delivery, dashboard actions, authorization, and alerts")


if __name__ == "__main__":
    main()
