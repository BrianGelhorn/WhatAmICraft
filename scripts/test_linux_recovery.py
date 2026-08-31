#!/usr/bin/env python3
"""Exercise Linux entrypoints without touching Docker, networking, or production."""

import configparser
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LINUX = ROOT / "scripts/linux"
FAKE_TOOL = '''
import json, os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with Path(os.environ["TEST_CALLS"]).open("a") as stream:
    stream.write(json.dumps([name, *args]) + "\\n")
if name == "df":
    print("Use%\\n" + os.environ.get("TEST_USAGE", "60") + "%")
elif name == "sudo":
    sys.exit(int(os.environ.get("TEST_LAUNCH_EXIT", "0")))
elif name == "ping":
    sys.exit(1)
elif name == "docker":
    sys.exit(int(os.environ.get("TEST_DOCKER_EXIT", "0")))
elif name == "tailscale":
    if args == ["status", "--json"]:
        print(json.dumps({"BackendState": os.environ.get("TEST_TAILSCALE", "Stopped")}))
    elif args[0] == os.environ.get("TEST_TAILSCALE_FAIL"):
        sys.exit(42)
'''


def fixture(root: Path) -> dict:
    tools = root / "bin"
    tools.mkdir()
    for name in ("df", "sudo", "ping", "docker", "tailscale"):
        path = tools / name
        path.write_text(f"#!{sys.executable}\n" + FAKE_TOOL)
        path.chmod(0o755)
    (root / "videos").mkdir()
    return {
        **os.environ, "PATH": f"{tools}:{os.environ['PATH']}",
        "TEST_CALLS": str(root / "calls.jsonl"), "XDG_RUNTIME_DIR": str(root / "runtime"),
        "APP_DIR": str(root / "app"), "VIDEO_STORAGE_PATH": str(root / "videos"),
        "WAIT_SECONDS": "0", "TAILSCALE_WAIT_SECONDS": "0",
        "DOCKER_CLEANUP_MIN_USED_PCT": "80",
        "DOCKER_CLEANUP_IMAGE_UNTIL": "168h", "DOCKER_CLEANUP_CACHE_UNTIL": "336h",
    }


def calls(env: dict) -> list:
    path = Path(env["TEST_CALLS"])
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def run(command: list[str], env: dict) -> subprocess.CompletedProcess:
    Path(env["TEST_CALLS"]).write_text("")
    return subprocess.run(command, env=env, text=True, capture_output=True, timeout=10)


