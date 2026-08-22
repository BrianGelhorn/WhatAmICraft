#!/usr/bin/env python3
"""HTTP service that owns analytics synchronization and exports."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

import analytics  # noqa: E402
import state_db  # noqa: E402


class AnalyticsService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = {"status": "idle", "startedAt": None, "finishedAt": None, "error": None}

    def snapshot(self) -> dict:
        return analytics.build_snapshot()

    def sync_status(self) -> dict:
        with self._lock:
            state = dict(self._state)
        state["platforms"] = state_db.load_flag("analytics_sync_status", {})
        return state

    def start_sync(self) -> dict:
        with self._lock:
            if self._state["status"] == "running":
                raise RuntimeError("Las estadísticas ya se están actualizando")
            started = datetime.now(timezone.utc).isoformat()
            self._state = {"status": "running", "startedAt": started, "finishedAt": None, "error": None}
        threading.Thread(target=self._run_sync, daemon=True).start()
        return self.sync_status()

    def _run_sync(self) -> None:
        error = None
        try:
            analytics.sync_all()
        except Exception as exc:  # sync_all records per-platform failures; this catches service-level failures.
            error = analytics._safe_error(exc)
        with self._lock:
            self._state.update({
                "status": "failed" if error else "completed",
                "finishedAt": datetime.now(timezone.utc).isoformat(),
                "error": error,
            })


def scheduler(service: AnalyticsService) -> None:
    while True:
        try:
            service.start_sync()
        except RuntimeError:
            pass
        threading.Event().wait(6 * 60 * 60)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return

    @property
    def service(self) -> AnalyticsService:
        return self.server.service  # type: ignore[attr-defined]

    def send_json(self, value: dict, status: int = 200) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, value: str, status: int = 200) -> None:
        body = value.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/markdown; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/health":
                self.send_json({"ok": True, "service": "analytics-api", "sync": self.service.sync_status()})
            elif path == "/api/analytics":
                self.send_json(self.service.snapshot())
            elif path == "/api/analytics/sync":
                self.send_json(self.service.sync_status())
            elif path == "/api/analytics/export.json":
                self.send_json(analytics.write_exports())
            elif path == "/api/analytics/export.md":
                analytics.write_exports()
                self.send_text((analytics.EXPORT_DIR / "gpt-analytics.md").read_text(encoding="utf-8"))
            else:
                self.send_json({"ok": False, "error": "Ruta no encontrada"}, HTTPStatus.NOT_FOUND)
        except Exception:
            self.send_json({"ok": False, "error": "No se pudo consultar analytics"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/analytics/trends":
            try:
                payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
                self.send_json({"ok": True, "signals": analytics.import_trend_signals(payload)})
            except ValueError as error:
                self.send_json({"ok": False, "error": str(error)}, HTTPStatus.CONFLICT)
            return
        if path == "/api/analytics/recommendation":
            try:
                payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
                recommendation = state_db.set_analytics_recommendation_status(str(payload.get("id", "")), str(payload.get("status", "")))
                self.send_json({"ok": True, "recommendation": recommendation})
            except ValueError as error:
                self.send_json({"ok": False, "error": str(error)}, HTTPStatus.CONFLICT)
            return
        if path != "/api/analytics/sync":
            self.send_json({"ok": False, "error": "Ruta no encontrada"}, HTTPStatus.NOT_FOUND)
            return
        try:
            self.send_json({"ok": True, "sync": self.service.start_sync()}, HTTPStatus.ACCEPTED)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.CONFLICT)
        except Exception:
            self.send_json({"ok": False, "error": "No se pudo iniciar analytics"}, HTTPStatus.INTERNAL_SERVER_ERROR)


def make_server(host: str, port: int, service: AnalyticsService | None = None) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), Handler)
    server.service = service or AnalyticsService()  # type: ignore[attr-defined]
    return server


def main() -> None:
    service = AnalyticsService()
    analytics.write_exports()
    threading.Thread(target=scheduler, args=(service,), daemon=True).start()
    server = make_server(os.getenv("ANALYTICS_HOST", "0.0.0.0"), int(os.getenv("ANALYTICS_PORT", "8791")), service)
    print(f"Analytics API activo en el puerto {server.server_port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
