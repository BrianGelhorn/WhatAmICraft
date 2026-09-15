#!/usr/bin/env python3
"""Build and validate the native studio datapack.  It never contacts a server."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "generated" / "studio"
PACK_FORMAT = 81  # Java 1.21.11 data pack format

# These are structured transcriptions of docs/minecraft-clip-library.md section 8.
BASE = [
    "gamemode creative @s", "execute in minecraft:overworld run tp @s 0 90 -8",
    "gamerule minecraft:advance_time false", "gamerule minecraft:advance_weather false",
    "gamerule minecraft:spawn_mobs false", "time set 6000", "weather clear",
]
SETS = {
"g11": ["fill 0 80 14 12 80 22 minecraft:stone_bricks", "fill 5 81 18 7 90 18 minecraft:stone_bricks", "fill 4 81 18 4 89 18 minecraft:ladder[facing=west]", "fill 2 90 16 8 90 20 minecraft:stone_bricks", "setblock 4 90 18 minecraft:air", "setblock 7 91 19 minecraft:sea_lantern", "tp @s 2.5 81 18.5 -90 10"],
"g12": ["fill 40 80 14 43 80 22 minecraft:stone_bricks", "fill 49 80 14 52 80 22 minecraft:stone_bricks", "fill 44 71 14 48 79 22 minecraft:air", "fill 44 70 14 48 70 22 minecraft:black_concrete", "fill 44 80 17 48 80 18 minecraft:oak_planks", "tp @s 41.5 81 17.5 -90 0"],
"g13": ["fill 80 80 14 92 80 22 minecraft:stone_bricks", "fill 80 81 14 80 84 22 minecraft:gray_concrete", "fill 92 81 14 92 84 22 minecraft:gray_concrete", "fill 80 85 14 92 85 17 minecraft:gray_concrete", "fill 80 81 18 84 84 18 minecraft:gray_concrete", "fill 87 81 18 92 84 18 minecraft:gray_concrete", "setblock 81 82 21 minecraft:sea_lantern", "setblock 91 82 21 minecraft:sea_lantern", "tp @s 85.5 81 15.5 0 0"],
"f02": ["fill 120 80 14 132 80 22 minecraft:stone_bricks", "fill 120 81 14 132 86 22 minecraft:air", "fill 122 80 14 122 80 22 minecraft:quartz_block", "fill 126 80 14 126 80 22 minecraft:quartz_block", "fill 130 80 14 130 80 22 minecraft:quartz_block", "summon minecraft:armor_stand 126 81 18 {ShowArms:1b,NoBasePlate:1b}", "tp @s 121.5 81 18.5 -90 10"],
"f03": ["fill 160 80 14 172 80 22 minecraft:stone_bricks", "fill 160 80 8 172 80 13 minecraft:stone_bricks", "fill 160 81 14 160 84 22 minecraft:stone_bricks", "fill 172 81 14 172 84 22 minecraft:stone_bricks", "fill 160 85 14 172 85 22 minecraft:stone_bricks", "fill 160 81 22 172 84 22 minecraft:stone_bricks", "fill 160 81 14 164 84 14 minecraft:stone_bricks", "fill 168 81 14 172 84 14 minecraft:stone_bricks", "fill 165 84 14 167 84 14 minecraft:stone_bricks", "setblock 166 81 18 minecraft:stone_bricks", "tp @s 166.5 81 9.5 0 0"],
"f04": ["fill 200 80 14 205 80 22 minecraft:soul_sand", "fill 206 80 13 206 80 22 minecraft:stone_bricks", "fill 207 80 15 212 80 22 minecraft:sand", "fill 207 80 14 211 80 14 minecraft:water", "fill 207 80 13 211 80 13 minecraft:stone_bricks", "setblock 212 80 14 minecraft:stone_bricks", "tp @s 203.5 81 18.5 -90 0"],
}
DURATIONS = {"g11":180,"g12":180,"g13":180,"f02":180,"f03":180,"f04":180}
KITS = {
"f02": ["minecraft:mace", "minecraft:trident"],
"f03": ["minecraft:sea_lantern", "minecraft:soul_lantern"],
"f04": ["minecraft:nether_wart", "minecraft:sugar_cane"],
}
KILLS = {
"f02": ["kill @e[type=minecraft:armor_stand,x=119,y=79,z=13,dx=14,dy=10,dz=10]"],
}
BRIEFS = {
"g11": ("trepada con escalera (actuación natural, sin familia)", "Subí la torre por la escalera y posá arriba para la toma."),
"g12": ("cruce por puente sobre foso (actuación natural, sin familia)", "Cruzá el puente de roble de plataforma a plataforma."),
"g13": ("cruce de umbral bajo pórtico (actuación natural, sin familia)", "Entrá por el pórtico y marcá el cruce del umbral."),
"f02": ("armas no apilables que pierden durabilidad con el uso (mace/trident)", "En survival, golpeá el dummy con mace y trident por turnos mirando la barra de durabilidad en HUD."),
"f03": ("bloques de luz (sea_lantern/soul_lantern)", "Caminá por la senda hasta la puerta, entrá al cuarto oscuro y colocá cada bloque real en el pedestal."),
"f04": ("plantas de cultivo (nether_wart/sugar_cane)", "Plantá cada cultivo real en su sustrato: wart en arena de almas, caña en arena junto al agua."),
}
CHUNKS = {"g11":[(0,0),(0,1)], "g12":[(2,0),(2,1),(3,0),(3,1)], "g13":[(5,0),(5,1)], "f02":[(7,0),(7,1),(8,0),(8,1)], "f03":[(10,0),(10,1),(11,0),(11,1)], "f04":[(12,0),(12,1),(13,0),(13,1)]}

def write(rel: str, lines: list[str]) -> None:
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def guard() -> list[str]:
    check = "execute unless dimension minecraft:overworld"
    box = "execute unless entity @s[x=-16,y=64,z=-32,dx=400,dy=80,dz=64]"
    return [f"{check} run tellraw @s {{\"text\":\"Studio: use the Overworld lab control area.\",\"color\":\"red\"}}", f"{check} run return 0", f"{box} run tellraw @s {{\"text\":\"Studio: stand in the reserved lab control area first.\",\"color\":\"red\"}}", f"{box} run return 0"]

def build() -> None:
    write("pack.mcmeta", [json.dumps({"pack":{"pack_format":PACK_FORMAT,"description":"WhatAmICraft isolated filming studio (Java 1.21.11)"}}, indent=2)])
    write("data/minecraft/tags/function/load.json", ['{"values":["studio:load"]}'])
    write("data/studio/function/load.mcfunction", ["scoreboard objectives add studio_scene dummy", "scoreboard objectives add studio_run dummy", "scoreboard objectives add studio_chunk dummy"])
    write("data/studio/function/help.mcfunction", ["tellraw @s {\"text\":\"Studio: scene/g11..g13,f02..f04/setup -> start; reset; next; stop. OP only.\",\"color\":\"gold\"}", "tellraw @s {\"text\":\"Manual acting: G11 climb, G12 crossing, G13 threshold. F02/F03/F04 are correlated test stages (F02 mace/trident, F03 sea_lantern/soul_lantern, F04 nether_wart/sugar_cane). Start clears inventory, gives the scene kit and marks the take; f02 drops you in survival with a practice dummy. Replay Mod is client-only.\",\"color\":\"gray\"}"])
    unload = []
    for i, scene in enumerate(SETS, 1):
        for n, (cx, cz) in enumerate(CHUNKS[scene]):
            key = f"#studio_{scene}_{n}"
            unload.append(f"execute if score #scene studio_scene matches {i} if score {key} studio_chunk matches 0 run forceload remove {cx * 16} {cz * 16}")
    write("data/studio/function/unload_active.mcfunction", unload)
    for index, (scene, commands) in enumerate(SETS.items(), 1):
        force = []
        for n, (cx, cz) in enumerate(CHUNKS[scene]):
            key = f"#studio_{scene}_{n}"
            force += [f"execute in minecraft:overworld store success score {key} studio_chunk run forceload query {cx * 16} {cz * 16}", f"execute in minecraft:overworld if score {key} studio_chunk matches 0 run forceload add {cx * 16} {cz * 16}"]
        setup = guard()+["function studio:reset", "function studio:unload_active", f"scoreboard players set @s studio_scene {index}", f"scoreboard players set #scene studio_scene {index}", "scoreboard players set @s studio_run 0"] + force + [f"schedule function studio:scene/{scene}/setup_apply 2t replace", f"tellraw @s {{\"text\":\"{scene.upper()} loading its bounded set.\",\"color\":\"yellow\"}}"]
        write(f"data/studio/function/scene/{scene}/setup.mcfunction", setup)
        initial = [f"execute in minecraft:overworld run {c}" for c in BASE+commands]
        write(f"data/studio/function/scene/{scene}/setup_apply.mcfunction", [f"execute unless score #scene studio_scene matches {index} run return 0", "execute as @a at @s in minecraft:overworld run function studio:scene/"+scene+"/setup_apply_actor"])
        write(f"data/studio/function/scene/{scene}/setup_apply_actor.mcfunction", initial + [f"tellraw @s {{\"text\":\"Representa: {BRIEFS[scene][0]}\",\"color\":\"aqua\"}}", f"tellraw @s {{\"text\":\"Hacé: {BRIEFS[scene][1]}\",\"color\":\"yellow\"}}", f"tellraw @s {{\"text\":\"{scene.upper()} ready ({DURATIONS[scene]} frames at 30 fps). Use /function studio:start.\",\"color\":\"green\"}}"])
        # Reapply the full bounded SET, so reset is repeatable instead of
        # merely deleting leftovers.
        write(f"data/studio/function/scene/{scene}/reset.mcfunction", ["function studio:stop_schedules"] + [f"execute in minecraft:overworld run {c}" for c in KILLS.get(scene, [])] + initial + ["tellraw @s {\"text\":\"Studio scene reset to its initial state.\",\"color\":\"yellow\"}"])
    write("data/studio/function/stop_schedules.mcfunction", [f"schedule clear studio:scene/{scene}/setup_apply" for scene in SETS])
    write("data/studio/function/start.mcfunction", guard()+["execute unless score @s studio_scene = #scene studio_scene run return 0", "execute unless score @s studio_scene matches 1.. run return 0", "scoreboard players set @s studio_run 1"] + [f"execute if score @s studio_scene matches {i} run function studio:scene/{s}/start" for i,s in enumerate(SETS,1)] + ["return 1"])
    for scene in SETS:
        kit = [f"give @s {item} 1" for item in KITS.get(scene, [])]
        survival = ["gamemode survival @s"] if scene == "f02" else []
        lines = guard()+[f"execute unless score @s studio_scene matches {list(SETS).index(scene)+1} run return 0", "clear @s"] + survival + kit + [f"tellraw @s {{\"text\":\"{scene.upper()} started. Kit given. Action is manual.\",\"color\":\"aqua\"}}"]
        write(f"data/studio/function/scene/{scene}/start.mcfunction", lines)
    write("data/studio/function/reset.mcfunction", guard()+["execute unless score @s studio_scene = #scene studio_scene run return 0", "execute unless score @s studio_scene matches 1.. run return 0"]+[f"execute if score @s studio_scene matches {i} run function studio:scene/{s}/reset" for i,s in enumerate(SETS,1)] + ["return 1"])
    write("data/studio/function/stop.mcfunction", guard()+["function studio:reset", "function studio:unload_active", "scoreboard players set #scene studio_scene 0", "scoreboard players set @s studio_scene 0", "scoreboard players set @s studio_run 0", "gamemode creative @s", "tellraw @s {\"text\":\"Studio released; world data was not deleted.\",\"color\":\"yellow\"}"])
    next_lines=guard()+["execute unless score @s studio_scene = #scene studio_scene run return 0", "execute unless score @s studio_scene matches 1.. run return 0", "scoreboard players set @s studio_run 0"]
    for i, scene in enumerate(SETS,1):
        target = list(SETS)[i % len(SETS)]
        next_lines += [f"execute if score @s studio_scene matches {i} run function studio:scene/{target}/setup"]
    next_lines += ["return 1"]
    write("data/studio/function/next.mcfunction", next_lines)

def validate() -> None:
    assert list(SETS) == ["g11", "g12", "g13", "f02", "f03", "f04"]
    assert all(DURATIONS[s] in (120,150,180) for s in SETS)
    assert set(DURATIONS) == set(SETS) == set(CHUNKS)
    assert any("minecraft:ladder[facing=west]" in c for c in SETS["g11"])
    assert any("minecraft:oak_planks" in c for c in SETS["g12"])
    assert any("minecraft:sea_lantern" in c for c in SETS["g13"])
    assert any("minecraft:quartz_block" in c for c in SETS["f02"])
    assert any("168 81 14" in c for c in SETS["f03"])
    assert any("minecraft:soul_sand" in c for c in SETS["f04"])
    assert any("armor_stand" in c for c in SETS["f02"])
    assert set(BRIEFS) == set(SETS)
    assert all(len(v) == 2 and all(isinstance(t, str) and t.strip() for t in v) for v in BRIEFS.values())
    assert KITS["f02"] == ["minecraft:mace", "minecraft:trident"]
    assert any("armor_stand" in c for c in KILLS["f02"])
    assert not any("half=" in c for xs in SETS.values() for c in xs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "validate"), nargs="?", default="build")
    args = parser.parse_args()
    validate()
    if args.command == "build":
        build()
        print(f"Built {OUT}")
    else:
        print("Scene source is valid")
