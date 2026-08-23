#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/quiz-copy-hook-experiments.json"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["format"] == "minecraft-quiz-copy-hook-experiments"
    assert manifest["variants"]
    ids = [variant["id"] for variant in manifest["variants"]]
    assert len(ids) == len(set(ids))
    for variant in manifest["variants"]:
        assert variant["status"] != "active" or not variant["audio"]["requiresRegeneration"]
        assert variant["timing"]["hookTitleFromFrame"] < 90
        assert variant["timing"]["handoffFromFrame"] < variant["timing"]["contentStartFrame"]
        assert variant["copy"]["title"] != "CAN YOU GUESS IT?"
        assert "COMMENT" in variant["copy"]["handoff"]
        assert variant["audio"]["requiresRegeneration"]
    print("ok: quiz-copy hook experiment contract")


if __name__ == "__main__":
    main()
