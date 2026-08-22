#!/usr/bin/env python3
"""Exercise the watchdog's real one-shot layered network check."""

from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
WATCHDOG = ROOT / "scripts/linux/wifi-watchdog.sh"


def fake_tools(directory: Path, https_ok: bool) -> None:
    tools = {
        "ip": "#!/bin/sh\necho 'default via 192.168.0.1 dev wlan0'\n",
        "ping": "#!/bin/sh\nexit 0\n",
        "getent": "#!/bin/sh\nexit 0\n",
        "curl": f"#!/bin/sh\nexit {0 if https_ok else 1}\n",
        "logger": "#!/bin/sh\nexit 0\n",
    }
    for name, body in tools.items():
        path = directory / name
        path.write_text(body, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)


def run_once(https_ok: bool) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as temp:
        tool_dir = Path(temp)
        fake_tools(tool_dir, https_ok)
        environment = os.environ.copy()
        environment.update(
            PATH=f"{tool_dir}{os.pathsep}{environment['PATH']}",
            WIFI_WATCHDOG_ONCE="1",
            WIFI_IFACE="wlan0",
        )
        return subprocess.run(
            ["bash", str(WATCHDOG)],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )


def main() -> None:
    if os.name == "nt":
        print("skip: watchdog behavior test runs on Linux CI")
        return
    assert run_once(True).returncode == 0
    failed = run_once(False)
    assert failed.returncode == 1
    assert "One-shot network check failed." in failed.stdout
    print("ok: watchdog requires gateway, DNS, and HTTPS before declaring connectivity")


if __name__ == "__main__":
    main()
