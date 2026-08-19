from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_BANK = ROOT / "legacy-episode-copy.en.json"
LEGACY_AUDIO = ROOT / "legacy-audio"
BANK_PATH = ROOT / "data/quiz-copy-episodes.json"
ITEMS = ROOT / "public/mc-assets/item-assets"

ROULETTE_NAMES = [
    "DIAMOND", "ENDER_PEARL", "GOLDEN_APPLE", "TOTEM_OF_UNDYING",
    "NETHERITE_SWORD", "EMERALD", "TNT", "IRON_INGOT", "REDSTONE",
    "SHIELD", "BOW", "FISHING_ROD", "CLOCK", "COMPASS",
]


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def asset_for(target: str) -> str:
    filename = f"{slug(target).upper()}.png"
    item_path = ITEMS / filename
    if item_path.exists():
        return f"mc-assets/item-assets/{filename}"
    entity_path = ROOT / "public/mc-assets/entity-assets" / filename
    if entity_path.exists():
        return f"mc-assets/entity-assets/{filename}"
    raise RuntimeError(f"Missing asset for {target}: {filename}")


def voice(src: str, text: str, duration_ms: int, seed_src: str) -> dict:
    return {
        "generate": False,
        "text": text,
        "publicSrc": src,
        "seedSrc": seed_src,
        "durationMs": duration_ms,
        "volume": 1,
        "speed": 1.02,
        "fromOffsetFrames": 0,
    }


