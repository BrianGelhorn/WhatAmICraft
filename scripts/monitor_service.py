#!/usr/bin/env python3
"""Health and error monitoring service for the isolated stack."""

from __future__ import annotations

import json
import os
import re
import threading
import time
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SAFE_SERVICE = re.compile(r"^[a-z0-9][a-z0-9-]{0,49}$")
SECRET_VALUE = re.compile(r"(?i)(token|secret|password|authorization|api[_ -]?key|refresh[_ -]?token)(\s*[:=]\s*)[^\s,;]+")
SECRET_KEY = re.compile(r"(?i)(token|secret|password|authorization|api[_ -]?key|refresh[_ -]?token)")


def redact(value: str) -> str:
    return SECRET_VALUE.sub(r"\1\2***", value)[:500]


def redact_context(value: object) -> object:
    if isinstance(value, dict):
        return {
            str(key): "***" if SECRET_KEY.search(str(key)) else redact_context(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_context(item) for item in value]
    return redact(str(value))


class MonitorService:
    def __init__(self, events_path: Path | None = None, targets: list[dict] | None = None) -> None:
        self.events_path = events_path or Path(os.getenv("MONITOR_EVENTS_PATH", str(ROOT / "out/monitor/events.jsonl")))
        self.targets = targets or self._configured_targets()
        self._lock = threading.Lock()
        self._status: dict[str, dict] = {}

    @staticmethod
    def _configured_targets() -> list[dict]:
        return [
            {"service": "dashboard", "url": f"{os.getenv('MONITOR_DASHBOARD_URL', 'http://dashboard:8787').rstrip('/')}/health", "expected": {200}},
            {"service": "clues-api", "url": f"{os.getenv('MONITOR_CLUES_URL', 'http://clues-api:8790').rstrip('/')}/health", "expected": {200}},
            {"service": "analytics-api", "url": f"{os.getenv('MONITOR_ANALYTICS_URL', 'http://analytics-api:8791').rstrip('/')}/health", "expected": {200}},
            {"service": "backup-rollback", "url": f"{os.getenv('MONITOR_BACKUP_URL', 'http://backup-rollback:8793').rstrip('/')}/health", "expected": {200}},
            {"service": "media", "url": os.getenv("MONITOR_MEDIA_URL", "http://media"), "expected": set(range(200, 500))},
            {"service": "bot", "heartbeat": os.getenv("MONITOR_BOT_HEARTBEAT", str(ROOT / "out/health/bot")), "maxAge": 120},
            {"service": "publisher-worker", "heartbeat": os.getenv("MONITOR_PUBLISHER_HEARTBEAT", str(ROOT / "out/health/publisher-worker")), "maxAge": 120},
        ]

    def _record(self, service: str, level: str, message: str, context: dict | None = None) -> dict:
        event = {
            "at": datetime.now(timezone.utc).isoformat(),
            "service": service,
            "level": level,
            "message": redact(message),
            "context": redact_context(context or {}),
        }
        with self._lock:
            self.events_path.parent.mkdir(parents=True, exist_ok=True)
            previous = self.events_path.read_text(encoding="utf-8").splitlines()[-1999:] if self.events_path.exists() else []
            temporary = self.events_path.with_suffix(".jsonl.tmp")
            temporary.write_text("\n".join([*previous, json.dumps(event, ensure_ascii=False)]) + "\n", encoding="utf-8")
            temporary.replace(self.events_path)
        return event

    def record_event(self, service: str, level: str, message: str, context: dict | None = None) -> dict:
        if not isinstance(service, str) or not SAFE_SERVICE.fullmatch(service):
            raise ValueError("service inválido")
        if level not in {"info", "warning", "error"}:
            raise ValueError("level inválido")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message inválido")
        if context is not None and (not isinstance(context, dict) or len(context) > 20):
            raise ValueError("context inválido")
        return self._record(service, level, message, context)

    def check_now(self) -> dict:
        checked_at = datetime.now(timezone.utc).isoformat()
        current = {}
        for target in self.targets:
            started = time.monotonic()
            if target.get("heartbeat"):
                heartbeat = Path(target["heartbeat"])
                age = time.time() - heartbeat.stat().st_mtime if heartbeat.exists() else None
                if age is None:
                    status, detail, code = "down", "heartbeat missing", None
                elif age > target["maxAge"]:
                    status, detail, code = "down", f"heartbeat stale ({age:.0f}s)", None
                else:
                    status, detail, code = "up", f"heartbeat {age:.0f}s", None
            else:
                try:
                    with urlopen(Request(target["url"], headers={"User-Agent": "whatamicraft-monitor"}), timeout=3) as response:
                        code = response.status
                    status = "up" if code in target["expected"] else "degraded"
                    detail = f"HTTP {code}"
                except HTTPError as error:
                    code = error.code
                    status = "up" if code in target["expected"] else "degraded"
                    detail = f"HTTP {code}"
                except (URLError, TimeoutError, OSError) as error:
                    code = None
                    status = "down"
                    detail = redact(str(error))
            result = {
                "service": target["service"],
                "status": status,
                "detail": detail,
                "httpStatus": code,
                "latencyMs": round((time.monotonic() - started) * 1000, 1),
                "checkedAt": checked_at,
            }
            previous = self._status.get(target["service"])
            if previous and previous["status"] != status:
                self._record(target["service"], "error" if status == "down" else "info", f"Estado cambió a {status}: {detail}", {"previous": previous["status"]})
            current[target["service"]] = result
        with self._lock:
            self._status = current
        return self.status()

    def status(self) -> dict:
        with self._lock:
            services = list(self._status.values())
        return {"checkedAt": max((item["checkedAt"] for item in services), default=None), "ok": bool(services) and all(item["status"] == "up" for item in services), "services": services}

    def events(self, limit: int = 100) -> list[dict]:
        limit = min(200, max(1, limit))
        if not self.events_path.exists():
            return []
        result = []
        for line in self.events_path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]:
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return

    @property
    def monitor(self) -> MonitorService:
        return self.server.monitor  # type: ignore[attr-defined]

    def send_json(self, value: dict, status: int = 200) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self, maximum: int = 16 * 1024) -> dict:
        size = int(self.headers.get("Content-Length", "0"))
        if size <= 0 or size > maximum:
            raise ValueError("Carga vacía o demasiado grande")
        value = json.loads(self.rfile.read(size))
        if not isinstance(value, dict):
            raise ValueError("El cuerpo debe ser un objeto JSON")
        return value

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/health":
                state = self.monitor.status()
                self.send_json({"ok": True, "service": "monitor", "dependenciesOk": state["ok"], "status": state})
            elif parsed.path == "/api/monitor/status":
                self.send_json(self.monitor.status())
            elif parsed.path == "/api/monitor/check":
                self.send_json(self.monitor.check_now())
            elif parsed.path == "/api/monitor/events":
                limit = int(parse_qs(parsed.query).get("limit", ["100"])[0])
                self.send_json({"items": self.monitor.events(limit)})
            else:
                self.send_json({"ok": False, "error": "Ruta no encontrada"}, HTTPStatus.NOT_FOUND)
        except (ValueError, json.JSONDecodeError) as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except Exception:
            self.send_json({"ok": False, "error": "No se pudo consultar el monitoreo"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        if urlparse(self.path).path not in {"/api/monitor/check", "/api/monitor/events"}:
            self.send_json({"ok": False, "error": "Ruta no encontrada"}, HTTPStatus.NOT_FOUND)
            return
        try:
            if urlparse(self.path).path == "/api/monitor/check":
                self.send_json(self.monitor.check_now())
                return
            value = self._body()
            event = self.monitor.record_event(value.get("service"), value.get("level", "error"), value.get("message"), value.get("context"))
            self.send_json({"ok": True, "event": event}, HTTPStatus.CREATED)
        except (ValueError, json.JSONDecodeError) as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except Exception:
            self.send_json({"ok": False, "error": "No se pudo registrar el evento"}, HTTPStatus.INTERNAL_SERVER_ERROR)


def make_server(host: str, port: int, monitor: MonitorService | None = None) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), Handler)
    server.monitor = monitor or MonitorService()  # type: ignore[attr-defined]
    return server


def main() -> None:
    monitor = MonitorService()
    def poll() -> None:
        interval = max(5, int(os.getenv("MONITOR_INTERVAL_SECONDS", "60")))
        while True:
            try:
                monitor.check_now()
            except Exception as error:
                monitor.record_event("monitor", "error", f"No se pudo comprobar los servicios: {error}")
            time.sleep(interval)

    threading.Thread(target=poll, daemon=True).start()
    server = make_server(os.getenv("MONITOR_HOST", "0.0.0.0"), int(os.getenv("MONITOR_PORT", "8792")), monitor)
    print(f"Monitor activo en el puerto {server.server_port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
