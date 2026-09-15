"""Deterministic, column-accurate terrain for the small studio scenes."""
from __future__ import annotations

import math
import random

SIZE = 192
HALF = SIZE // 2
CELL = 1  # A command column is the height-map column; never approximate terrain in steps.
BASE_Y = -63
EDGE_Y = 72
KEEP = {"f02": (0, 0, 12, 8), "f03": (0, 0, 12, 14), "f04": (0, 0, 12, 9), "f08": (0, 0, 12, 8), "f09": (0, 0, 12, 8), "f10": (0, -4, 12, 9), "f11": (0, 0, 12, 8)}
PALETTES = {
    "f02": ("minecraft:grass_block", "minecraft:dirt", "minecraft:oak_log", "minecraft:oak_leaves"),
    "f03": ("minecraft:podzol", "minecraft:stone", "minecraft:spruce_log", "minecraft:spruce_leaves"),
    "f04": ("minecraft:grass_block", "minecraft:dirt", "minecraft:birch_log", "minecraft:birch_leaves"),
    "f08": ("minecraft:stone", "minecraft:tuff", "minecraft:oak_log", "minecraft:oak_leaves"),
    "f09": ("minecraft:grass_block", "minecraft:dirt", "minecraft:oak_log", "minecraft:oak_leaves"),
    "f10": ("minecraft:moss_block", "minecraft:dirt", "minecraft:birch_log", "minecraft:birch_leaves"),
    "f11": ("minecraft:podzol", "minecraft:dirt", "minecraft:spruce_log", "minecraft:spruce_leaves"),
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
    elif scene == "f08":
        mass = _gauss(x, z, -48, 30, 46, 15) + _gauss(x, z, 54, -38, 44, 13)
    elif scene == "f09":
        mass = _gauss(x, z, -42, -32, 58, 12) + _gauss(x, z, 48, 42, 52, 11)
    elif scene == "f10":
        mass = _gauss(x, z, -50, 40, 48, 13) + _gauss(x, z, 50, -44, 46, 12)
    elif scene == "f11":
        mass = _gauss(x, z, -48, 36, 50, 18) + _gauss(x, z, 52, -34, 46, 14)
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
    if scene == "f08" and slope >= 3:
        return "minecraft:cobblestone"
    if scene == "f11" and slope >= 3:
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
    # Nothing generated stands above Y126 (height cap 115 + tallest spruce),
    # so clearing stops at Y131 instead of Y143.
    for z in range(-HALF, HALF, 4):
        commands.append(_fill(ox - HALF, 73, oz + z, ox + HALF - 1, 101, oz + z + 3, "minecraft:air"))
        commands.append(_fill(ox - HALF, 102, oz + z, ox + HALF - 1, 131, oz + z + 3, "minecraft:air"))
    for x in range(-HALF, HALF):
        for z in range(-HALF, HALF):
            commands.extend(_column(ox, oz, scene, seed, x, z))
    # Functional plots are level, clear to camera height, and founded by the normal columns.
    x1, z1, x2, z2 = KEEP[scene]
    commands.append(_fill(ox + x1, 81, oz + z1, ox + x2, 92, oz + z2, "minecraft:air"))
    return commands


def _scatter(scene: str, seed: int, tag: str, zmin: int, zmax: int, target: int,
             min_d2: int, existing: list[tuple[int, int]], attempts: int = 60000) -> list[tuple[int, int]]:
    rng = random.Random(f"{scene}:{seed}:{tag}")
    points: list[tuple[int, int]] = []
    for _ in range(attempts):
        if len(points) == target:
            return points
        x, z = rng.randint(-91, 91), rng.randint(zmin, zmax)
        if _plot_distance(scene, x, z) < 10:
            continue
        if scene == "f02" and math.hypot(x + 22, z - 13) < 10:
            continue
        if scene == "f03" and -10 <= x <= 22 and -2 <= z <= 25:
            continue
        if scene == "f04" and 10 <= x <= 36 and -94 <= z <= 94:
            continue
        if all((x - px) ** 2 + (z - pz) ** 2 >= min_d2 for px, pz in existing + points):
            points.append((x, z))
    raise ValueError(f"Unable to place {target} trees for {scene}/{tag}, seed {seed}")


def _tree_candidates(scene: str, seed: int) -> list[tuple[int, int]]:
    """Clustered rear/side woodland plus a dense background band; foreground stays a camera corridor."""
    main = {"f02": 75, "f03": 65, "f04": 72, "f08": 70, "f09": 72, "f10": 68, "f11": 64}[scene]
    back = {"f02": 30, "f03": 28, "f04": 30, "f08": 28, "f09": 30, "f10": 28, "f11": 32}[scene]
    points = _scatter(scene, seed, "wood", -10, 91, main, 64, [])
    return points + _scatter(scene, seed, "back", 55, 91, back, 36, points)


def trees(scene: str, seed: int) -> list[tuple[int, int]]:
    return _tree_candidates(scene, seed)


def variant(scene: str, seed: int, x: int, z: int) -> int:
    """Deterministic shape variant 0..2, shared by builders and tests."""
    return abs(x * 5 + z * 11 + seed) % 3


def hero_index(scene: str, seed: int) -> int:
    """Tallest-base candidate becomes the landmark tree; deterministic."""
    points = trees(scene, seed)
    return max(range(len(points)), key=lambda i: height(scene, seed, *points[i]))


def _leaf(x: int, y: int, z: int, block: str) -> str:
    return f"setblock {x} {y} {z} {block}[persistent=true]"


def _disc(commands: list[str], ox: int, oz: int, x: int, z: int, y: int, r: int, leaf: str, diamond: bool = False) -> None:
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            if (abs(dx) + abs(dz) <= r) if diamond else (dx * dx + dz * dz <= r * r + 1):
                commands.append(_leaf(ox + x + dx, y, oz + z + dz, leaf))


def _oak(ox: int, oz: int, seed: int, x: int, z: int, scene: str, hero: bool = False) -> list[str]:
    base = height(scene, seed, x, z)
    v = variant(scene, seed, x, z)
    if v == 1:  # tall emergent, narrow high crown
        h, layers = 9 + (abs(x * 3 - z + seed) % 2), ((0, 2), (1, 2), (2, 2), (3, 1))
    elif v == 2:  # low bushy, wide crown near the ground
        h, layers = 4 + (abs(x + z * 3 + seed) % 2), ((0, 3), (1, 4), (2, 3), (3, 1))
    else:  # spreading, broad irregular crown
        h, layers = 6 + (abs(x * 7 + z + seed) % 3), ((0, 2), (1, 3), (2, 3), (3, 2), (4, 1))
    if hero:
        h += 2
    h = max(4, min(h, 124 - base))  # crown top never clears into the Y131 air band
    leaf = "minecraft:oak_leaves"
    commands = []
    for dy, radius in ((h - 1 + d, r) for d, r in layers):
        _disc(commands, ox, oz, x, z, base + 1 + dy, radius, leaf)
    # Leaves first; the trunk and short branches deliberately replace their centres.
    commands.append(_fill(ox + x, base + 1, oz + z, ox + x, base + h + 1, oz + z, "minecraft:oak_log"))
    commands += [f"setblock {ox+x+1} {base+h} {oz+z} minecraft:oak_log", f"setblock {ox+x-1} {base+h-1} {oz+z} minecraft:oak_log"]
    if hero:
        commands.append(f"setblock {ox+x} {base+h-2} {oz+z+1} minecraft:oak_log")
    return commands


def _spruce(ox: int, oz: int, seed: int, x: int, z: int, scene: str, hero: bool = False) -> list[str]:
    base = height(scene, seed, x, z)
    v = variant(scene, seed, x, z)
    if v == 1:  # giant, broad tapering spire
        h, tiers = 11 + (abs(x - z + seed) % 2), ((3, 3), (5, 4), (7, 3), (9, 2), (11, 1))
    elif v == 2:  # short and wide
        h, tiers = 6 + (abs(x * 2 + z + seed) % 2), ((2, 3), (4, 2), (6, 1))
    else:  # classic conical
        h, tiers = 8 + (abs(x + z * 5 + seed) % 3), ((3, 3), (5, 3), (7, 2), (9, 1))
    if hero:
        h += 2
    h = max(5, min(h, 127 - base))  # tip never clears into the Y131 air band
    leaf = "minecraft:spruce_leaves"
    commands = []
    for dy, radius in tiers:
        if dy > h:
            continue
        _disc(commands, ox, oz, x, z, base + dy, radius, leaf, diamond=True)
    commands.append(_leaf(ox + x, base + h + 1, oz + z, leaf))
    commands.append(_fill(ox + x, base + 1, oz + z, ox + x, base + h, oz + z, "minecraft:spruce_log"))
    return commands


def _birch(ox: int, oz: int, seed: int, x: int, z: int, scene: str, hero: bool = False) -> list[str]:
    base = height(scene, seed, x, z)
    v = variant(scene, seed, x, z)
    if v == 2:  # tall, slightly broader top
        h, layers = 9 + (abs(x - z * 2 + seed) % 2), ((0, 1), (1, 2), (2, 2), (3, 1))
    else:  # slender
        h, layers = 6 + (abs(x * 3 - z + seed) % 3), ((0, 1), (1, 2), (2, 1))
    if hero:
        h += 2
    h = max(5, min(h, 126 - base))  # crown top never clears into the Y131 air band
    leaf = "minecraft:birch_leaves"
    commands = []
    for dy, radius in ((h - 1 + d, r) for d, r in layers):
        _disc(commands, ox, oz, x, z, base + 1 + dy, radius, leaf)
    commands.append(_fill(ox + x, base + 1, oz + z, ox + x, base + h, oz + z, "minecraft:birch_log"))
    if v == 1:  # twin: second slimmer stem rooted on its own column
        base2 = height(scene, seed, x + 1, z)
        h2 = max(4, min(h - 1, 126 - base2))
        for dy, radius in ((h2 - 1, 1), (h2, 2)):
            _disc(commands, ox, oz, x + 1, z, base2 + 1 + dy, radius, leaf)
        commands.append(_fill(ox + x + 1, base2 + 1, oz + z, ox + x + 1, base2 + h2, oz + z, "minecraft:birch_log"))
    return commands


def _f02_features(ox: int, oz: int, seed: int) -> list[str]:
    # The clear terrace is the real, hazard-free attack lane; damage stays beyond it.
    commands = [_fill(ox + lane, 80, oz, ox + lane, 80, oz + 8, "minecraft:dirt_path") for lane in (2, 6, 10)]
    commands += [f"setblock {ox+x} {height('f02', seed, x, z)} {oz+z} minecraft:coarse_dirt"
                 for z in (-4, 20, 21) for x in range(-12, -7)]
    for x in (-10, -9, -8, 15, 16, 17):
        base = height("f02", seed, x, 18)
        commands.append(_fill(ox+x, base+1, oz+18, ox+x, base+2, oz+18, "minecraft:oak_log"))
    commands += [f"setblock {ox+x} {height('f02', seed, x, z)+1} {oz+z} minecraft:cracked_stone_bricks"
                 for x, z in ((-13, 17), (-12, 18), (14, 18), (16, 19), (-30, 8), (28, 12))]
    # Grounded ruined gate and rubble read as a battlefield, never as a trap.
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
    # No emissive block is installed: the back pedestals compare player-placed real lights.
    # The offset entrance/baffle keeps direct skylight away from the covered test room.
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
        _fill(ox + 5, 81, oz + 8, ox + 6, 84, oz + 8, "minecraft:deepslate_tiles"),
        _fill(ox + 3, 80, oz + 13, ox + 4, 81, oz + 15, "minecraft:polished_deepslate"),
        _fill(ox + 8, 80, oz + 13, ox + 9, 81, oz + 15, "minecraft:polished_deepslate"),
        _fill(ox + 5, 80, oz + 13, ox + 7, 81, oz + 15, "minecraft:stone_bricks"),
    ]


