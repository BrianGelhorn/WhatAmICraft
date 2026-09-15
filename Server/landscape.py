"""Deterministic, column-accurate terrain for the small studio scenes."""
from __future__ import annotations

import math
import random

SIZE = 192
HALF = SIZE // 2
CELL = 1  # A command column is the height-map column; never approximate terrain in steps.
BASE_Y = -63
EDGE_Y = 72
KEEP = {"f02": (0, 0, 12, 8), "f03": (0, 0, 12, 14), "f04": (0, 0, 12, 9)}
PALETTES = {
    "f02": ("minecraft:grass_block", "minecraft:dirt", "minecraft:oak_log", "minecraft:oak_leaves"),
    "f03": ("minecraft:podzol", "minecraft:stone", "minecraft:spruce_log", "minecraft:spruce_leaves"),
    "f04": ("minecraft:grass_block", "minecraft:dirt", "minecraft:birch_log", "minecraft:birch_leaves"),
}


def _smooth(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def _gauss(x: int, z: int, cx: int, cz: int, radius: float, amplitude: float) -> float:
    return amplitude * math.exp(-((x - cx) ** 2 + (z - cz) ** 2) / (radius * radius))


def _noise(seed: int, x: int, z: int) -> float:
    """Continuous low-frequency variation, not per-block voxel noise."""
    phase_x = (seed % 997) / 997.0 * math.tau
    phase_z = (seed % 577) / 577.0 * math.tau
    return math.sin(x / 13.0 + phase_x) * .8 + math.cos(z / 17.0 + phase_z) * .7


def _plot_distance(scene: str, x: int, z: int) -> float:
    x1, z1, x2, z2 = KEEP[scene]
    dx = max(x1 - x, 0, x - x2)
    dz = max(z1 - z, 0, z - z2)
    return math.hypot(dx, dz)


def height(scene: str, seed: int, x: int, z: int) -> int:
    """Actual terrain surface for one local block column, including the action terrace."""
    edge = min(x + HALF, HALF - 1 - x, z + HALF, HALF - 1 - z)
    if edge <= 0:
        return EDGE_Y
    if scene == "f02":
        mass = _gauss(x, z, -50, 26, 48, 16) + _gauss(x, z, 50, 48, 44, 10)
    elif scene == "f03":
        # The high rear mass is terrain, so the sanctuary reads as carved into a mountain.
        mass = _gauss(x, z, 10, 62, 54, 39) + _gauss(x, z, -54, 52, 44, 20)
    else:
        mass = _gauss(x, z, -54, 38, 50, 15) + _gauss(x, z, 56, 54, 48, 12)
    natural = EDGE_Y + (mass + _noise(seed, x, z)) * _smooth(edge / 12.0)
    # A twelve-block apron turns the clear Y80 exercise area into a terrace, not a cliff.
    terrace = _smooth(1.0 - _plot_distance(scene, x, z) / 12.0)
    surface = natural * (1.0 - terrace) + 80 * terrace
    if scene == "f04":
        near_z = max(-90, min(89, z))
        center = 23 + round(3 * math.sin(near_z / 10.0))
        distance = math.hypot(max(0, abs(x - center) - 4), z - near_z)
        shore = _smooth(1 - distance / 9.0)
        surface = surface * (1 - shore) + 80 * shore
    return min(115, max(EDGE_Y, round(surface)))


def _surface(scene: str, seed: int, x: int, z: int, y: int) -> str:
    ground, _, _, _ = PALETTES[scene]
    slope = max(abs(y - height(scene, seed, x - 1, z)), abs(y - height(scene, seed, x + 1, z)), abs(y - height(scene, seed, x, z - 1)), abs(y - height(scene, seed, x, z + 1)))
    if scene == "f03" and (y >= 92 or slope >= 3):
        return "minecraft:stone"
    if scene == "f02" and slope >= 3:
        return "minecraft:coarse_dirt"
    if scene == "f04" and y >= 84:
        return "minecraft:coarse_dirt"
    return ground


def _fill(x1: int, y1: int, z1: int, x2: int, y2: int, z2: int, block: str) -> str:
    return f"fill {x1} {y1} {z1} {x2} {y2} {z2} {block}"


def _column(ox: int, oz: int, scene: str, seed: int, x: int, z: int) -> list[str]:
    y = height(scene, seed, x, z)
    _, under, _, _ = PALETTES[scene]
    return [_fill(ox + x, BASE_Y, oz + z, ox + x, y - 1, oz + z, under),
            _fill(ox + x, y, oz + z, ox + x, y, oz + z, _surface(scene, seed, x, z, y))]


def terrain_commands(scene: str, seed: int, origin: tuple[int, int]) -> list[str]:
    """Clear the bounded work volume then build every terrain column from bedrock upward."""
    ox, oz = origin
    commands = []
    # Strips 4 deep, split in Y so each clear stays within /fill's 32,768 cap.
    for z in range(-HALF, HALF, 4):
        commands.append(_fill(ox - HALF, 73, oz + z, ox + HALF - 1, 107, oz + z + 3, "minecraft:air"))
        commands.append(_fill(ox - HALF, 108, oz + z, ox + HALF - 1, 143, oz + z + 3, "minecraft:air"))
    for x in range(-HALF, HALF):
        for z in range(-HALF, HALF):
            commands.extend(_column(ox, oz, scene, seed, x, z))
    # Functional plots are level, clear to camera height, and founded by the normal columns.
    x1, z1, x2, z2 = KEEP[scene]
    commands.append(_fill(ox + x1, 81, oz + z1, ox + x2, 92, oz + z2, "minecraft:air"))
    return commands


def _tree_candidates(scene: str, seed: int) -> list[tuple[int, int]]:
    """Clustered rear/side woodland; the negative-z foreground stays a camera corridor."""
    target = {"f02": 60, "f03": 55, "f04": 58}[scene]
    rng = random.Random(f"{scene}:{seed}")
    points: list[tuple[int, int]] = []
    for _ in range(20000):
        if len(points) == target:
            return points
        x, z = rng.randint(-91, 91), rng.randint(-10, 91)
        if _plot_distance(scene, x, z) < 10:
            continue
        if scene == "f02" and math.hypot(x + 22, z - 13) < 10:
            continue
        if scene == "f03" and -10 <= x <= 22 and -2 <= z <= 25:
            continue
        if scene == "f04" and 10 <= x <= 36 and -94 <= z <= 94:
            continue
        if all((x - px) ** 2 + (z - pz) ** 2 >= 64 for px, pz in points):
            points.append((x, z))
    raise ValueError(f"Unable to place {target} trees for {scene}, seed {seed}")


def trees(scene: str, seed: int) -> list[tuple[int, int]]:
    return _tree_candidates(scene, seed)


def _leaf(x: int, y: int, z: int, block: str) -> str:
    return f"setblock {x} {y} {z} {block}[persistent=true]"


def _oak(ox: int, oz: int, seed: int, x: int, z: int) -> list[str]:
    base, h = height("f02", seed, x, z), 5 + (abs(x * 7 + z + seed) % 3)
    leaf = "minecraft:oak_leaves"
    commands = []
    for dy, radius in ((h - 1, 2), (h, 3), (h + 1, 2), (h + 2, 1)):
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if dx * dx + dz * dz <= radius * radius + 1:
                    commands.append(_leaf(ox + x + dx, base + 1 + dy, oz + z + dz, leaf))
    # Leaves first; the trunk and two short branches deliberately replace their centres.
    commands.append(_fill(ox + x, base + 1, oz + z, ox + x, base + h + 1, oz + z, "minecraft:oak_log"))
    commands += [f"setblock {ox+x+1} {base+h} {oz+z} minecraft:oak_log", f"setblock {ox+x-1} {base+h-1} {oz+z} minecraft:oak_log"]
    return commands


def _spruce(ox: int, oz: int, seed: int, x: int, z: int) -> list[str]:
    base, h = height("f03", seed, x, z), 8 + (abs(x + z * 5 + seed) % 3)
    leaf = "minecraft:spruce_leaves"
    commands = []
    for dy, radius in ((3, 3), (5, 3), (7, 2), (9, 1)):
        if dy > h:
            continue
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if abs(dx) + abs(dz) <= radius:
                    commands.append(_leaf(ox + x + dx, base + dy, oz + z + dz, leaf))
    commands.append(_leaf(ox + x, base + h + 1, oz + z, leaf))
    commands.append(_fill(ox + x, base + 1, oz + z, ox + x, base + h, oz + z, "minecraft:spruce_log"))
    return commands


def _birch(ox: int, oz: int, seed: int, x: int, z: int) -> list[str]:
    base, h = height("f04", seed, x, z), 6 + (abs(x * 3 - z + seed) % 3)
    leaf = "minecraft:birch_leaves"
    commands = []
    for dy, radius in ((h - 1, 1), (h, 2), (h + 1, 1)):
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if dx * dx + dz * dz <= radius * radius:
                    commands.append(_leaf(ox + x + dx, base + 1 + dy, oz + z + dz, leaf))
    commands.append(_fill(ox + x, base + 1, oz + z, ox + x, base + h, oz + z, "minecraft:birch_log"))
    return commands


def _f02_features(ox: int, oz: int, seed: int) -> list[str]:
    commands = [_fill(ox + lane, 80, oz, ox + lane, 80, oz + 8, "minecraft:dirt_path") for lane in (2, 6, 10)]
    # Grounded piers and a real opening, rather than seven columns forming a wall.
    top = max(height("f02", seed, x, 13) for x in range(-24, -17)) + 5
    for x, z in ((-24, 13), (-18, 13)):
        base = height("f02", seed, x, z)
        commands.append(_fill(ox + x, base + 1, oz + z, ox + x, top, oz + z, "minecraft:stone_bricks"))
    commands.append(_fill(ox - 23, top, oz + 13, ox - 19, top, oz + 13, "minecraft:mossy_stone_bricks"))
    commands.append(f"setblock {ox-24} {top+1} {oz+13} minecraft:cracked_stone_bricks")
    for x, z, extra in ((-16, 17, 1), (-15, 17, 2), (-16, 18, 2), (-17, 17, 1)):
        base = height("f02", seed, x, z)
        commands.append(_fill(ox+x, base+1, oz+z, ox+x, base+extra, oz+z, "minecraft:cobblestone"))
    commands.append(f"summon minecraft:armor_stand {ox+6} 81 {oz+4} {{Tags:[\"studio_dummy\"],ShowArms:1b,NoBasePlate:1b}}")
    return commands


def _f03_features(ox: int, oz: int) -> list[str]:
    # Terrain provides the mountain. These are only the carved, roofed sanctuary surfaces.
    return [
        _fill(ox, 81, oz + 6, ox + 12, 86, oz + 18, "minecraft:air"),
        _fill(ox, 80, oz + 6, ox + 12, 80, oz + 18, "minecraft:stone_bricks"),
        _fill(ox, 87, oz + 6, ox + 12, 87, oz + 18, "minecraft:deepslate_tiles"),
        _fill(ox, 81, oz + 6, ox, 86, oz + 18, "minecraft:deepslate_tiles"),
        _fill(ox + 12, 81, oz + 6, ox + 12, 86, oz + 18, "minecraft:deepslate_tiles"),
        _fill(ox, 81, oz + 18, ox + 12, 86, oz + 18, "minecraft:deepslate_tiles"),
        _fill(ox, 81, oz + 6, ox + 4, 86, oz + 6, "minecraft:deepslate_tiles"),
        _fill(ox + 8, 81, oz + 6, ox + 12, 86, oz + 6, "minecraft:deepslate_tiles"),
        _fill(ox + 5, 85, oz + 6, ox + 7, 86, oz + 6, "minecraft:chiseled_stone_bricks"),
        _fill(ox + 5, 80, oz + 13, ox + 7, 81, oz + 15, "minecraft:stone_bricks"),
    ]


def _river_cells() -> list[tuple[int, int]]:
    cells = []
    for z in range(-90, 89):
        center = 23 + round(3 * math.sin(z / 10.0))
        cells.extend((x, z) for x in range(center - 2, center + 3))
    return cells


def _f04_features(ox: int, oz: int, seed: int) -> list[str]:
    water = set(_river_cells())
    bank = set()
    for x, z in water:
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, z + dz) not in water:
                bank.add((x + dx, z + dz))
    commands = []
    # Every source has a solid floor; every exposed neighbour is a Y80 dry bank.
    for x, z in sorted(bank | water):
        commands.append(_fill(ox + x, 81, oz + z, ox + x, 143, oz + z, "minecraft:air"))
        commands.append(_fill(ox + x, BASE_Y, oz + z, ox + x, 79, oz + z, "minecraft:dirt"))
        commands.append(f"setblock {ox+x} 80 {oz+z} minecraft:grass_block")
    # All banks exist before any water can tick, even across scheduled batches.
    for x, z in sorted(water):
        commands.append(f"setblock {ox+x} 80 {oz+z} minecraft:water")
    # A short bridge is founded through both banks; terrace crops are at the water's Y80 level.
    for x in range(19, 28):
        commands.append(f"setblock {ox+x} 81 {oz} minecraft:oak_planks")
    for x in (19, 27):
        commands.append(_fill(ox + x, BASE_Y, oz, ox + x, 80, oz, "minecraft:oak_log"))
    commands += [_fill(ox - 1, BASE_Y, oz, ox - 1, 80, oz + 10, "minecraft:stone_bricks"),
                 _fill(ox, 80, oz + 1, ox + 5, 80, oz + 9, "minecraft:soul_sand"),
                 _fill(ox + 7, 80, oz + 2, ox + 12, 80, oz + 9, "minecraft:sand"),
                 _fill(ox + 7, 80, oz + 1, ox + 12, 80, oz + 1, "minecraft:water"),
                 f"setblock {ox+2} 81 {oz+3} minecraft:nether_wart[age=0]",
                 f"setblock {ox+8} 81 {oz+2} minecraft:sugar_cane"]
    return commands


