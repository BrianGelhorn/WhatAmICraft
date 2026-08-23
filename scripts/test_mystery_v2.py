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
    assert config["hook"]["question"] and config["hook"]["emphasis"] and timeline["hints"][0]["from"] <= 35
    assert config["renderMode"] == "final" and timeline["durationInFrames"] == expected_frames[variant]
    assert timeline["cta"]["durationInFrames"] >= {"fast": 60, "balanced": 75, "comment_bait": 90}[variant]
    assert timeline["reveal"]["durationInFrames"] >= 66
    assert config["answer"]["image"] != config["answer"]["silhouette"]
    assert config["answer"]["silhouette"] == "images/guess-types/hidden/Weapon.png"
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
    "HintHeader", "HintKeyword", "HintVisual", "DurabilityLossPrefab", "StackLimitPrefab", "InventoryPropertiesPrefab", "ItemEntityInteractionPrefab", "EntityEquipmentPrefab",
    "CountdownScene", "RevealTransform", "RevealAnswer", "CommentCTA", "CaptionRenderer", "AudioTimeline",
    "MusicDucker", "LoopBridge", "SafeZoneOverlay", "DebugTimeline",
):
    assert f"export const {name}" in component
assert "Math.random(" not in component and "transition:" not in component
assert "NEXT CLUE" not in component and "×64" not in component and "YOUR TURN" not in component
assert "SAFE_TOP = 170" in component and "SAFE_BOTTOM = 1600" in component
assert "activeTiming.startFrame" in component and "config.cta.prompt" in component
assert 'config.renderMode === "preview"' in component
assert episode["hints"][1]["visual"]["supportingAsset"].endswith("/ZOMBIE.png")
assert [hint["visual"]["prefab"] for hint in episode["hints"]] == ["inventory-properties", "item-entity-interaction", "entity-equipment"]
assert [[step["type"] for step in hint["visual"]["steps"]] for hint in episode["hints"]] == [["durability", "stack-limit"], ["melee", "ranged"], ["holds-answer"]]
assert episode["hints"][0]["voiceText"] == "Loses durability. Won't stack."
assert "wears down" not in episode["hints"][0]["voiceText"].lower()
for decorative_primitive in ("finalFlash", "const sweep", "const scan", "borderRight:", "width: `${progress * 100}%`"):
    assert decorative_primitive not in component
assert "ItemEntityInteractionPrefab config={config} hint={hint}" in component
assert "return <MysteryObject config={config} size={340}" not in component
assert "config.hook.emphasis" in component and "activeStep.label" in component and "const wear =" not in component
assert 'name="Category silhouette"' in component and ">?</div>" in component
assert "progress={0.14}" not in component
assert 'hint.visual.prefab === "durability-loss"' in component
assert 'hint.visual.prefab === "stack-limit"' in component

schema = read_json(ROOT / "schemas/mystery-v2-episode.schema.json")
assert schema["properties"]["schema_version"]["const"] == 2

root = (ROOT / "src/Root.tsx").read_text(encoding="utf-8")
assert 'id="MysteryVideo"' in root and "fps={30}" in root and "width={1080}" in root and "height={1920}" in root
producer = (ROOT / "scripts/produce_mystery_v2.py").read_text(encoding="utf-8")
assert '"maxTempo": 1.6' in producer and '"-af", f"atempo=' in producer
assert '"--scale=0.5"' in producer and '"--contact-sheet"' in producer
assert 'audio/mystery-v2/voice-cache/' in producer and '"voiceSignature": signature' in producer

bad_silhouette = deepcopy(episode)
bad_silhouette["answer"]["silhouette"] = bad_silhouette["answer"]["image"]
rejected(bad_silhouette, "silueta genérica de la categoría")

missing_hook_emphasis = deepcopy(episode)
del missing_hook_emphasis["hookOptions"]["question-first"]["emphasisText"]
rejected(missing_hook_emphasis, "emphasisText")

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

unknown_visual = deepcopy(episode)
unknown_visual["hints"][0]["visual"]["prefab"] = "generic"
rejected(unknown_visual, "prefabricado implementado")

wrong_prefab_step = deepcopy(episode)
wrong_prefab_step["hints"][0]["visual"]["steps"][0]["type"] = "melee"
rejected(wrong_prefab_step, "no es compatible")

approved_durability = deepcopy(episode)
approved_durability["hints"][0]["fragments"] = approved_durability["hints"][0]["fragments"][:1]
approved_durability["hints"][0]["visual"] = {"prefab": "durability-loss", "steps": [approved_durability["hints"][0]["visual"]["steps"][0]]}
validate_episode(approved_durability)

approved_stack = deepcopy(episode)
approved_stack["hints"][0]["fragments"] = ["STACK LIMIT: 16"]
approved_stack["hints"][0]["displayText"] = "STACK LIMIT: 16"
approved_stack["hints"][0]["visual"] = {"prefab": "stack-limit", "steps": [{"type": "stack-limit", "label": "STACK LIMIT", "value": "16", "from": 0}]}
validate_episode(approved_stack)

approved_enchantment = deepcopy(episode)
approved_enchantment["hints"][0]["fragments"] = ["PUEDE ENCANTARSE"]
approved_enchantment["hints"][0]["displayText"] = "PUEDE ENCANTARSE"
approved_enchantment["hints"][0]["visual"] = {"prefab": "enchantment-glint", "steps": [{"type": "enchantment", "label": "ENCHANTABLE", "from": 0}], "supportingAsset": "mc-assets/item-assets/ENCHANTED_BOOK.png"}
validate_episode(approved_enchantment)

late_first_step = deepcopy(episode)
late_first_step["hints"][0]["visual"]["steps"][0]["from"] = 0.1
rejected(late_first_step, "debe empezar en 0")

duplicate_step_time = deepcopy(episode)
duplicate_step_time["hints"][0]["visual"]["steps"][1]["from"] = 0
rejected(duplicate_step_time, "únicos y ascendentes")

missing_stack_value = deepcopy(episode)
del missing_stack_value["hints"][0]["visual"]["steps"][1]["value"]
rejected(missing_stack_value, ".value")

fragment_step_mismatch = deepcopy(episode)
fragment_step_mismatch["hints"][0]["fragments"] = fragment_step_mismatch["hints"][0]["fragments"][:1]
rejected(fragment_step_mismatch, "cantidad de fragments")

missing_supporting_asset = deepcopy(episode)
del missing_supporting_asset["hints"][1]["visual"]["supportingAsset"]
rejected(missing_supporting_asset, "supportingAsset es obligatorio")

unknown_environment = deepcopy(episode)
unknown_environment["hints"][2]["visual"]["environment"] = "random-flash"
rejected(unknown_environment, "environment desconocido")

print("ok: mystery-v2 retention, audio, CTA and generation contract")