def _f08_features(ox: int, oz: int) -> list[str]:
    # Two cobble plinths display the real blocks side by side; the take compares them.
    return [
        f"setblock {ox+4} 81 {oz+4} minecraft:cobblestone",
        f"setblock {ox+8} 81 {oz+4} minecraft:cobblestone",
        f"setblock {ox+4} 82 {oz+4} minecraft:amethyst_block",
        f"setblock {ox+8} 82 {oz+4} minecraft:calcite",
    ]


def _f09_features(ox: int, oz: int) -> list[str]:
    # A single worn center line; the items stay in hand, nothing is installed.
    return [_fill(ox + 6, 80, oz, ox + 6, 80, oz + 8, "minecraft:dirt_path")]


def _f10_features(ox: int, oz: int) -> list[str]:
    # Contained basin: stone rim, water over a sand bed, kelp planted real.
    return [
        _fill(ox + 3, 80, oz + 1, ox + 9, 80, oz + 1, "minecraft:stone"),
        _fill(ox + 3, 80, oz + 7, ox + 9, 80, oz + 7, "minecraft:stone"),
        _fill(ox + 3, 80, oz + 1, ox + 3, 80, oz + 7, "minecraft:stone"),
        _fill(ox + 9, 80, oz + 1, ox + 9, 80, oz + 7, "minecraft:stone"),
        _fill(ox + 4, 79, oz + 2, ox + 8, 79, oz + 6, "minecraft:sand"),
        _fill(ox + 4, 80, oz + 2, ox + 8, 80, oz + 6, "minecraft:water"),
        f"setblock {ox+5} 80 {oz+4} minecraft:kelp",
        f"setblock {ox+7} 80 {oz+5} minecraft:kelp",
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
        commands.append(_fill(ox + x, 81, oz + z, ox + x, 131, oz + z, "minecraft:air"))
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
        "f08": [(-9, 4), (21, 4), (-16, -10), (28, 16), (0, -14), (12, 22)],
        "f09": [(-9, 4), (21, 4), (-14, -8), (26, 14), (2, -14), (10, 20)],
        "f10": [(-9, 2), (21, 2), (-12, -12), (24, 16), (4, -16), (8, 20)],
        "f11": [(-20, 12), (20, 18), (-30, 42), (30, 54), (-8, 66), (22, 72)],
        "f04": [(-9, 17), (-21, 27), (7, 17), (-46, -14), (38, 38), (-4, -20)],
    }[scene]
    blocks = {"f02": "minecraft:poppy", "f03": "minecraft:brown_mushroom", "f04": "minecraft:cornflower", "f08": "minecraft:tuff", "f09": "minecraft:short_grass", "f10": "minecraft:azure_bluet", "f11": "minecraft:brown_mushroom"}
    want = {"f02": "minecraft:grass_block", "f03": "minecraft:podzol", "f04": "minecraft:grass_block", "f08": "minecraft:stone", "f09": "minecraft:grass_block", "f10": "minecraft:moss_block", "f11": "minecraft:podzol"}[scene]
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


