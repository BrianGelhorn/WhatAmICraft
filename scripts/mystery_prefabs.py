#!/usr/bin/env python3
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data/mystery-v2-visual-prefabs.json"
GENERATED_PATH = ROOT / "src/generated/mystery-v2-visual-prefabs.json"
PREFAB_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ROLES = ("property-state", "action-interaction", "origin-context")


def load_prefab_catalog(path: Path = CATALOG_PATH) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version") != 1 or value.get("format") != "mystery-v2-visual-prefabs" or value.get("status") != "draft":
        raise RuntimeError("Catálogo de prefabs inválido")
    prefabs = value.get("prefabs")
    if not isinstance(prefabs, list) or len(prefabs) != 30:
        raise RuntimeError("El catálogo debe contener exactamente 30 prefabs")
    numbers = [prefab.get("number") for prefab in prefabs if isinstance(prefab, dict)]
    ids = [prefab.get("id") for prefab in prefabs if isinstance(prefab, dict)]
    if numbers != list(range(1, 31)) or len(ids) != len(set(ids)):
        raise RuntimeError("Los prefabs deben estar numerados 1-30 y tener IDs únicos")
    for prefab in prefabs:
        number = prefab["number"]
        if not PREFAB_ID.fullmatch(str(prefab.get("id", ""))):
            raise RuntimeError(f"Prefab {number}: id inválido")
        if prefab.get("role") != ROLES[(number - 1) // 10]:
            raise RuntimeError(f"Prefab {number}: role no coincide con su bloque de galería")
        if prefab.get("status") != "draft":
            raise RuntimeError(f"Prefab {number}: solo puede estar draft antes de aprobación")
        for field in ("title", "description"):
            if not isinstance(prefab.get(field), str) or not prefab[field].strip():
                raise RuntimeError(f"Prefab {number}: falta {field}")
        for field in ("relations", "supportedKinds", "assets"):
            values = prefab.get(field)
            if not isinstance(values, list) or not values or len(values) != len(set(values)):
                raise RuntimeError(f"Prefab {number}: {field} debe ser una lista única no vacía")
        for asset in prefab["assets"]:
            if not (ROOT / "public" / asset).is_file():
                raise RuntimeError(f"Prefab {number}: falta public/{asset}")
    return value
