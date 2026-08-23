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
assert all(prefab["status"] == "draft" for prefab in prefabs)
assert len({relation for prefab in prefabs for relation in prefab["relations"]}) >= 30

component = (ROOT / "src/components/mystery/MysteryPrefabGallery.tsx").read_text(encoding="utf-8")
for prefab in prefabs:
    assert f'case "{prefab["id"]}"' in component
assert "Math.random(" not in component and "transition:" not in component
assert "Unknown prefab preview" in component

root = (ROOT / "src/Root.tsx").read_text(encoding="utf-8")
assert 'id="MysteryPrefabGallery"' in root and "width={3840}" in root and "height={2160}" in root
assert GENERATED_PATH.is_file()
generated = load_prefab_catalog(GENERATED_PATH)
assert generated == catalog

api = (ROOT / "scripts/clues_api.py").read_text(encoding="utf-8")
assert 'parsed.path == "/api/clue-prefabs"' in api

print("ok: 30 numbered draft mystery prefabs, gallery renderer, catalog API")