def _bush(ox: int, oz: int, x: int, y: int, z: int, leaf: str) -> list[str]:
    """Low plus-shaped blob with a cap; needs no support (persistent leaves)."""
    return [_leaf(ox + x + dx, y + 1, oz + z + dz, leaf) for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))] + [_leaf(ox + x, y + 2, oz + z, leaf)]


def _fallen_log(ox: int, oz: int, seed: int, scene: str, x: int, z: int) -> list[str]:
    """Four grounded segments following the terrain step by step."""
    _, _, log, _ = PALETTES[scene]
    return [f"setblock {ox+x+k} {height(scene, seed, x + k, z)+1} {oz+z} {log}" for k in range(4)]


def _undergrowth_spot(scene: str, seed: int, x: int, z: int) -> bool:
    """Floor dressing stays out of the plot, structures and open water."""
    if _plot_distance(scene, x, z) < 4:
        return False
    if scene == "f02":
        return math.hypot(x + 21, z - 13) >= 8
    if scene == "f03":
        return not (-6 <= x <= 18 and 0 <= z <= 24)
    if scene in ("f08", "f09"):
        return not (-4 <= x <= 16 and -4 <= z <= 12)
    if scene == "f10":
        return not (-4 <= x <= 16 and -8 <= z <= 13)
    if scene == "f11":
        return not (-4 <= x <= 16 and -4 <= z <= 12)
    return not (14 <= x <= 32 or (-3 <= x <= 14 and -2 <= z <= 12))


