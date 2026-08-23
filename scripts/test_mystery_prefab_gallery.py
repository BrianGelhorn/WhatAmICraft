#!/usr/bin/env python3
from pathlib import Path

from mystery_prefabs import GENERATED_PATH, ROOT, load_prefab_catalog


catalog = load_prefab_catalog()
prefabs = catalog["prefabs"]
assert len(prefabs) == 30
assert [prefab["number"] for prefab in prefabs] == list(range(1, 31))
assert [prefab["role"] for prefab in prefabs[:10]] == ["property-state"] * 10
assert [prefab["role"] for prefab in prefabs[10:20]] == ["action-interaction"] * 10
assert [prefab["role"] for prefab in prefabs[20:]] == ["origin-context"] * 10
assert catalog["status"] == "review"
assert [prefab["id"] for prefab in prefabs if prefab["status"] == "approved"] == ["durability-loss", "stack-limit", "enchantment-glint"]
assert all(prefab["status"] == ("approved" if prefab["id"] == "enchantment-glint" else "draft") for prefab in prefabs[2:])
assert len({relation for prefab in prefabs for relation in prefab["relations"]}) >= 30
ids = {prefab["id"] for prefab in prefabs}
assert {"repair-restore", "grants-status-effect", "mob-interaction", "special-movement", "block-transformation"} <= ids
assert not {"smelting-progress", "blocks-damage", "ignite-target", "water-interaction", "teleport-use"} & ids

component = (ROOT / "src/components/mystery/MysteryPrefabGallery.tsx").read_text(encoding="utf-8")
for prefab in prefabs:
    assert f'case "{prefab["id"]}"' in component
assert "Math.random(" not in component and "transition:" not in component
assert "Unknown prefab preview" in component
assert component.count("<Steve") >= 10
durability = (ROOT / "src/components/mystery/DurabilityLossVisual.tsx").read_text(encoding="utf-8")
assert "durabilitySteps = [1, 0.82, 0.6, 0.38, 0.18, 0]" in durability
assert "durabilityStepFrames = [0, 14, 26, 36, 44, 50]" in durability
assert "useCurrentFrame() % 84" in durability
assert "breakPieces" in durability and "clipPath" in durability
assert "<DurabilityLossVisual assetSrc={a}" in component
assert "<EnchantmentGlintVisual assetSrc={a}" in component
assert "<CooldownVisual assetSrc={a}" in component
cooldown = (ROOT / "src/components/mystery/CooldownVisual.tsx").read_text(encoding="utf-8")
assert 'label = inUse ? "" : ready ? "READY" : "WAIT"' in cooldown
assert "conic-gradient(from 0deg" in cooldown and "progress * 100" not in cooldown
assert "iconRotation" in cooldown and "useProgress" in cooldown

root = (ROOT / "src/Root.tsx").read_text(encoding="utf-8")
assert 'id="MysteryPrefabGallery"' in root and "width={3840}" in root and "height={2160}" in root
assert GENERATED_PATH.is_file()
generated = load_prefab_catalog(GENERATED_PATH)
assert generated == catalog

api = (ROOT / "scripts/clues_api.py").read_text(encoding="utf-8")
assert 'parsed.path == "/api/clue-prefabs"' in api

print("ok: 3 approved and 27 draft mystery prefabs, shared renderer, catalog API")
