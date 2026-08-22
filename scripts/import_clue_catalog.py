#!/usr/bin/env python3
"""Materialize validated clue-api episodes into the render bank."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data/new-clues-20260815"
BANK_PATH = ROOT / "data/quiz-copy-episodes.json"
USED_PATH = ROOT / "data/used-targets.json"
ASSETS = ROOT / "public/mc-assets"


def asset_for(target_id: str) -> str:
    expected = f"{target_id.upper()}.png"
    for folder in ("item-assets", "entity-assets"):
        path = ASSETS / folder / expected
        if path.exists():
            return f"mc-assets/{folder}/{expected}"
    raise RuntimeError(f"Falta el asset de {target_id}")


def voice(episode_id: str, name: str, text: str) -> dict:
    return {
        "generate": True,
        "text": text,
        "publicSrc": f"audio/quiz-copy/{episode_id}/{name}.mp3",
        "seedSrc": f"audio/episodes/{episode_id}/{name}.mp3",
        "durationMs": 0,
        "volume": 1,
        "speed": 1.02,
        "fromOffsetFrames": 0,
    }


def next_episode_id(existing: set[str]) -> str:
    numbers = [int(match.group(1)) for value in existing if (match := re.fullmatch(r"mc-(\d+)", value))]
    return f"mc-{max(numbers, default=0) + 1:02d}"


def build_episode(template: dict, episode_id: str, source: dict) -> dict:
    episode = copy.deepcopy(template)
    target = source["target"]
    target_id = target["id"]
    display_name = target["display_name"]
    kind = target["kind"]
    guess_type = kind.title()
    icon = asset_for(target_id)

    episode.update({"id": episode_id, "uniqueAnswer": True, "needsReview": False})
    episode["answer"] = {
        "id": target_id,
        "displayName": display_name,
        "guessType": guess_type,
        "edition": target["edition"],
        "version": target["version"],
    }
    episode["hook"]["selectedIcon"] = icon
    episode["thumbnail"].update({
        "headlineBottom": guess_type.upper(),
        "difficulty": source.get("difficulty", "medium").upper(),
        "icon": icon,
        "platforms": {"vertical": "silhouette"},
    })
    episode["reveal"]["icon"] = icon
    episode["reveal"]["answerText"] = f"{display_name.upper()}!"
    episode["clues"] = [
        {"text": clue["text"], "voice": voice(episode_id, f"clue-{index}", clue["text"])}
        for index, clue in enumerate(source["clues"], 1)
    ]
    episode["reveal"]["voice"] = voice(
        episode_id,
        "reveal",
        f"Did you guess it? It is... the {display_name}!",
    )
    episode["reveal"]["voice"].update({"answerStartMs": 0, "syncOffsetFrames": 5})
    return episode


def main() -> None:
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    used = json.loads(USED_PATH.read_text(encoding="utf-8"))
    used_ids = set(used.get("target_ids", [])) | {
        item["id"] for item in used.get("targets", []) if isinstance(item, dict) and item.get("id")
    }
    episodes = list(bank["episodes"])
    existing_targets = {episode["answer"]["id"] for episode in episodes}
    existing_ids = {episode["id"] for episode in episodes}
    template = copy.deepcopy(episodes[0])
    imported = []

    for source_path in sorted(SOURCE_DIR.glob("*.json")):
        if source_path.name == "manifest.json":
            continue
        source = json.loads(source_path.read_text(encoding="utf-8"))["episode"]
        target_id = source["target"]["id"]
        if target_id in used_ids:
            raise RuntimeError(f"El objetivo ya fue usado: {target_id}")
        if target_id in existing_targets:
            continue
        episode_id = next_episode_id(existing_ids)
        episode = build_episode(template, episode_id, source)
        episodes.append(episode)
        existing_ids.add(episode_id)
        existing_targets.add(target_id)
        imported.append(episode_id)

    result = {
        "$schema": bank["$schema"],
        "schema_version": bank["schema_version"],
        "format": bank["format"],
        "episodes": episodes,
    }
    BANK_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"imported={len(imported)} total={len(episodes)} ids={','.join(imported)}")


if __name__ == "__main__":
    main()