def _undergrowth(scene: str, ox: int, oz: int, seed: int, points: list[tuple[int, int]]) -> list[str]:
    _, _, _, leaves = PALETTES[scene]
    tuft = {"f02": "minecraft:short_grass", "f03": "minecraft:moss_carpet", "f04": "minecraft:short_grass", "f08": "minecraft:short_grass", "f09": "minecraft:short_grass", "f10": "minecraft:short_grass", "f11": "minecraft:fern"}[scene]
    rocks = ["minecraft:stone", "minecraft:cobblestone", "minecraft:mossy_cobblestone"]
    commands = []
    rng = random.Random(f"{scene}:{seed}:under")
    for i, (x, z) in enumerate(points):
        if i % 2 == 0:
            ux, uz = x + rng.randint(-6, 6), z + rng.randint(-6, 6)
            if (abs(ux) <= 90 and abs(uz) <= 90
                    and _undergrowth_spot(scene, seed, ux, uz)
                    and all((ux - px) ** 2 + (uz - pz) ** 2 >= 9 for px, pz in points)):
                commands.extend(_bush(ox, oz, ux, height(scene, seed, ux, uz), uz, leaves))
        if i % 5 == 0:
            ux, uz = x + rng.randint(-6, 6), z + rng.randint(-6, 6)
            cells = [(ux + k, uz) for k in range(4)]
            if (all(abs(cx) <= 90 and abs(cz) <= 90 for cx, cz in cells)
                    and all(_undergrowth_spot(scene, seed, cx, cz) for cx, cz in cells)):
                commands.extend(_fallen_log(ox, oz, seed, scene, ux, uz))
        if i % 4 == 1:
            ux, uz = x + rng.randint(-8, 8), z + rng.randint(-8, 8)
            if (abs(ux) <= 90 and abs(uz) <= 90
                    and _undergrowth_spot(scene, seed, ux, uz)
                    and all((ux - px) ** 2 + (uz - pz) ** 2 >= 4 for px, pz in points)):
                uy = height(scene, seed, ux, uz)
                if scene in ("f03", "f11") or _surface(scene, seed, ux, uz, uy) == "minecraft:grass_block":
                    for dx, dz in ((0, 0), (1, 0), (0, 1), (1, 1)):
                        vx, vz = ux + dx, uz + dz
                        if abs(vx) > 90 or abs(vz) > 90 or not _undergrowth_spot(scene, seed, vx, vz):
                            continue
                        vy = height(scene, seed, vx, vz)
                        if scene in ("f03", "f11") or _surface(scene, seed, vx, vz, vy) == "minecraft:grass_block":
                            commands.append(f"setblock {ox+vx} {vy+1} {oz+vz} {tuft}")
        if i % 6 == 2:
            ux, uz = x + rng.randint(-8, 8), z + rng.randint(-8, 8)
            cells = [(ux + dx, uz + dz) for dx, dz in ((0, 0), (1, 0), (0, 1))]
            if (all(abs(cx) <= 90 and abs(cz) <= 90 for cx, cz in cells)
                    and all(_undergrowth_spot(scene, seed, cx, cz) for cx, cz in cells)
                    and all((cx - px) ** 2 + (cz - pz) ** 2 >= 4 for cx, cz in cells for px, pz in points)):
                for (cx, cz), block in zip(cells, rocks):
                    commands.append(f"setblock {ox+cx} {height(scene, seed, cx, cz)+1} {oz+cz} {block}")
    return commands


