"""Import legacy MCEdit schematics into modern datapack structures."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import re
import shutil
import struct
import unicodedata
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE_PATTERN = "*MUSHROOM*.zip"
MOUNTED_SOURCE = ROOT / "source-bundle.zip"
STRUCTURE_DIR = "data/studio/structure/assets"


class UnsupportedSchematic(ValueError):
    """A legacy block has no safe Java 1.21.11 conversion."""


class NBT:
    def __init__(self, data: bytes):
        self.stream = io.BytesIO(data)

    def read(self, size: int) -> bytes:
        value = self.stream.read(size)
        if len(value) != size:
            raise ValueError("truncated NBT")
        return value

    def u8(self) -> int:
        return self.read(1)[0]

    def string(self) -> str:
        return self.read(struct.unpack(">H", self.read(2))[0]).decode("utf-8", "replace")

    def payload(self, tag: int):
        if tag == 1:
            return struct.unpack(">b", self.read(1))[0]
        if tag == 2:
            return struct.unpack(">h", self.read(2))[0]
        if tag == 3:
            return struct.unpack(">i", self.read(4))[0]
        if tag == 4:
            return struct.unpack(">q", self.read(8))[0]
        if tag == 5:
            return struct.unpack(">f", self.read(4))[0]
        if tag == 6:
            return struct.unpack(">d", self.read(8))[0]
        if tag == 7:
            return self.read(struct.unpack(">i", self.read(4))[0])
        if tag == 8:
            return self.string()
        if tag == 9:
            element = self.u8()
            size = struct.unpack(">i", self.read(4))[0]
            return [self.payload(element) for _ in range(size)]
        if tag == 10:
            result = {}
            while True:
                child = self.u8()
                if child == 0:
                    return result
                name = self.string()
                result[name] = self.payload(child)
        if tag == 11:
            size = struct.unpack(">i", self.read(4))[0]
            return list(struct.unpack(f">{size}i", self.read(size * 4)))
        if tag == 12:
            size = struct.unpack(">i", self.read(4))[0]
            return list(struct.unpack(f">{size}q", self.read(size * 8)))
        raise ValueError(f"unsupported NBT tag {tag}")

    def root(self) -> dict:
        if self.u8() != 10:
            raise ValueError("schematic root is not a compound")
        self.string()
        return self.payload(10)


def _tag(tag: int, name: str, value: object) -> bytes:
    if tag == 0:
        return b"\x00"
    return bytes([tag]) + struct.pack(">H", len(name.encode("utf-8"))) + name.encode("utf-8") + _payload(tag, value)


def _payload(tag: int, value: object) -> bytes:
    if tag == 1:
        return struct.pack(">b", int(value))
    if tag == 2:
        return struct.pack(">h", int(value))
    if tag == 3:
        return struct.pack(">i", int(value))
    if tag == 4:
        return struct.pack(">q", int(value))
    if tag == 5:
        return struct.pack(">f", float(value))
    if tag == 6:
        return struct.pack(">d", float(value))
    if tag == 7:
        value = bytes(value)
        return struct.pack(">i", len(value)) + value
    if tag == 8:
        raw = str(value).encode("utf-8")
        return struct.pack(">H", len(raw)) + raw
    if tag == 9:
        element, values = value
        return bytes([element]) + struct.pack(">i", len(values)) + b"".join(_payload(element, item) for item in values)
    if tag == 10:
        return b"".join(_tag(child[0], name, child[1]) for name, child in value.items()) + b"\x00"
    if tag == 11:
        return struct.pack(">i", len(value)) + struct.pack(f">{len(value)}i", *value)
    raise ValueError(f"unsupported output NBT tag {tag}")


def _list_tag(name: str, element: int, values: list) -> bytes:
    return _tag(9, name, (element, values))


def _legacy_state(block_id: int, data: int) -> tuple[str, dict[str, str]]:
    simple = {
        1: "stone", 2: "grass_block", 3: "dirt", 4: "cobblestone", 8: "water", 9: "water", 12: "sand",
        13: "gravel", 20: "glass", 24: "sandstone", 30: "cobweb", 48: "mossy_cobblestone",
        49: "obsidian", 78: "snow", 80: "snow_block", 82: "clay", 87: "netherrack",
        88: "soul_sand", 89: "glowstone", 98: "stone_bricks", 121: "end_stone", 155: "quartz_block", 159: "white_terracotta",
        111: "lily_pad", 172: "terracotta", 174: "packed_ice",
    }
    if block_id in simple:
        return f"minecraft:{simple[block_id]}", {}
    if block_id == 0:
        return "minecraft:air", {}
    if block_id == 5:
        return f"minecraft:{['oak', 'spruce', 'birch', 'jungle', 'acacia', 'dark_oak'][data & 7]}_planks", {}
    stairs = {53: "oak", 67: "cobblestone", 107: "jungle", 108: "brick", 109: "stone_brick", 114: "nether_brick", 128: "sandstone", 134: "spruce", 135: "birch", 136: "jungle", 156: "quartz", 163: "acacia", 164: "dark_oak"}
    if block_id in stairs:
        return f"minecraft:{stairs[block_id]}_stairs", {"facing": ["east", "west", "south", "north"][data & 3], "half": "top" if data & 4 else "bottom", "shape": "straight"}
    if block_id == 17:
        wood = ["oak", "spruce", "birch", "jungle"][data & 3]
        axis = {0: "y", 4: "x", 8: "z", 12: "y"}.get(data & 12, "y")
        return f"minecraft:{wood}_log", {"axis": axis}
    if block_id == 18:
        wood = ["oak", "spruce", "birch", "jungle"][data & 3]
        return f"minecraft:{wood}_leaves", {"persistent": "true", "distance": "1"}
    if block_id == 161:
        wood = ["acacia", "dark_oak"][data & 1]
        return f"minecraft:{wood}_leaves", {"persistent": "true", "distance": "1"}
    if block_id == 162:
        wood = ["acacia", "dark_oak"][data & 1]
        axis = {0: "y", 4: "x", 8: "z", 12: "y"}.get(data & 12, "y")
        return f"minecraft:{wood}_log", {"axis": axis}
    if block_id == 31:
        return ("minecraft:fern" if data == 2 else "minecraft:short_grass"), {}
    if block_id == 35:
        colors = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray", "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black"]
        return f"minecraft:{colors[data & 15]}_wool", {}
    if block_id == 39:
        return "minecraft:brown_mushroom", {}
    if block_id == 40:
        return "minecraft:red_mushroom", {}
    if block_id in (99, 100):
        name = "brown_mushroom_block" if block_id == 99 else "red_mushroom_block"
        props = {side: str(bool(data & bit)).lower() for side, bit in (("up", 1), ("down", 2), ("north", 4), ("south", 8), ("west", 16), ("east", 32))}
        return f"minecraft:{name}", props
    if block_id == 37:
        return "minecraft:dandelion", {}
    if block_id == 38:
        flowers = ["poppy", "blue_orchid", "allium", "azure_bluet", "red_tulip", "orange_tulip", "white_tulip", "pink_tulip", "oxeye_daisy", "cornflower", "lily_of_the_valley"]
        return f"minecraft:{flowers[min(data, len(flowers) - 1)]}", {}
    if block_id == 81:
        return "minecraft:cactus", {}
    if block_id == 86:
        return "minecraft:pumpkin", {"facing": ["south", "west", "north", "east"][data & 3]}
    if block_id == 103:
        return "minecraft:melon", {}
    if block_id == 125:
        return f"minecraft:{['oak', 'spruce', 'birch', 'jungle', 'acacia', 'dark_oak'][data & 7]}_planks", {}
    if block_id == 126:
        return "minecraft:cocoa", {"facing": ["south", "west", "north", "east"][data & 3], "age": str((data >> 2) & 3)}
    if block_id == 127:
        return "minecraft:cocoa", {"facing": ["south", "west", "north", "east"][data & 3], "age": str((data >> 2) & 3)}
    if block_id == 85:
        return "minecraft:oak_fence", {}
    if block_id in (188, 189, 190, 191, 192):
        wood = {188: "spruce", 189: "birch", 190: "jungle", 191: "dark_oak", 192: "acacia"}[block_id]
        return f"minecraft:{wood}_fence", {}
    if block_id == 143:
        return "minecraft:oak_button", {"face": "wall", "facing": "north", "powered": "false"}
    if block_id in (183, 184, 185, 186, 187):
        wood = {183: "spruce", 184: "birch", 185: "jungle", 186: "dark_oak", 187: "acacia"}[block_id]
        return f"minecraft:{wood}_fence_gate", {"facing": "north", "in_wall": "false", "open": "false", "powered": "false"}
    if block_id in (43, 44):
        return "minecraft:stone_slab", {"type": "top" if data & 8 else "bottom"}
    if block_id == 50:
        return "minecraft:torch", {}
    if block_id == 54:
        return "minecraft:chest", {"facing": "north"}
    raise UnsupportedSchematic(f"unsupported legacy block {block_id}:{data}")


def _safe_id(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value or "asset"


def _name_info(filename: str) -> tuple[str, str, int]:
    stem = Path(filename).stem
    stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode()
    match = re.match(r"(?:MUSH(?:-VAR)?\.)?(.+?)\.n(?:[^A-Za-z0-9]?)([A-Za-z]+|\d+)\.(\d+)blocks$", stem, re.I)
    if not match:
        return _safe_id(stem), "1", 0
    family, variant, count = match.groups()
    return _safe_id(family), variant.lower(), int(count)


def _legacy_schematic(blob: bytes) -> tuple[dict, dict]:
    root = NBT(gzip.decompress(blob)).root()
    width, height, length = (int(root[key]) for key in ("Width", "Height", "Length"))
    blocks = bytes(root.get("Blocks", b""))
    data = bytes(root.get("Data", b""))
    extra = bytes(root.get("AddBlocks", b""))
    states = []
    for index, block in enumerate(blocks):
        high = (extra[index // 2] >> (4 if index % 2 == 0 else 0)) & 15 if index // 2 < len(extra) else 0
        states.append(_legacy_state(block | (high << 8), data[index] if index < len(data) else 0))
    palette: list[tuple[str, dict]] = [("minecraft:air", {})]
    palette_index = {("minecraft:air", ()): 0}
    placed = []
    for index, state in enumerate(states):
        if state[0] == "minecraft:air":
            continue
        key = (state[0], tuple(sorted(state[1].items())))
        if key not in palette_index:
            palette.append(state)
            palette_index[key] = len(palette) - 1
        x = index % width
        z = (index // width) % length
        y = index // (width * length)
        placed.append((x, y, z, palette_index[key]))
    palette_nbt = [{"Name": name, **({"Properties": {key: value for key, value in props.items()}} if props else {})} for name, props in palette]
    block_nbt = [{"pos": [x, y, z], "state": state} for x, y, z, state in placed]
    for tile in root.get("TileEntities", []):
        if not isinstance(tile, dict):
            continue
        x, y, z = int(tile.get("x", 0)), int(tile.get("y", 0)), int(tile.get("z", 0))
        nbt = {key: value for key, value in tile.items() if key not in {"x", "y", "z"}}
        if nbt.get("id") == "MobSpawner":
            nbt["id"] = "minecraft:spawner"
        for block in block_nbt:
            if block["pos"] == [x, y, z]:
                block["nbt"] = nbt
                break
    entities = []
    for entity in root.get("Entities", []):
        if not isinstance(entity, dict):
            continue
        pos = entity.get("Pos", [entity.get("x", 0.0), entity.get("y", 0.0), entity.get("z", 0.0)])
        entities.append({"pos": [float(pos[0]), float(pos[1]), float(pos[2])], "blockPos": [int(pos[0]), int(pos[1]), int(pos[2])], "nbt": entity})
    structure = {
        "size": [width, height, length],
        "palette": palette_nbt,
        "blocks": block_nbt,
        "entities": entities,
    }
    meta = {"size": [width, height, length], "blocks": len(placed), "palette": len(palette), "entities": len(entities)}
    return structure, meta


def _encode_structure(structure: dict) -> bytes:
    palette = []
    for item in structure["palette"]:
        children = {"Name": (8, item["Name"])}
        if "Properties" in item:
            children["Properties"] = (10, {key: (8, value) for key, value in item["Properties"].items()})
        palette.append(children)
    blocks = []
    for item in structure["blocks"]:
        children = {"pos": (11, item["pos"]), "state": (3, item["state"])}
        if "nbt" in item:
            children["nbt"] = (10, {key: _typed(value) for key, value in item["nbt"].items()})
        blocks.append(children)
    entities = []
    for item in structure["entities"]:
        entities.append({"pos": (9, (6, item["pos"])), "blockPos": (11, item["blockPos"]), "nbt": (10, {key: _typed(value) for key, value in item["nbt"].items()})})
    root = {"size": (11, structure["size"]), "palette": (9, (10, palette)), "blocks": (9, (10, blocks)), "entities": (9, (10, entities))}
    return gzip.compress(_tag(10, "", root))


def _typed(value):
    if isinstance(value, bool):
        return (1, int(value))
    if isinstance(value, int):
        return (3, value)
    if isinstance(value, float):
        return (6, value)
    if isinstance(value, str):
        return (8, value)
    if isinstance(value, bytes):
        return (7, value)
    if isinstance(value, list):
        if not value:
            return (9, (1, []))
        if all(isinstance(item, (int, bool)) for item in value):
            element = 3
        elif all(isinstance(item, (int, float)) for item in value):
            element = 6
        elif all(isinstance(item, dict) for item in value):
            element = 10
        else:
            element = 8
        return (9, (element, value))
    if isinstance(value, dict):
        return (10, {key: _typed(item) for key, item in value.items()})
    return (8, str(value))


def find_source() -> Path | None:
    sources = find_sources()
    return sources[0] if sources else None


def find_sources() -> list[Path]:
    selected = os.environ.get("STUDIO_ASSET_ZIPS") or os.environ.get("STUDIO_ASSET_ZIP")
    if selected:
        paths = []
        for value in selected.split(os.pathsep):
            candidate = Path(value)
            if candidate.parent != ROOT / "uploads" or candidate.suffix.lower() != ".zip" or not candidate.is_file():
                raise ValueError("STUDIO_ASSET_ZIPS must name ZIPs in /studio/uploads")
            paths.append(candidate)
        return paths
    if MOUNTED_SOURCE.is_file() and zipfile.is_zipfile(MOUNTED_SOURCE):
        return [MOUNTED_SOURCE]
    candidates = [path for path in sorted(ROOT.parent.glob(SOURCE_PATTERN)) if zipfile.is_zipfile(path)]
    return candidates[:1]


def _read_structure(path: Path) -> dict:
    return NBT(gzip.decompress(path.read_bytes())).root()


def inspect_bundle(source: Path) -> dict:
    """Read a ZIP inventory without writing structures or touching a world."""
    summary = {"level_dat": 0, "region_files": 0, "schematic_files": 0, "nbt_files": 0,
               "command_files": 0, "tag_files": 0}
    warnings, catalog = [], []
    with zipfile.ZipFile(source) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            lower = name.lower()
            parts = lower.split("/")
            if parts[-1] == "level.dat":
                summary["level_dat"] += 1
            if lower.endswith(".mca") and "region" in parts:
                summary["region_files"] += 1
            if lower.endswith(".nbt"):
                summary["nbt_files"] += 1
            if lower.endswith(".mcfunction"):
                summary["command_files"] += 1
            if "/tags/" in f"/{lower}" and lower.endswith(".json"):
                summary["tag_files"] += 1
            if not lower.endswith(".schematic"):
                continue
            summary["schematic_files"] += 1
            try:
                family, variant, filename_count = _name_info(Path(name).name)
                _, meta = _legacy_schematic(archive.read(info))
                asset_id = f"{family}_{variant}"
                used = {item["id"] for item in catalog}
                suffix = 2
                while asset_id in used:
                    asset_id = f"{family}_{variant}_{suffix}"
                    suffix += 1
                catalog.append({"id": asset_id, "family": family, "variant": variant,
                                "source": name, "filename_blocks": filename_count, **meta,
                                "scenes": ["f03", "f09", "f10", "f11"]})
            except Exception as error:
                warnings.append(f"{name}: not imported ({error})")
    world = bool(summary["level_dat"] or summary["region_files"])
    schematics = bool(summary["schematic_files"])
    kind = "both" if world and schematics else "world" if world else "schematics" if schematics else "unknown"
    if kind == "world" and not catalog:
        warnings.append("World archive detected; no extractable schematic assets were found.")
    if world and not (summary["level_dat"] and summary["region_files"]):
        warnings.append("World archive looks incomplete (missing level.dat or region files).")
    if schematics and len(catalog) != summary["schematic_files"]:
        warnings.append("Some schematics were not cataloged; see the per-file warnings.")
    catalog.sort(key=lambda item: item["id"])
    return {"source": source.name, "kind": kind, "members": summary, "assets": catalog, "warnings": warnings}


def _rotated(x: int, z: int, width: int, length: int, rotation: str) -> tuple[int, int]:
    if rotation == "clockwise_90":
        return length - 1 - z, x
    if rotation == "counterclockwise_90":
        return z, width - 1 - x
    return x, z


def _state_text(state: dict) -> str:
    properties = state.get("Properties", {})
    if not properties:
        return state["Name"]
    suffix = ",".join(f"{key}={value}" for key, value in sorted(properties.items()))
    return f"{state['Name']}[{suffix}]"


def import_bundles(out: Path, sources: list[Path]) -> list[dict]:
    structure_root = out / STRUCTURE_DIR
    shutil.rmtree(out / "data/studio/structures/assets", ignore_errors=True)
    structure_root.mkdir(parents=True, exist_ok=True)
    for path in structure_root.glob("*.nbt"):
        path.unlink()
    if not sources:
        return []
    catalog = []
    seen_archives = set()
    for source in sources:
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest in seen_archives:
            continue
        seen_archives.add(digest)
        with zipfile.ZipFile(source) as archive:
            for info in archive.infolist():
                if not info.filename.lower().endswith(".schematic"):
                    continue
                family, variant, filename_count = _name_info(Path(info.filename).name)
                structure, meta = _legacy_schematic(archive.read(info))
                asset_id = f"{family}_{variant}"
                target = structure_root / f"{asset_id}.nbt"
                if target.exists():
                    suffix = 2
                    while (structure_root / f"{asset_id}_{suffix}.nbt").exists():
                        suffix += 1
                    asset_id = f"{asset_id}_{suffix}"
                    target = structure_root / f"{asset_id}.nbt"
                target.write_bytes(_encode_structure(structure))
                catalog.append({"id": asset_id, "archive": source.name, "family": family, "variant": variant, "source": Path(info.filename).name, "filename_blocks": filename_count, **meta, "tags": ["organic", "bundle"], "scenes": ["f03", "f09", "f10", "f11"]})
    catalog.sort(key=lambda item: item["id"])
    names = [source.name for source in sources]
    (out / "asset_catalog.json").write_text(json.dumps({"source": names[0] if len(names) == 1 else names, "count": len(catalog), "assets": catalog}, indent=2, sort_keys=True), encoding="utf-8")
    return catalog


def import_bundle(out: Path) -> list[dict]:
    return import_bundles(out, find_sources())


def placement_commands(scene: str, seed: int, origin: tuple[int, int], catalog: list[dict], height_fn, structure_root: Path | None = None) -> tuple[list[str], dict | None]:
    if scene != "f11" or not catalog:
        return [], None
    selected = []
    families = set()
    ordered = sorted(catalog, key=lambda item: (item.get("archive", ""), item["family"], item["id"]))
    for asset in ordered:
        if asset["family"] in families:
            continue
        families.add(asset["family"])
        selected.append(asset)
        if len(selected) == 8:
            break
    points = [(-18, 8), (18, 12), (-28, 34), (30, 42), (-8, 54), (22, 66), (-42, 58), (44, 24)]
    commands = []
    for index, (asset, (x, z)) in enumerate(zip(selected, points)):
        y = height_fn(scene, seed, x, z) + 1
        rotation = ("none", "clockwise_90", "counterclockwise_90")[(seed + index) % 3]
        if structure_root is None:
            commands.append(f"place template studio:assets/{asset['id']} {origin[0] + x} {y} {origin[1] + z} {rotation} none 1.0 {seed + index}")
        else:
            structure = _read_structure(structure_root / f"{asset['id']}.nbt")
            width, _, length = structure["size"]
            for block in structure["blocks"]:
                state = structure["palette"][block["state"]]
                tx, tz = _rotated(block["pos"][0], block["pos"][2], width, length, rotation)
                commands.append(f"setblock {origin[0] + x + tx} {y + block['pos'][1]} {origin[1] + z + tz} {_state_text(state)}")
    marker = [origin[0] + 14, 81, origin[1] + 1]
    commands.append(f"setblock {marker[0]} {marker[1]} {marker[2]} minecraft:structure_void")
    return commands, {"block": "minecraft:structure_void", "pos": marker, "assets": [asset["id"] for asset in selected], "placement": "blocks" if structure_root else "templates"}
