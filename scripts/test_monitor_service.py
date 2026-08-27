#!/usr/bin/env python3
"""Behavior checks for monitoring, recovery events, redaction, and HTTP API."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

from monitor_service import MonitorService, make_server

ROOT = Path(__file__).resolve().parents[1]


class FakeHandler(BaseHTTPRequestHandler):
    statuses = {"/health": 200, "/media": 200}

    def do_GET(self) -> None:
        status = self.statuses.get(self.path, 404)
        self.send_response(status)
        self.end_headers()

    def log_message(self, *_args: object) -> None:
        return


def json_request(url: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(url, data=body, method=method, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read())


fake = ThreadingHTTPServer(("127.0.0.1", 0), FakeHandler)
threading.Thread(target=fake.serve_forever, daemon=True).start()
fake_url = f"http://127.0.0.1:{fake.server_port}"

def main() -> None:
    directory = ROOT / "out"
    events_path = Path(directory) / "events.jsonl"
    events_path.unlink(missing_ok=True)
    heartbeat = Path(directory) / "test-bot-heartbeat"
    heartbeat.parent.mkdir(parents=True, exist_ok=True)
    heartbeat.touch()
    monitor = MonitorService(
        events_path=events_path,
        targets=[
            {"service": "fake-api", "url": f"{fake_url}/health", "expected": {200}},
            {"service": "fake-media", "url": f"{fake_url}/media", "expected": {200, 403}},
            {"service": "fake-bot", "heartbeat": str(heartbeat), "maxAge": 120},
        ],
    )
    assert monitor.check_now()["ok"]
    assert monitor.status()["services"][-1]["status"] == "up"
    FakeHandler.statuses["/health"] = 503
    assert monitor.check_now()["services"][0]["status"] == "degraded"
    FakeHandler.statuses["/health"] = 200
    assert monitor.check_now()["ok"]
    event = monitor.record_event("dashboard", "error", "token=abc password=secret", {"meta": {"access_token": "private"}})
    encoded = json.dumps(event)
    assert "abc" not in encoded and "secret" not in encoded and "private" not in encoded
    assert "***" in encoded
    assert any(item["service"] == "fake-api" for item in monitor.events())

    server = make_server("127.0.0.1", 0, monitor)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monitor_url = f"http://127.0.0.1:{server.server_port}"
    status, health = json_request(f"{monitor_url}/health")
    assert status == 200 and health["service"] == "monitor"
    status, state = json_request(f"{monitor_url}/api/monitor/status")
    assert status == 200 and len(state["services"]) == 3
    status, created = json_request(
        f"{monitor_url}/api/monitor/events",
        method="POST",
        payload={"service": "fake-api", "level": "warning", "message": "recovering"},
    )
    assert status == 201 and created["ok"]
    heartbeat.unlink()
    assert monitor.check_now()["services"][-1]["status"] == "down"
    server.shutdown()
    events_path.unlink(missing_ok=True)
    heartbeat.unlink(missing_ok=True)
    fake.shutdown()
    print("ok: monitoring service checks dependencies, recovery, redaction, and HTTP API")


if __name__ == "__main__":
    main()
