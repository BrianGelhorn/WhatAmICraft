#!/usr/bin/env python3
from copy import deepcopy

from produce_mystery_v2 import BANK_PATH, ROOT, VARIANTS, read_json, render_path, selected_config, validate_episode, voice_specs


def rejected(episode: dict, expected: str) -> None:
    try:
        validate_episode(episode)
    except RuntimeError as error:
        assert expected in str(error), error
    else:
        raise AssertionError(f"Expected validation error containing: {expected}")


episode = read_json(BANK_PATH)["episodes"][0]
validate_episode(episode)
expected_frames = {"fast": 465, "balanced": 495, "comment_bait": 506}

for variant in VARIANTS:
    config = selected_config(episode, variant)
    timeline = config["timeline"]
    scenes = [timeline["hook"], *timeline["hints"], timeline["countdown"], timeline["reveal"], timeline["cta"], timeline["loop"]]
    assert scenes[0]["from"] == 0
    assert all(right["from"] == left["from"] + left["durationInFrames"] for left, right in zip(scenes, scenes[1:]))
    assert scenes[-1]["from"] + scenes[-1]["durationInFrames"] == timeline["durationInFrames"]
    assert config["hook"]["question"] and timeline["hints"][0]["from"] <= 35
    assert config["renderMode"] == "final" and timeline["durationInFrames"] == expected_frames[variant]
    assert timeline["cta"]["durationInFrames"] >= {"fast": 60, "balanced": 75, "comment_bait": 90}[variant]
    assert timeline["reveal"]["durationInFrames"] >= 66
    assert config["answer"]["image"] == config["answer"]["silhouette"]
    assert config["reveal"]["answerText"].lower() == config["answer"]["text"].lower()
    assert len(config["hints"]) == 3 and all(1 <= len(hint["fragments"]) <= 2 for hint in config["hints"])
    assert config["cta"]["options"] == ["1", "2", "3"]
    assert config["cta"]["prompt"]
    assert not any(token in config["cta"]["text"].upper() for token in ("YES", "NO", "DID YOU GET", "YOUR TURN", "TYPE ONE"))
    if variant == "comment_bait":
        assert config["cta"]["text"] == "COMMENT 1, 2, OR 3"
    beats = config["retentionBeats"]
    assert beats[0]["frame"] == 0 and beats[-1]["frame"] == timeline["durationInFrames"] - 1
    assert max(right["frame"] - left["frame"] for left, right in zip(beats, beats[1:])) <= 45
    specs = voice_specs(episode, config)
    assert specs[0]["from"] <= 5
    assert all(spec["from"] < spec["sceneEnd"] for spec in specs)
    assert next(spec for spec in specs if spec["id"] == "countdown")["maxTempo"] == 1.6
    reveal_spec = next(spec for spec in specs if spec["id"] == "reveal")
    assert reveal_spec["alignFrame"] == timeline["reveal"]["from"] + 24

preview = selected_config(episode, "balanced", "preview")
assert preview["renderMode"] == "preview"
assert render_path(preview).name == "mystery-trident-v2-balanced-preview.mp4"

used = read_json(ROOT / "data/used-targets.json")
used_ids = set(used.get("target_ids", [])) | {item["id"] for item in used.get("targets", []) if isinstance(item, dict) and item.get("id")}
assert "crossbow" in used_ids
assert all(item["answer"]["id"] != "crossbow" for item in read_json(BANK_PATH)["episodes"])

component = (ROOT / "src/components/mystery/MysteryComponents.tsx").read_text(encoding="utf-8")
for name in (
    "HookScene", "HookQuestion", "MysteryObject", "CategoryBadge", "GlobalProgress", "HintScene",
    "HintHeader", "HintKeyword", "HintVisual", "DurabilityVisual", "CombatRangeVisual", "DrownedVisual",
    "CountdownScene", "RevealTransform", "RevealAnswer", "CommentCTA", "CaptionRenderer", "AudioTimeline",
    "MusicDucker", "LoopBridge", "SafeZoneOverlay", "DebugTimeline",
):
    assert f"export const {name}" in component
assert "Math.random(" not in component and "transition:" not in component
assert "NEXT CLUE" not in component and "×64" not in component and "YOUR TURN" not in component
assert "SAFE_TOP = 170" in component and "SAFE_BOTTOM = 1600" in component
assert "activeTiming.startFrame" in component and "config.cta.prompt" in component
assert 'config.renderMode === "preview"' in component
assert episode["hints"][1]["visualAsset"].endswith("/ZOMBIE.png")
for decorative_primitive in ("finalFlash", "const sweep", "const scan", "borderRight:", "width: `${progress * 100}%`"):
    assert decorative_primitive not in component
assert "CombatRangeVisual config={config} hint={hint}" in component

root = (ROOT / "src/Root.tsx").read_text(encoding="utf-8")
assert 'id="MysteryVideo"' in root and "fps={30}" in root and "width={1080}" in root and "height={1920}" in root
producer = (ROOT / "scripts/produce_mystery_v2.py").read_text(encoding="utf-8")
assert '"maxTempo": 1.6' in producer and '"-af", f"atempo=' in producer
assert '"--scale=0.5"' in producer and '"--contact-sheet"' in producer
assert 'audio/mystery-v2/voice-cache/' in producer and '"voiceSignature": signature' in producer

bad_silhouette = deepcopy(episode)
bad_silhouette["answer"]["silhouette"] = "mc-assets/entity-assets/flat/ARROW.png"
rejected(bad_silhouette, "forma exacta")

late_hint = deepcopy(episode)
late_hint["variants"]["balanced"]["timeline"]["hook"] = 36
rejected(late_hint, "antes de 1.20s")

short_cta = deepcopy(episode)
short_cta["variants"]["comment_bait"]["timeline"]["cta"] = 89
rejected(short_cta, "CTA requiere")

duplicate_hint = deepcopy(episode)
duplicate_hint["hints"][1]["voiceText"] = duplicate_hint["hints"][0]["voiceText"]
rejected(duplicate_hint, "pistas repetidas")

wrong_countdown = deepcopy(episode)
wrong_countdown["countdown"]["voiceText"] = "Three. One. Two."
rejected(wrong_countdown, "números visibles")

contradictory_cta = deepcopy(episode)
contradictory_cta["ctaOptions"]["hint-count"]["displayText"] = "DID YOU GET IT?"
rejected(contradictory_cta, "CTA contradictorio")

print("ok: mystery-v2 retention, audio, CTA and generation contract")
