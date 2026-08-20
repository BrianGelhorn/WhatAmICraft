#!/usr/bin/env python3
"""Daily backup and guarded rollback service for the isolated stack."""

from __future__ import annotations

import hmac
import json
import os
import threading
import time
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

import backup_state


ROOT = Path(os.getenv("BACKUP_ROOT", "/app"))
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", str(ROOT / "backups" / "ops")))
DEFAULT_KEEP = max(int(os.getenv("BACKUP_KEEP", "14")), 1)
DEFAULT_INTERVAL = max(int(os.getenv("BACKUP_INTERVAL_SECONDS", "86400")), 60)
MAX_BODY_BYTES = 4096


def utc_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


class BackupService:
    def __init__(
        self,
        root: Path = ROOT,
        backup_dir: Path = BACKUP_DIR,
        keep: int = DEFAULT_KEEP,
        interval_seconds: int = DEFAULT_INTERVAL,
        admin_token: str = "",
    ) -> None:
        self.root = root.resolve()
        self.backup_dir = backup_dir.resolve()
        self.keep = max(keep, 2)  # preserve the selected backup while creating the pre-restore safety copy
        self.interval_seconds = max(interval_seconds, 60)
        self.admin_token = admin_token
        self.lock = threading.RLock()
        self.last_error: str | None = None
        self.last_action: dict | None = None
        self.next_due_at: float | None = None

    def _files(self) -> list[Path]:
        return sorted(self.backup_dir.glob("state-*.zip"), key=lambda item: item.stat().st_mtime, reverse=True)

    def list_backups(self) -> list[dict]:
        result = []
        for path in self._files():
            item = path.stat()
            result.append(
                {
                    "name": path.name,
                    "size": item.st_size,
                    "createdAt": utc_iso(item.st_mtime),
                }
            )
        return result

    def _resolve_backup(self, name: str) -> Path:
        if Path(name).name != name or not name.startswith("state-") or not name.endswith(".zip"):
            raise ValueError("backup inválido")
        candidate = (self.backup_dir / name).resolve()
        if candidate.parent != self.backup_dir or not candidate.is_file():
            raise FileNotFoundError("backup no encontrado")
        return candidate

    def _record(self, action: str, path: Path | None = None) -> dict:
        self.last_action = {
            "action": action,
            "backup": path.name if path else None,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        return self.last_action

    def create_backup(self, action: str = "manual") -> dict:
        with self.lock:
            try:
                path = backup_state.backup(
                    keep=self.keep,
                    quiet=True,
                    root=self.root,
                    backup_dir=self.backup_dir,
                )
                self.last_error = None
                self.next_due_at = time.time() + self.interval_seconds
                return self._record(action, path)
            except Exception as exc:
                self.last_error = f"{type(exc).__name__}: {exc}"
                raise

    def create_if_due(self) -> dict | None:
        with self.lock:
            latest = self._files()[0] if self._files() else None
            if latest and time.time() - latest.stat().st_mtime < self.interval_seconds:
                self.next_due_at = latest.stat().st_mtime + self.interval_seconds
                return None
        return self.create_backup("scheduled")

    def restore(self, name: str) -> dict:
        with self.lock:
            source = self._resolve_backup(name)
            self.create_backup("pre-restore")
            try:
                backup_state.restore(source, root=self.root)
                self.last_error = None
                return self._record("restore", source)
            except Exception as exc:
                self.last_error = f"{type(exc).__name__}: {exc}"
                raise

    def health(self) -> dict:
        with self.lock:
            backups = self.list_backups()
            return {
                "ok": self.last_error is None,
                "service": "backup-rollback",
                "backupCount": len(backups),
                "latestBackup": backups[0] if backups else None,
                "keep": self.keep,
                "intervalSeconds": self.interval_seconds,
                "nextDueAt": utc_iso(self.next_due_at) if self.next_due_at else None,
                "lastAction": self.last_action,
                "lastError": self.last_error,
            }

    def authorized(self, token: str | None) -> bool:
        return bool(self.admin_token) and bool(token) and hmac.compare_digest(token, self.admin_token)


class BackupHandler(BaseHTTPRequestHandler):
    server_version = "backup-rollback/1.0"

    @property
    def service(self) -> BackupService:
        return self.server.service  # type: ignore[attr-defined]

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def token(self) -> str | None:
        return self.headers.get("X-Backup-Token")

    def read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_BODY_BYTES:
            raise ValueError("body demasiado grande")
        raw = self.rfile.read(length) if length else b"{}"
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("body inválido")
        return value

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/health":
            self.send_json(self.service.health())
        elif path == "/api/backups":
            self.send_json({"backups": self.service.list_backups()})
        else:
            self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/")
        try:
            body = self.read_body()
            if not self.service.authorized(self.token()):
                self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                return
            if path == "/api/backups":
                self.send_json({"backup": self.service.create_backup("manual")}, HTTPStatus.CREATED)
                return
            if path == "/api/rollback":
                if body.get("confirm") is not True:
                    raise ValueError("confirm requerido")
                name = body.get("backup")
                if not isinstance(name, str):
                    raise ValueError("backup requerido")
                self.send_json({"restore": self.service.restore(unquote(name))})
                return
            if path.startswith("/api/backups/") and path.endswith("/restore"):
                if body.get("confirm") is not True:
                    raise ValueError("confirm requerido")
                name = path[len("/api/backups/") : -len("/restore")].strip("/")
                self.send_json({"restore": self.service.restore(unquote(name))})
                return
            self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except FileNotFoundError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception:
            self.send_json({"error": "backup operation failed"}, HTTPStatus.INTERNAL_SERVER_ERROR)


def make_server(host: str, port: int, service: BackupService | None = None) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), BackupHandler)
    server.service = service or BackupService(admin_token=os.getenv("BACKUP_ADMIN_TOKEN", ""))  # type: ignore[attr-defined]
    return server


def scheduler(service: BackupService, stop: threading.Event) -> None:
    while not stop.wait(60):
        try:
            service.create_if_due()
        except Exception:
            continue


def main() -> int:
    service = BackupService(admin_token=os.getenv("BACKUP_ADMIN_TOKEN", ""))
    if os.getenv("BACKUP_ON_START", "true").lower() in {"1", "true", "yes"}:
        try:
            service.create_if_due()
        except Exception:
            pass
    stop = threading.Event()
    thread = threading.Thread(target=scheduler, args=(service, stop), daemon=True)
    thread.start()
    server = make_server(os.getenv("BACKUP_HOST", "0.0.0.0"), int(os.getenv("BACKUP_PORT", "8793")), service)
    try:
        server.serve_forever()
    finally:
        stop.set()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
