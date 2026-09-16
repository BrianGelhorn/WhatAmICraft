#!/usr/bin/env python3
"""Build bounded, compatible schematic bundles from the source library."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import asset_importer

ROOT = Path(__file__).parent
SOURCES = {
    "Epic Rocks Bundle v2- by bidule995.zip": "epic-rocks-compatible.zip",
    "LemonFoxs Tree Bundle.zip": "lemonfox-trees-compatible.zip",
    "V2-European and mangrove tree - pack by eremilion.zip": "european-mangrove-trees-v2-compatible.zip",
}
MAX_SIZE = 48
MAX_BLOCKS = 10_000


def curate(source: Path, target: Path) -> dict:
    kept, rejected = [], []
    temporary = target.with_suffix(".tmp")
    target.parent.mkdir(exist_ok=True)
    try:
        with zipfile.ZipFile(source) as incoming, zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as outgoing:
            for info in incoming.infolist():
                if not info.filename.lower().endswith(".schematic"):
                    continue
                raw = incoming.read(info)
                try:
                    _, meta = asset_importer._legacy_schematic(raw)
                    if max(meta["size"]) > MAX_SIZE or meta["blocks"] > MAX_BLOCKS:
                        raise ValueError(f"exceeds {MAX_SIZE} blocks or {MAX_BLOCKS} placed blocks")
                    outgoing.writestr(info.filename, raw)
                    kept.append(info.filename)
                except Exception as error:
                    rejected.append({"source": info.filename, "reason": str(error)})
            summary = {"source": source.name, "kept": len(kept), "rejected": len(rejected),
                       "limits": {"max_size": MAX_SIZE, "max_blocks": MAX_BLOCKS}, "warnings": rejected}
            outgoing.writestr("CURATION.json", json.dumps(summary, indent=2, sort_keys=True))
        temporary.replace(target)
        return summary
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    missing = [name for name in SOURCES if not (ROOT / "library/bundles" / name).is_file()]
    if missing:
        raise SystemExit("Missing local source bundles: " + ", ".join(missing))
    for source_name, target_name in SOURCES.items():
        result = curate(ROOT / "library/bundles" / source_name, ROOT / "uploads" / target_name)
        print(f"{target_name}: {result['kept']} activos, {result['rejected']} omitidos")
