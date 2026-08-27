#!/usr/bin/env python3
"""Exercise thread and child-process lifecycle boundaries without providers."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))
sys.path.insert(0, str(ROOT / "scripts"))

import analytics_service  # noqa: E402
import app  # noqa: E402
import backup_service  # noqa: E402
import production_common  # noqa: E402


def wait_for(predicate, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    assert predicate(), "condition did not become true before timeout"


def process_exists(pid: int) -> bool:
    """Treat a zombie as stopped; this avoids false positives after SIGKILL."""
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8") as stream:
            fields = stream.read().split()
        return len(fields) < 3 or fields[2] != "Z"
    except FileNotFoundError:
        return False
    except OSError:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True


@contextmanager
def patched(module, **values):
    original = {name: getattr(module, name) for name in values}
    try:
        for name, value in values.items():
            setattr(module, name, value)
        yield
    finally:
        for name, value in original.items():
            setattr(module, name, value)


def test_terminate_process_kills_descendants() -> None:
    """Cancelling a group must not leave a child alive after its parent exits."""
    with tempfile.TemporaryDirectory(prefix="whatamicraft-process-") as directory:
        child_file = Path(directory) / "child.pid"
        code = """import os
import pathlib
import signal
import sys
import time

child = os.fork()
if child == 0:
    pathlib.Path(sys.argv[1]).write_text(str(os.getpid()))
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    while True:
        time.sleep(1)
while True:
    time.sleep(1)
