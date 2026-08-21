#!/usr/bin/env python3
"""Regression check for clue-catalog episodes entering the render inventory."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))
import app  # noqa: E402


def main() -> None:
    bank = json.loads((ROOT / "data/quiz-copy-episodes.json").read_text(encoding="utf-8"))
    source_ids = {
        json.loads(path.read_text(encoding="utf-8"))["episode"]["target"]["id"]
        for path in (ROOT / "data/new-clues-20260815").glob("*.json")
        if path.name != "manifest.json"
    }
    imported = {episode["answer"]["id"]: episode for episode in bank["episodes"]}
    assert source_ids <= imported.keys()
    assert all(imported[target]["clues"][0]["voice"]["generate"] for target in source_ids)

    captured = {}
    app.start_command = lambda label, command, *args, **kwargs: captured.update(label=label, command=command)
    app.start_job("mc-47")
    assert "--generate-audio" in captured["command"]
    assert "--episode" in captured["command"] and "mc-47" in captured["command"]
    print(f"ok: {len(source_ids)} clue episodes are generable from the dashboard")


if __name__ == "__main__":
    main()
