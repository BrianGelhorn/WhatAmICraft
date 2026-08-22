#!/usr/bin/env python3
"""Checks Telegram alert classification, redaction, and compact formatting."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review import bot  # noqa: E402


def main() -> None:
    cases = [
        ("Remotion render failed at frame 114", "generator.log", "Render / Remotion"),
        ("YouTube upload returned 401 invalid token", "publisher.log", "Publicación / credenciales"),
        ("ElevenLabs voice request failed", "generator.log", "Audio / voces"),
        ("API timeout while connecting", "dashboard.log", "Red / API"),
        ("Permission denied: publishing-secrets.json", "publisher.log", "Archivos / permisos"),
        ("Dashboard job cancelled", "dashboard.log", "Dashboard / tarea"),
        ("unexpected fixture failure", "worker.log", "Error no clasificado"),
    ]
    for text, source, expected in cases:
        assert bot.classify_error(text, source) == expected

    detail = bot.fundamental_error(
        "Traceback (most recent call last):\n"
        "  File 'worker.py', line 1\n"
        "Error: access_token=secret-value\n"
        + ("noise\n" * 100)
    )
    assert detail == "Error: access_token=<redacted>"
    assert len(detail) <= 420

    alert = bot.error_alert("ERROR render failed\ntraceback details", "out/logs/generator.log", "Tarea: mc-01")
    assert alert.startswith("⚠️ ALERTA · Render / Remotion")
    assert "Tarea: mc-01" in alert
    assert "Detalle: ERROR render failed" in alert
    assert "traceback details" not in alert
    assert len(alert) < 1000

    print("ok: Telegram alert classification, redaction, and compact summaries")


if __name__ == "__main__":
    main()
