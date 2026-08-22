#!/usr/bin/env python3
"""Behavior test for real backup creation, listing, authorization, and rollback."""

from __future__ import annotations

import json
import shutil
import threading
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import backup_service
import backup_state


def request(base: str, method: str, path: str, payload: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Backup-Token"] = token
    try:
        with urllib.request.urlopen(
            urllib.request.Request(f"{base}{path}", data=body, headers=headers, method=method), timeout=5
        ) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "out" / "backup-service-test"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    try:
        (root / "data").mkdir(parents=True)
        (root / "out" / "logs").mkdir(parents=True)
        (root / "data" / "state.json").write_text('{"status":"before"}\n', encoding="utf-8")
        (root / "data" / "publishing-secrets.json").touch()
        (root / ".env").touch()
        (root / "out" / "queue.json").write_text('{"pending":["mc-01"]}\n', encoding="utf-8")
        backup_dir = root / "backups" / "ops"
        service = backup_service.BackupService(root, backup_dir, keep=1, interval_seconds=60, admin_token="test-token")
        server = backup_service.make_server("127.0.0.1", 0, service)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            status, health = request(base, "GET", "/health")
            assert status == 200 and health["service"] == "backup-rollback"

            status, denied = request(base, "POST", "/api/backups", {})
            assert status == 401 and denied["error"] == "unauthorized"

            status, created = request(base, "POST", "/api/backups", {}, "test-token")
            assert status == 201 and created["backup"]["action"] == "manual"
            backup_name = created["backup"]["backup"]
            assert (backup_dir / backup_name).is_file()
            with zipfile.ZipFile(backup_dir / backup_name) as archive:
                assert "data/state.json" in archive.namelist()
                assert "data/publishing-secrets.json" not in archive.namelist()
                assert ".env" not in archive.namelist()
            assert service.keep == 2

            (root / "data" / "state.json").write_text('{"status":"corrupted"}\n', encoding="utf-8")
            status, invalid = request(base, "POST", "/api/rollback", {"backup": backup_name}, "test-token")
            assert status == 400 and invalid["error"] == "confirm requerido"
            status, restored = request(
                base, "POST", "/api/rollback", {"backup": backup_name, "confirm": True}, "test-token"
            )
            assert status == 200 and restored["restore"]["action"] == "restore"
            assert json.loads((root / "data" / "state.json").read_text(encoding="utf-8"))["status"] == "before"
            assert len(service.list_backups()) >= 2  # original plus the pre-restore safety backup

            malicious = backup_dir / "state-malicious.zip"
            with zipfile.ZipFile(malicious, "w") as archive:
                archive.writestr("../outside.txt", "must not extract")
            try:
                backup_state.restore(malicious, root=root)
            except RuntimeError as error:
                assert "Ruta insegura" in str(error)
            else:
                raise AssertionError("unsafe archive path was accepted")
            assert not (root.parent / "outside.txt").exists()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("ok: backup service creates, lists, authorizes, protects, and rolls back state")


if __name__ == "__main__":
    main()
