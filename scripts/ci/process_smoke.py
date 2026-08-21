#!/usr/bin/env python3
"""Run the real Telegram bot process against an isolated fake Telegram API."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]


class FakeTelegramHandler(BaseHTTPRequestHandler):
    updates_served = False
    requests: list[tuple[str, bytes]] = []

    def log_message(self, *_args: object) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        path = urlparse(self.path).path
        type(self).requests.append((path, body))
        if path.endswith("/getUpdates") and not type(self).updates_served:
            type(self).updates_served = True
            result = [{"update_id": 1, "message": {"chat": {"id": 42}, "text": "/estado"}}]
        else:
            result = []
        payload = {"ok": True, "result": result}
        if path.endswith("/sendMessage"):
            payload["result"] = {"message_id": 1}
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class QuietHTTPServer(ThreadingHTTPServer):
    def handle_error(self, _request: object, _client_address: object) -> None:
        return


def main() -> None:
    isolated_root = ROOT / "out"
    isolated_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="whatamicraft-bot-process-", dir=isolated_root) as temporary:
        sandbox = Path(temporary)
        shutil.copytree(ROOT / "scripts", sandbox / "scripts")
        (sandbox / "data").mkdir()
        (sandbox / "data" / "quiz-copy-episodes.json").write_text('{"episodes": []}\n', encoding="utf-8")
        (sandbox / "data" / "used-targets.json").write_text('{"targets": []}\n', encoding="utf-8")
        (sandbox / "out" / "logs").mkdir(parents=True)

        FakeTelegramHandler.updates_served = False
        FakeTelegramHandler.requests = []
        server = QuietHTTPServer(("127.0.0.1", 0), FakeTelegramHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        process = None
        try:
            env = {
                **os.environ,
                "PYTHONUNBUFFERED": "1",
                "WHATAMICRAFT_TEST_TELEGRAM": "1",
                "TELEGRAM_API_BASE_URL": f"http://127.0.0.1:{server.server_port}",
                "TELEGRAM_BOT_TOKEN": "ci-token",
                "TELEGRAM_REVIEW_CHAT_ID": "42",
            }
            process = subprocess.Popen(
                [sys.executable, "-u", str(sandbox / "scripts/review/bot.py")],
                cwd=sandbox,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if any(path.endswith("/sendMessage") for path, _ in FakeTelegramHandler.requests):
                    break
                if process.poll() is not None:
                    break
                time.sleep(0.1)
            if not any(path.endswith("/getUpdates") for path, _ in FakeTelegramHandler.requests):
                process.terminate()
                output, _ = process.communicate(timeout=5)
                safe_output = (output or "").replace("ci-token", "<redacted>")[-2000:]
                raise AssertionError(f"bot process made no Telegram request: {safe_output}")
            messages = [
                json.loads(body.decode("utf-8"))
                for path, body in FakeTelegramHandler.requests
                if path.endswith("/sendMessage")
            ]
            assert messages and "ESTADO DE PRODUCCIÓN" in messages[0]["text"]
            captured = "\n".join(body.decode("utf-8", "replace") for _, body in FakeTelegramHandler.requests)
            assert "ci-token" not in captured
        finally:
            if process is not None:
                process.terminate()
                try:
                    output, _ = process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    output, _ = process.communicate(timeout=5)
                assert "ci-token" not in (output or "")
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    print("ok: real bot process handles an isolated status request without leaking its token")


if __name__ == "__main__":
    main()