def build_episode(episode_id: str, source: dict) -> dict:
    target = source["target"]
    target_id = slug(target)
    icon = asset_for(target)
    roulette = [name for name in ROULETTE_NAMES if f"mc-assets/item-assets/{name}.png" != icon]
    if len(roulette) < 7:
        roulette.extend(path.stem for path in sorted(ITEMS.glob("*.png")) if path.stem != Path(icon).stem)
    roulette = [f"mc-assets/item-assets/{name}.png" for name in roulette[:7]]
    clues = source["clues"][:3]
    manifest = json.loads((LEGACY_AUDIO / episode_id / "manifest.json").read_text(encoding="utf-8"))
    clue_meta = manifest.get("clues", [])
    clue_voices = []
    for index, text in enumerate(clues, 1):
        source_path = LEGACY_AUDIO / episode_id / f"clue-{index}.mp3"
        if not source_path.exists():
            raise RuntimeError(f"Missing clue audio: {source_path}")
        destination = ROOT / f"public/audio/quiz-copy/{episode_id}/clue-{index}.mp3"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        seed_destination = ROOT / f"public/audio/episodes/{episode_id}/clue-{index}.mp3"
        seed_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, seed_destination)
        clue_voices.append(voice(
            f"audio/quiz-copy/{episode_id}/clue-{index}.mp3",
            text,
            int(clue_meta[index - 1]["durationMs"]),
            f"audio/episodes/{episode_id}/clue-{index}.mp3",
        ))
    reveal_source = LEGACY_AUDIO / episode_id / "reveal.mp3"
    reveal_destination = ROOT / f"public/audio/quiz-copy/{episode_id}/reveal.mp3"
    shutil.copy2(reveal_source, reveal_destination)
    reveal_seed_destination = ROOT / f"public/audio/episodes/{episode_id}/reveal.mp3"
    reveal_seed_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(reveal_source, reveal_seed_destination)
    reveal_meta = manifest["reveal"]
    return {
        "id": episode_id,
        "uniqueAnswer": True,
        "needsReview": False,
        "answer": {
            "id": target_id,
            "displayName": target,
            "guessType": "Item",
            "edition": "java",
            "version": "1.21.5",
        },
        "background": "images/template-layers/background.png",
        "hook": {
            "eyebrow": "MINECRAFT MYSTERY",
            "title": "CAN YOU GUESS IT?",
            "handoff": "3 HINTS · ONE CHANCE",
            "categoryPrefix": "CATEGORY",
            "selectedIcon": icon,
            "rouletteIcons": roulette,
        },
        "hintUi": {"label": "HINT {current} / {total}", "cta": "LOCK IN YOUR GUESS"},
        "thumbnail": {
            "eyebrow": "MINECRAFT MYSTERY",
            "headlineTop": "GUESS THIS",
            "headlineBottom": "ITEM",
            "difficulty": "HARD",
            "subline": "3 HINTS · 1 CHANCE",
            "mysteryLabel": "WHAT AM I?",
            "hintLabel": "HINT {number}",
            "background": "images/template-layers/background.png",
            "icon": icon,
            "accent": "#FFD34F",
            "secondaryAccent": "#7EC850",
            "iconScale": 1,
            "iconOffsetY": 0,
            "platforms": {"vertical": "silhouette"},
            "outputDir": "out/thumbnails",
        },
        "clues": [{"text": text, "voice": clue_voices[index]} for index, text in enumerate(clues)],
        "reveal": {
            "prompt": "FINAL ANSWER?",
            "answerLabel": "THE ANSWER IS",
            "answerText": f"{target.upper()}!",
            "cta": "HOW MANY HINTS DID YOU NEED?",
            "icon": icon,
            "countdownFrom": 3,
            "voice": {
                **voice(
                    f"audio/quiz-copy/{episode_id}/reveal.mp3",
                    f"Did you guess it? It is... the {target}!",
                    int(reveal_meta["durationMs"]),
                    "audio/episodes/{episode_id}/reveal.mp3".format(episode_id=episode_id),
                ),
                "answerStartMs": int(reveal_meta["answerStartMs"]),
                "syncOffsetFrames": 5,
            },
        },
        "timeline": {
            "contentStartFrame": 180,
            "reelStopFrame": 34,
            "hookTitleFromFrame": 42,
            "handoffFromFrame": 80,
            "categoryFromFrame": 34,
            "hintDurationInFrames": 155,
            "revealDurationInFrames": 210,
            "answerStartFrame": 72,
            "countdownStepInFrames": 24,
        },
        "voiceGeneration": {"voiceId": "pNInz6obpgDQGcFmaJgB", "model": "eleven_v3"},
        "audio": {
            "normalization": {"voiceTargetLufs": -16, "voiceTruePeakDb": -1.5, "voiceLoudnessRange": 11},
            "music": {"folder": "public/audio/music", "targetLufs": -16, "truePeakDb": -1.5, "loudnessRange": 11, "volume": 0.16, "duckedVolume": 0.07, "fadeInFrames": 24, "fadeOutFrames": 36, "duckFadeFrames": 6},
            "roulette": {"publicSrc": "audio/sfx/roulette-ticks-unified.wav", "from": 0, "durationInFrames": 36, "volume": 1, "targetPeakDb": -8},
            "countdownClick": {"publicSrc": "audio/sfx/quiz-copy/menu-button.m4a", "durationInFrames": 5, "volume": 1, "targetPeakDb": -8},
            "revealBell": {"publicSrc": "audio/sfx/quiz-copy/reveal-bell.m4a", "durationInFrames": 16, "volume": 0.85, "targetPeakDb": -4.5},
            "genericVoices": [
                {"id": "hook", "generate": False, "text": "Can you guess it?", "publicSrc": "audio/voice/quiz-copy/hook.mp3", "from": 48, "durationInFrames": 28, "volume": 1},
                {"id": "handoff", "generate": False, "text": "Three hints. One chance.", "publicSrc": "audio/voice/quiz-copy/handoff.mp3", "from": 80, "durationInFrames": 54, "volume": 1, "playbackRate": 1.12, "fadeOutFrames": 11},
            ],
        },
    }


def main() -> None:
    legacy = json.loads(LEGACY_BANK.read_text(encoding="utf-8"))
    current = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    episodes = {episode["id"]: episode for episode in current["episodes"] if episode["id"] == "mc-03"}
    for episode_id in sorted(path.name for path in LEGACY_AUDIO.iterdir() if path.is_dir()):
        if episode_id not in episodes:
            try:
                episodes[episode_id] = build_episode(episode_id, legacy[episode_id])
            except RuntimeError as error:
                print(f"skip {episode_id}: {error}")
    output = {"$schema": "../schemas/quiz-copy-episode.schema.json", "schema_version": 1, "format": "minecraft-quiz-copy", "episodes": [episodes[key] for key in sorted(episodes)]}
    BANK_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"restored {len(output['episodes'])} episodes")


if __name__ == "__main__":
    main()
