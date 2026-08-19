from __future__ import annotations

import time
from pathlib import Path

from publishing.settings import CONFIG_PATH, _write, load_config
from review.storage import queue_episode


ROOT = Path(__file__).resolve().parents[1]
FIRST_EPISODE = "mc-01"
FIRST_VIDEO = ROOT / "out/episodes/mc-01-crossbow.mp4"
RENDERING_VIDEO = ROOT / "out/episodes/.mc-01-crossbow.rendering.mp4"
MAX_WAIT_SECONDS = 24 * 60 * 60
STABLE_CHECK_SECONDS = 10


def main() -> None:
    started_at = time.time()
    deadline = started_at + MAX_WAIT_SECONDS
    while time.time() < deadline:
        if FIRST_VIDEO.exists() and FIRST_VIDEO.stat().st_mtime >= started_at and not RENDERING_VIDEO.exists():
            size = FIRST_VIDEO.stat().st_size
            time.sleep(STABLE_CHECK_SECONDS)
            if FIRST_VIDEO.exists() and FIRST_VIDEO.stat().st_size == size:
                queue_episode(FIRST_EPISODE)
                config = load_config()
                config["schedule"]["enabled"] = True
                _write(CONFIG_PATH, config)
                print(f"publish gate opened: {FIRST_EPISODE}", flush=True)
                return
        time.sleep(30)
    raise TimeoutError("No apareció el primer video nuevo dentro de 24 horas")


if __name__ == "__main__":
    main()