def check_cleanup() -> None:
    unit = configparser.ConfigParser(interpolation=None)
    unit.read(LINUX / "docker-disk-cleanup.service")
    command = shlex.split(unit["Service"]["ExecStart"].replace("/home/brian/MinecraftQuizGuesser", str(ROOT)))
    with tempfile.TemporaryDirectory(prefix="cleanup-test-") as temporary:
        env = fixture(Path(temporary))
        try:
            result = run(command, env)
        except PermissionError as error:
            raise AssertionError("cleanup must run a non-executable script from a clean checkout") from error
        assert result.returncode == 0 and "skip" in result.stdout, result.stderr
        assert not [call for call in calls(env) if call[0] == "docker"]
        env["TEST_USAGE"] = "90"
        result = run(command, env)
        assert result.returncode == 0, result.stderr
        assert [call for call in calls(env) if call[0] == "docker"] == [
            ["docker", "image", "prune", "--force", "--filter", "until=168h"],
            ["docker", "builder", "prune", "--force", "--filter", "until=336h"],
        ]
        env["TEST_DOCKER_EXIT"] = "42"
        assert run(command, env).returncode == 42
        assert len([call for call in calls(env) if call[0] == "docker"]) == 1
        with (Path(env["XDG_RUNTIME_DIR"]) / "whatamicraft/docker-disk-cleanup.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            assert run(command, env).returncode == 0
            assert calls(env) == [], "overlapping cleanup must not prune"


def installed_units() -> list[configparser.ConfigParser]:
    installer = (LINUX / "install-minecraft-quiz-service.sh").read_text()
    units = []
    for body in re.findall(r"<<SERVICE\n(.*?)\nSERVICE", installer, re.DOTALL):
        rendered = subprocess.check_output(["bash", "-c", f"cat <<SERVICE\n{body}\nSERVICE"],
                                           env={**os.environ, "APP_USER": "test", "APP_DIR": "/test/app"}, text=True)
        unit = configparser.ConfigParser(interpolation=None)
        unit.read_string(rendered)
        units.append(unit)
    return units


def check_startup() -> None:
    units = installed_units()
    boot = units[0]
    with tempfile.TemporaryDirectory(prefix="boot-test-") as temporary:
        env = fixture(Path(temporary))
        shutil.copytree(ROOT / "scripts", Path(env["APP_DIR"]) / "scripts")
        data = Path(env["APP_DIR"]) / "data"
        data.mkdir()
        for name in ("used-targets.json", "quiz-copy-episodes.json"):
            shutil.copy2(ROOT / "data" / name, data / name)
        # Run the actual unit commands, resolving the install destination to its source.
        for key in ("ExecStartPre", "ExecStart"):
            if key in boot["Service"]:
                script = LINUX / Path(boot["Service"][key]).name
                result = run(["bash", str(script)], env)
                log = Path(env["APP_DIR"]) / "out/logs/minecraft-quiz-service.log"
                detail = log.read_text() if log.exists() else result.stderr
                assert result.returncode == 0, f"Tailscale unavailable must not block the stack: {detail}"
        assert calls(env) == [["docker", "info"], ["sudo", "-n", "/usr/local/sbin/whatamicraft-up"]]
        assert list((Path(env["APP_DIR"]) / "backups/ops").glob("state-*.zip"))
        env["TEST_LAUNCH_EXIT"] = "42"
        assert run(["bash", str(LINUX / "start-minecraft-quiz.sh")], env).returncode == 42
        env.pop("TEST_LAUNCH_EXIT")
        backup_dir = Path(env["APP_DIR"]) / "backups/ops"
        backup_dir.rename(backup_dir.with_name("previous-ops"))
        backup_dir.write_text("blocked backup directory")
        assert run(["bash", str(LINUX / "start-minecraft-quiz.sh")], env).returncode != 0
        assert calls(env) == [["docker", "info"]], "failed backup must not be ignored"
        env["VIDEO_STORAGE_PATH"] = str(Path(temporary) / "missing-volume")
        assert run(["bash", str(LINUX / "start-minecraft-quiz.sh")], env).returncode != 0
        assert calls(env) == [["docker", "info"]], "missing video storage must prevent container creation"
    assert len(units) == 2, "remote access needs an independent unit"
    access = units[1]
    assert "tailscaled.service" not in str(dict(boot["Unit"]))
    assert "minecraft-quiz.service" not in str(dict(access["Unit"]))
    for unit in units:
        assert unit["Service"]["Restart"] == "on-failure"
        assert unit["Service"]["RestartSec"] == "30"
        assert unit["Unit"]["StartLimitIntervalSec"] == "0"
    hook = (LINUX / "install-wifi-watchdog.sh").read_text()
    assert 'install-minecraft-quiz-service.sh" --install-only' in hook
    installer = (LINUX / "install-minecraft-quiz-service.sh").read_text()
    assert 'if [ "${1:-}" != "--install-only" ]; then' in installer
    assert "systemctl --no-block start minecraft-quiz-access.service" in installer


def check_access_failures() -> None:
    command = ["bash", str(LINUX / "configure-tailscale-access.sh")]
    with tempfile.TemporaryDirectory(prefix="access-test-") as temporary:
        env = fixture(Path(temporary))
        assert run(command, env).returncode != 0
        assert all(call[1:] == ["status", "--json"] for call in calls(env))
        env["TEST_TAILSCALE"] = "Running"
        for failing in ("serve", "funnel"):
            env["TEST_TAILSCALE_FAIL"] = failing
            assert run(command, env).returncode != 0, f"{failing} failure must remain retryable"
            assert calls(env)[-1][1] == failing, "stop configuration at the first failed operation"
        env.pop("TEST_TAILSCALE_FAIL")
        assert run(command, env).returncode == 0
        assert calls(env) == [
            ["tailscale", "status", "--json"],
            ["tailscale", "serve", "--bg", "--https=8443", "http://127.0.0.1:8787"],
            ["tailscale", "funnel", "--bg", "--https=443", "http://127.0.0.1:8080"],
            ["tailscale", "serve", "status"],
        ], "recovery must preserve existing routes, not reset Tailscale"


def main() -> None:
    check_cleanup()
    check_startup()
    check_access_failures()
    print("ok: cleanup permissions/policy/locking, independent boot, storage guard, and access recovery")


if __name__ == "__main__":
    main()