"""
        process = subprocess.Popen(
            [sys.executable, "-c", code, str(child_file)],
            start_new_session=True,
        )
        child_pid = None
        try:
            def child_pid_ready() -> bool:
                try:
                    return child_file.exists() and child_file.read_text(encoding="utf-8").strip().isdigit()
                except OSError:
                    return False

            wait_for(child_pid_ready)
            child_pid = int(child_file.read_text(encoding="utf-8"))
            assert os.getpgid(child_pid) == process.pid
            app._terminate_process(process)
            wait_for(lambda: not process_exists(child_pid))
            assert process.poll() is not None
        finally:
            if child_pid and process_exists(child_pid):
                os.killpg(process.pid, signal.SIGKILL)
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)


def command_harness(tmp: Path):
    state = {"status": "idle", "pid": None, "code": None, "success": 0}
    original_job = app.JOB
    original_processes = app.ACTIVE_PROCESSES
    original_cancel = app.CANCEL_REQUESTED
    app.JOB = {"status": "idle", "label": "", "lines": []}
    app.ACTIVE_PROCESSES = {}
    app.CANCEL_REQUESTED = {}

    def read_job(_lane=None):
        return {"status": state["status"], "pid": state["pid"]}

    def begin_job(*_args, **_kwargs):
        state["status"] = "running"

    def set_job_pid(pid, _lane="main"):
        state["pid"] = pid

    def finish_job(status, code, *_args, **_kwargs):
        state.update(status=status, code=code)

    def on_success():
        state["success"] += 1

    values = {
        "read_job": read_job,
        "begin_job": begin_job,
        "set_job_pid": set_job_pid,
        "finish_job": finish_job,
        "append_job_line": lambda *_args, **_kwargs: None,
        "append_log": lambda *_args, **_kwargs: None,
        "LOG_DIR": tmp / "logs",
    }
    return state, on_success, (original_job, original_processes, original_cancel), values


def restore_command_harness(original) -> None:
    app.JOB, app.ACTIVE_PROCESSES, app.CANCEL_REQUESTED = original


def test_start_command_releases_thread_state_on_success_and_spawn_failure() -> None:
    with tempfile.TemporaryDirectory(prefix="whatamicraft-command-") as directory:
        state, on_success, original, values = command_harness(Path(directory))
        try:
            before = {thread.ident for thread in threading.enumerate()}
            with patched(app, **values):
                app.start_command(
                    "successful fixture",
                    [sys.executable, "-c", "print('done')"],
                    on_success=on_success,
                )
                wait_for(lambda: state["status"] != "running")
                assert state["status"] == "completed" and state["code"] == 0
                assert state["success"] == 1
                assert app.ACTIVE_PROCESSES["main"] is None
                assert app.CANCEL_REQUESTED["main"] is False

                def fail_popen(*_args, **_kwargs):
                    raise OSError("fixture spawn failure")

                with patched(app.subprocess, Popen=fail_popen):
                    state.update(status="idle", code=None, pid=None)
                    app.start_command("failed fixture", ["does-not-run"])
                    wait_for(lambda: state["status"] != "running")
                assert state["status"] == "failed" and state["code"] == 1
                assert app.ACTIVE_PROCESSES["main"] is None
                assert app.CANCEL_REQUESTED["main"] is False
            wait_for(lambda: not any(t.is_alive() for t in threading.enumerate() if t.ident not in before))
        finally:
            restore_command_harness(original)


def test_start_command_rejects_duplicate_lane_and_cancellation_cleans_up() -> None:
    with tempfile.TemporaryDirectory(prefix="whatamicraft-cancel-") as directory:
        state, _on_success, original, values = command_harness(Path(directory))
        try:
            with patched(app, **values):
                state["status"] = "running"
                try:
                    app.start_command("duplicate", [sys.executable, "-c", "pass"])
                except RuntimeError as error:
                    assert "tarea en curso" in str(error)
                else:
                    raise AssertionError("duplicate lane was accepted")

                state.update(status="idle", pid=None)
                app.start_command("cancellable fixture", [sys.executable, "-c", "import time; time.sleep(30)"])
                wait_for(lambda: state["pid"] is not None)
                app.cancel_active_job("main")
                wait_for(lambda: app.ACTIVE_PROCESSES["main"] is None)
                assert state["status"] == "cancelled"
                assert app.CANCEL_REQUESTED["main"] is False
        finally:
            restore_command_harness(original)


def test_production_lock_stops_heartbeat_thread() -> None:
    with tempfile.TemporaryDirectory(prefix="whatamicraft-lock-") as directory:
        lock = Path(directory) / "production.lock"
        before = {thread.ident for thread in threading.enumerate()}
        with patched(production_common, PRODUCTION_LOCK=lock):
            with production_common.production_lock():
                assert lock.is_dir()
                heartbeat = [thread for thread in threading.enumerate() if thread.ident not in before]
                assert len(heartbeat) == 1 and heartbeat[0].daemon
                heartbeat_id = heartbeat[0].ident
            wait_for(
                lambda: not any(
                    thread.ident == heartbeat_id and thread.is_alive() for thread in threading.enumerate()
                )
            )
        assert not lock.exists()


def test_analytics_sync_rejects_overlap_and_recovers_after_failure() -> None:
    service = analytics_service.AnalyticsService()
    started = threading.Event()
    release = threading.Event()
    calls = {"count": 0}

    def blocked_sync():
        calls["count"] += 1
        started.set()
        release.wait(2)

    before = {thread.ident for thread in threading.enumerate()}
    with patched(
        analytics_service.analytics,
        sync_all=blocked_sync,
    ), patched(analytics_service.state_db, load_flag=lambda *_args: {}):
        service.start_sync()
        wait_for(started.is_set)
        try:
            service.start_sync()
        except RuntimeError:
            pass
        else:
            raise AssertionError("concurrent analytics sync was accepted")
        release.set()
        wait_for(lambda: service.sync_status()["status"] == "completed")

        def failed_sync():
            calls["count"] += 1
            raise RuntimeError("provider unavailable")

        analytics_service.analytics.sync_all = failed_sync
        service.start_sync()
        wait_for(lambda: service.sync_status()["status"] == "failed")
        assert "provider unavailable" in service.sync_status()["error"]
        analytics_service.analytics.sync_all = lambda: calls.update(count=calls["count"] + 1)
        service.start_sync()
        wait_for(lambda: service.sync_status()["status"] == "completed")
    wait_for(lambda: not any(thread.is_alive() for thread in threading.enumerate() if thread.ident not in before))
    assert calls["count"] == 3


def test_backup_scheduler_exits_when_stop_is_requested() -> None:
    class Stop:
        def __init__(self):
            self.calls = 0

        def wait(self, _seconds):
            self.calls += 1
            return self.calls > 1

    class Service:
        def __init__(self):
            self.calls = 0

        def create_if_due(self):
            self.calls += 1

    stop, service = Stop(), Service()
    thread = threading.Thread(target=backup_service.scheduler, args=(service, stop), daemon=True)
    thread.start()
    thread.join(timeout=1)
    assert not thread.is_alive()
    assert stop.calls == 2 and service.calls == 1


def main() -> None:
    test_terminate_process_kills_descendants()
    test_start_command_releases_thread_state_on_success_and_spawn_failure()
    test_start_command_rejects_duplicate_lane_and_cancellation_cleans_up()
    test_production_lock_stops_heartbeat_thread()
    test_analytics_sync_rejects_overlap_and_recovers_after_failure()
    test_backup_scheduler_exits_when_stop_is_requested()
    print("ok: process groups, command threads, locks, analytics sync, cancellation, and scheduler cleanup")


if __name__ == "__main__":
    main()