def feature_commands(scene: str, seed: int, origin: tuple[int, int]) -> list[str]:
    ox, oz = origin
    points = trees(scene, seed)
    landmark = hero_index(scene, seed)
    builders = {"f02": _oak, "f03": _spruce, "f04": _birch, "f08": _oak, "f09": _oak, "f10": _birch, "f11": _spruce}
    commands: list[str] = []
    for i, (x, z) in enumerate(points):
        commands.extend(builders[scene](ox, oz, seed, x, z, scene, hero=(i == landmark)))
    commands.extend(_undergrowth(scene, ox, oz, seed, points))
    if scene == "f02":
        commands.extend(_f02_features(ox, oz, seed))
    elif scene == "f03":
        commands.extend(_f03_features(ox, oz))
    elif scene == "f04":
        commands.extend(_f04_features(ox, oz, seed))
    elif scene == "f08":
        commands.extend(_f08_features(ox, oz))
    elif scene == "f09":
        commands.extend(_f09_features(ox, oz))
    elif scene == "f10":
        commands.extend(_f10_features(ox, oz))
    else:
        commands.extend([f"setblock {ox+x} {height(scene, seed, x, z)+1} {oz+z} minecraft:podzol" for x, z in ((-20, 12), (20, 18), (-30, 42), (30, 54))])
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
        checkpoints["roof"] = {"block": "minecraft:deepslate_tiles", "pos": [ox + 6, 87, oz + 14]}
        checkpoints["pedestal"] = {"block": "minecraft:polished_deepslate", "pos": [ox + 3, 81, oz + 14]}
    elif scene == "f04":
        checkpoints["water"] = {"block": "minecraft:water", "pos": [ox + 23, 80, oz]}
        checkpoints["plant"] = {"block": "minecraft:sugar_cane", "pos": [ox + 8, 81, oz + 2]}
    elif scene == "f08":
        checkpoints["display"] = {"block": "minecraft:amethyst_block", "pos": [ox + 4, 82, oz + 4]}
    elif scene == "f09":
        checkpoints["lane"] = {"block": "minecraft:dirt_path", "pos": [ox + 6, 80, oz + 4]}
    elif scene == "f10":
        checkpoints["water"] = {"block": "minecraft:water", "pos": [ox + 6, 80, oz + 4]}
        checkpoints["plant"] = {"block": "minecraft:kelp", "pos": [ox + 5, 80, oz + 4]}
    else:  # f11
        checkpoints["grove_floor"] = {"block": "minecraft:podzol", "pos": [ox - 20, height(scene, seed, -20, 12), oz + 12]}
    return {"origin": [ox, oz], "bounds": [ox - HALF, oz - HALF, ox + HALF - 1, oz + HALF - 1], "keepout": [ox + KEEP[scene][0], oz + KEEP[scene][1], ox + KEEP[scene][2], oz + KEEP[scene][3]], "heightmap": {"edge_y": EDGE_Y, "peak": peak_y, "tree_count": len(trees(scene, seed)), "camera": [ox + 6, 81, oz + 1]}, "checkpoints": checkpoints}