def _accents(scene: str, ox: int, oz: int, seed: int) -> list[str]:
    points = {
        "f02": [(-7, 18), (16, 21), (-31, 4), (-52, -14), (34, 34), (48, -4), (-12, -16)],
        "f03": [(-12, 28), (-34, 18), (26, 31), (-56, -12), (44, 6), (10, -18)],
        "f04": [(-9, 17), (-21, 27), (7, 17), (-46, -14), (38, 38), (-4, -20)],
    }[scene]
    blocks = {"f02": "minecraft:poppy", "f03": "minecraft:brown_mushroom", "f04": "minecraft:cornflower"}
    want = {"f02": "minecraft:grass_block", "f03": "minecraft:podzol", "f04": "minecraft:grass_block"}[scene]
    commands = []
    for x, z in points:
        y = height(scene, seed, x, z)
        if scene == "f03":
            commands.append(f"setblock {ox+x} {y} {oz+z} minecraft:podzol")
            commands.append(f"setblock {ox+x} {y+1} {oz+z} {blocks[scene]}")
        elif _surface(scene, seed, x, z, y) == want:
            commands.append(f"setblock {ox+x} {y+1} {oz+z} {blocks[scene]}")
        else:
            # Slopes get a pebble, never a flower that would pop off invalid soil.
            commands.append(f"setblock {ox+x} {y+1} {oz+z} minecraft:cobblestone")
    return commands


