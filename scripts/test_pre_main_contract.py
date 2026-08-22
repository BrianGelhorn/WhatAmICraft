#!/usr/bin/env python3
"""Keep the notebook pre-main environment isolated and non-publishing."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "compose.pre-main.yaml"
LAUNCHER = ROOT / "scripts/pre_main.ps1"


def main() -> None:
    compose = COMPOSE.read_text(encoding="utf-8")
    launcher = LAUNCHER.read_text(encoding="utf-8")

    assert "staging/runtime/pre-main" in compose
    assert '"127.0.0.1:8878:8787"' in compose
    assert '"127.0.0.1:8088:80"' in compose
    assert "publishing-secrets.json" not in compose
    for credential in (
        "YOUTUBE_REFRESH_TOKEN",
        "TIKTOK_ACCESS_TOKEN",
        "INSTAGRAM_ACCESS_TOKEN",
        "META_ACCESS_TOKEN",
        "TELEGRAM_BOT_TOKEN",
    ):
        assert f"{credential}: \"\"" in compose, credential

    assert "prepare_staging.py" in launcher
    assert "whatamicraft-pre-main" in launcher
    assert "--reset" in launcher
    assert "docker compose" in launcher

    print("pre-main contract: ok")


if __name__ == "__main__":
    main()
