#!/usr/bin/env python3
from copy import deepcopy
from pathlib import Path

from produce_mystery_v2 import BANK_PATH, ROOT, VARIANTS, read_json, selected_config, validate_episode, voice_specs


def rejected(episode: dict, expected: str) -> None:
    try:
        validate_episode(episode)
    except RuntimeError as error:
        assert expected in str(error), error
    else:
        raise AssertionError(f"Expected validation error containing: {expected}")


episode = read_json(BANK_PATH)["episodes"][0]
validate_episode(episode)

for variant in VARIANTS:
    config = selected_config(episode, variant)
    timeline = config["timeline"]
    scenes = [timeline["hook"], *timeline["hints"], timeline["countdown"], timeline["reveal"], timeline["cta"], timeline["loop"]]
    assert scenes[0]["from"] == 0
    assert all(right["from"] == left["from"] + left["durationInFrames"] for left, right in zip(scenes, scenes[1:]))
    assert scenes[-1]["from"] + scenes[-1]["durationInFrames"] == timeline["durationInFrames"]
    assert config["hook"]["question"] and timeline["hints"][0]["from"] <= 45
    assert timeline["cta"]["durationInFrames"] >= 45
    assert timeline["reveal"]["durationInFrames"] >= 60
    assert config["answer"]["image"] == config["answer"]["silhouette"]
    assert len(config["hints"]) == 3 and all(2 <= len(hint["fragments"]) <= 3 for hint in config["hints"])
    specs = voice_specs(episode, config)
    assert specs[0]["from"] == 0
    assert all(spec["from"] < spec["sceneEnd"] for spec in specs)

component = (ROOT / "src/components/mystery/MysteryComponents.tsx").read_text(encoding="utf-8")
for name in ("HookScene", "MysteryObject", "HintScene", "ProgressMeter", "CountdownScene", "RevealScene", "CTAScene", "CaptionRenderer", "AudioTimeline", "LoopBridge", "SafeZoneOverlay", "RetentionDebugOverlay"):
    assert f"export const {name}" in component
assert "Math.random(" not in component and "transition:" not in component

bad_silhouette = deepcopy(episode)
bad_silhouette["answer"]["silhouette"] = "mc-assets/entity-assets/flat/ARROW.png"
rejected(bad_silhouette, "forma exacta")

late_hint = deepcopy(episode)
late_hint["variants"]["balanced"]["timeline"]["hook"] = 46
rejected(late_hint, "frame 46")

print("ok: mystery-v2 retention and generation contract")