def feature_commands(scene: str, seed: int, origin: tuple[int, int]) -> list[str]:
    ox, oz = origin
    commands: list[str] = []
    for x, z in trees(scene, seed):
        commands.extend(_oak(ox, oz, seed, x, z) if scene == "f02" else _spruce(ox, oz, seed, x, z) if scene == "f03" else _birch(ox, oz, seed, x, z))
    commands.extend(_f02_features(ox, oz, seed) if scene == "f02" else _f03_features(ox, oz) if scene == "f03" else _f04_features(ox, oz, seed))
    commands.extend(_accents(scene, ox, oz, seed))
    return commands


def _peak(scene: str, seed: int) -> tuple[int, int, int]:
    return max(((height(scene, seed, x, z), x, z) for x in range(-HALF, HALF) for z in range(-HALF, HALF)))


def metadata(scene: str, seed: int, origin: tuple[int, int]) -> dict:
    ox, oz = origin
    peak_y, peak_x, peak_z = _peak(scene, seed)
    tx, tz = trees(scene, seed)[0]
    checkpoints = {
        "soil": {"block": "minecraft:soul_sand" if scene == "f04" else PALETTES[scene][0], "pos": [ox + 1, 80, oz + 1]},
        "foundation": {"block": PALETTES[scene][1], "pos": [ox + 1, BASE_Y, oz + 1]},
        "tree_trunk": {"block": PALETTES[scene][2], "pos": [ox + tx, height(scene, seed, tx, tz) + 1, oz + tz]},
        "peak": {"block": _surface(scene, seed, peak_x, peak_z, peak_y), "pos": [ox + peak_x, peak_y, oz + peak_z]},
        "camera": {"block": "minecraft:air", "pos": [ox + 6, 81, oz + 1]},
    }
    if scene == "f02":
        checkpoints["structure"] = {"block": "minecraft:stone_bricks", "pos": [ox - 24, height(scene, seed, -24, 13) + 1, oz + 13]}
    elif scene == "f03":
        checkpoints["structure"] = {"block": "minecraft:stone_bricks", "pos": [ox + 6, 80, oz + 14]}
    else:
        checkpoints["water"] = {"block": "minecraft:water", "pos": [ox + 23, 80, oz]}
        checkpoints["plant"] = {"block": "minecraft:sugar_cane", "pos": [ox + 8, 81, oz + 2]}
    return {"origin": [ox, oz], "bounds": [ox - HALF, oz - HALF, ox + HALF - 1, oz + HALF - 1], "keepout": [ox + KEEP[scene][0], oz + KEEP[scene][1], ox + KEEP[scene][2], oz + KEEP[scene][3]], "heightmap": {"edge_y": EDGE_Y, "peak": peak_y, "tree_count": len(trees(scene, seed)), "camera": [ox + 6, 81, oz + 1]}, "checkpoints": checkpoints}
