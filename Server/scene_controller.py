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
"g01": ["fill -6 80 -6 6 80 8 minecraft:stone_bricks", "fill -5 81 6 5 86 6 minecraft:gray_concrete", "setblock 0 81 0 minecraft:chest[facing=north]", "tp @s 0.5 81 -0.5 0 15"],
"g02": ["fill 34 80 -6 46 80 8 minecraft:stone_bricks", "fill 34 81 0 34 84 7 minecraft:gray_concrete", "fill 46 81 0 46 84 7 minecraft:gray_concrete", "fill 40 81 1 40 84 6 minecraft:gray_concrete", "fill 34 81 7 46 84 7 minecraft:gray_concrete", "tp @s 40.5 81 -1.5 0 0"],
"g03": ["fill 74 80 -5 79 80 6 minecraft:stone_bricks", "fill 80 75 0 82 75 2 minecraft:stone_bricks", "fill 80 76 0 82 78 2 minecraft:air", "fill 80 79 0 82 79 2 minecraft:stone", "fill 80 80 0 82 80 2 minecraft:sand", "tp @s 79 81 1.5 -90 25"],
"g04": ["fill 116 77 -2 128 77 5 minecraft:stone_bricks", "fill 116 80 0 120 80 3 minecraft:stone_bricks", "fill 123 80 0 128 80 3 minecraft:stone_bricks", "fill 122 79 0 122 79 3 minecraft:stone_bricks", "tp @s 118.5 81 1.5 -90 0", "gamemode survival @s"],
"g05": ["gamemode creative @s", "fill 154 80 -3 167 80 5 minecraft:stone_bricks", "fill 165 81 -2 165 85 4 minecraft:gray_concrete", "setblock 156 81 0 minecraft:stone_bricks", "setblock 156 82 0 minecraft:dispenser[facing=east]", "tp @s 160.5 81 1.8 90 0"],
"g06": ["fill 192 80 -18 210 80 14 minecraft:stone_bricks", "fill 200 81 8 202 103 10 minecraft:stone_bricks", "fill 197 81 8 205 81 10 minecraft:stone_bricks", "fill 195 81 -10 197 94 -10 minecraft:gray_concrete", "tp @s 199 81 7 0 -25"],
"g07": ["fill 235 80 -6 246 80 7 minecraft:stone_bricks", "fill 240 81 1 240 84 1 minecraft:gray_concrete", "fill 242 81 1 243 84 1 minecraft:gray_concrete", "setblock 241 81 1 minecraft:gray_concrete", "fill 240 83 1 243 84 1 minecraft:gray_concrete", "fill 240 81 5 243 84 5 minecraft:gray_concrete", "setblock 241 81 3 minecraft:stone_bricks", "setblock 242 83 4 minecraft:sea_lantern", "setblock 239 82 1 minecraft:sticky_piston[facing=east]", "setblock 240 82 1 minecraft:stone_bricks", "setblock 238 82 1 minecraft:lever[face=wall,facing=west]", "tp @s 237.5 81 0.5 -90 0"],
"g08": ["fill 276 80 -4 288 80 9 minecraft:stone_bricks", "fill 279 81 1 280 82 1 minecraft:gray_concrete", "fill 283 81 1 284 82 1 minecraft:gray_concrete", "fill 282 81 4 282 83 5 minecraft:gray_concrete", "fill 283 81 6 285 83 6 minecraft:gray_concrete", "setblock 283 81 5 minecraft:stone_bricks", "tp @s 280.5 81 0.5 90 10"],
"g09": ["fill 314 80 -5 328 80 8 minecraft:stone_bricks", "fill 324 81 0 324 85 7 minecraft:gray_concrete", "fill 318 81 0 320 85 0 minecraft:gray_concrete", "fill 318 81 7 324 85 7 minecraft:gray_concrete", "fill 318 85 0 324 85 7 minecraft:stone_bricks", "setblock 323 83 5 minecraft:sea_lantern", "difficulty normal", "summon minecraft:zombie 321.5 81 2.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[180.0f,0.0f],Tags:[\"clip_g09\"]}"],
"g10": ["fill 355 80 -4 365 80 8 minecraft:stone_bricks", "fill 355 81 6 365 86 6 minecraft:gray_concrete", "tp @s 360.5 81 0.5 180 0", "gamemode survival @s"],
}
DURATIONS = {"g01":180,"g02":180,"g03":150,"g04":150,"g05":120,"g06":180,"g07":180,"g08":180,"g09":150,"g10":120}
CHUNKS = {"g01":[(-1,-1),(-1,0),(0,-1),(0,0)], "g02":[(2,-1),(2,0)], "g03":[(4,-1),(4,0),(5,-1),(5,0)], "g04":[(7,-1),(7,0),(8,-1),(8,0)], "g05":[(9,-1),(9,0),(10,-1),(10,0)], "g06":[(12,-2),(12,-1),(12,0),(13,-2),(13,-1),(13,0)], "g07":[(14,-1),(14,0),(15,-1),(15,0)], "g08":[(17,-1),(17,0),(18,-1),(18,0)], "g09":[(19,-1),(19,0),(20,-1),(20,0)], "g10":[(22,-1),(22,0)]}

def write(rel: str, lines: list[str]) -> None:
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def guard() -> list[str]:
    check = "execute unless dimension minecraft:overworld"
    box = "execute unless entity @s[x=-16,y=64,z=-32,dx=400,dy=80,dz=64]"
    return [f"{check} run tellraw @s {{\"text\":\"Studio: use the Overworld lab control area.\",\"color\":\"red\"}}", f"{check} run return 0", f"{box} run tellraw @s {{\"text\":\"Studio: stand in the reserved lab control area first.\",\"color\":\"red\"}}", f"{box} run return 0"]

def owner_guard() -> list[str]:
    return guard()+["execute unless score @s studio_owner_id = #owner studio_lock run tellraw @s {\"text\":\"Studio lock is owned by another operator; use studio:admin/release only after confirming they are offline.\",\"color\":\"red\"}", "execute unless score @s studio_owner_id = #owner studio_lock run return 0"]

def build() -> None:
    write("pack.mcmeta", [json.dumps({"pack":{"pack_format":PACK_FORMAT,"description":"WhatAmICraft isolated filming studio (Java 1.21.11)"}}, indent=2)])
    write("data/minecraft/tags/function/load.json", ['{"values":["studio:load"]}'])
    write("data/studio/function/load.mcfunction", ["scoreboard objectives add studio_scene dummy", "scoreboard objectives add studio_run dummy", "scoreboard objectives add studio_owner_id dummy", "scoreboard objectives add studio_lock dummy"])
    write("data/studio/function/help.mcfunction", ["tellraw @s {\"text\":\"Studio: claim -> scene/g01/setup ... scene/g10/setup -> start; reset; next; stop. OP only.\",\"color\":\"gold\"}", "tellraw @s {\"text\":\"Manual acting: G01,G02,G04,G06,G08,G10. Automated props: G03 fall, G05 single dispenser pulse, G07 piston, G09 staged zombie. Replay Mod is client-only.\",\"color\":\"gray\"}"])
    write("data/studio/function/claim.mcfunction", guard()+["execute if score #owner studio_lock matches 1.. run tellraw @s {\"text\":\"Studio is locked, including when its owner is offline.\",\"color\":\"red\"}", "execute if score #owner studio_lock matches 1.. run return 0", "scoreboard players add #serial studio_lock 1", "scoreboard players operation #owner studio_lock = #serial studio_lock", "scoreboard players operation @s studio_owner_id = #owner studio_lock", "tag @s add studio_owner", "tellraw @s {\"text\":\"Studio claimed. Choose a setup.\",\"color\":\"green\"}"])
    write("data/studio/function/admin/release.mcfunction", ["function studio:stop_schedules", "function studio:unload_active", "scoreboard players set #owner studio_lock 0", "scoreboard players set #scene studio_scene 0", "tag @a[tag=studio_owner] remove studio_owner", "tellraw @s {\"text\":\"Studio lock released. Use only after confirming the previous owner is offline.\",\"color\":\"yellow\"}"])
    unload = []
    for i, scene in enumerate(SETS, 1):
        for n, (cx, cz) in enumerate(CHUNKS[scene]):
            key = f"#studio_{scene}_{n}"
            unload.append(f"execute if score #scene studio_scene matches {i} if score {key} studio_lock matches 0 run forceload remove {cx * 16} {cz * 16}")
    write("data/studio/function/unload_active.mcfunction", unload)
    for index, (scene, commands) in enumerate(SETS.items(), 1):
        force = []
        for n, (cx, cz) in enumerate(CHUNKS[scene]):
            key = f"#studio_{scene}_{n}"
            force += [f"execute in minecraft:overworld store success score {key} studio_lock run forceload query {cx * 16} {cz * 16}", f"execute in minecraft:overworld if score {key} studio_lock matches 0 run forceload add {cx * 16} {cz * 16}"]
        setup = owner_guard()+["function studio:reset", "function studio:unload_active", f"scoreboard players set @s studio_scene {index}", f"scoreboard players set #scene studio_scene {index}", "scoreboard players set @s studio_run 0"] + force + [f"schedule function studio:scene/{scene}/setup_apply 2t replace", f"tellraw @s {{\"text\":\"{scene.upper()} loading its bounded set.\",\"color\":\"yellow\"}}"]
        write(f"data/studio/function/scene/{scene}/setup.mcfunction", setup)
        initial = [f"execute in minecraft:overworld run {c}" for c in BASE+commands]
        if scene == "g05": initial.insert(0, "execute in minecraft:overworld run kill @e[type=minecraft:arrow,x=154,y=80,z=-3,dx=13,dy=6,dz=8]")
        if scene == "g07": initial.insert(0, "execute in minecraft:overworld run fill 238 82 1 241 82 1 minecraft:air")
        if scene == "g09": initial.insert(0, "execute in minecraft:overworld run kill @e[type=minecraft:zombie,tag=clip_g09,x=314,y=80,z=-5,dx=14,dy=8,dz=13]")
        if scene == "g05": initial += ["execute in minecraft:overworld run item replace block 156 82 0 container.0 with minecraft:arrow 64"]
        if scene == "g07": initial += ["execute in minecraft:overworld run setblock 238 82 1 minecraft:lever[face=wall,facing=west,powered=true]"]
        write(f"data/studio/function/scene/{scene}/setup_apply.mcfunction", ["execute unless score #owner studio_lock matches 1.. run return 0", f"execute unless score #scene studio_scene matches {index} run return 0", "execute as @a if score @s studio_owner_id = #owner studio_lock at @s in minecraft:overworld run function studio:scene/"+scene+"/setup_apply_actor"])
        write(f"data/studio/function/scene/{scene}/setup_apply_actor.mcfunction", initial + [f"tellraw @s {{\"text\":\"{scene.upper()} ready ({DURATIONS[scene]} frames at 30 fps). Use /function studio:start.\",\"color\":\"green\"}}"])
        # Reapply the full bounded SET, so G07 geometry and G09's single tagged
        # actor are repeatable instead of merely deleting leftovers.
        write(f"data/studio/function/scene/{scene}/reset.mcfunction", ["function studio:stop_schedules"] + initial + ["tellraw @s {\"text\":\"Studio scene reset to its initial state.\",\"color\":\"yellow\"}"])
    write("data/studio/function/stop_schedules.mcfunction", [f"schedule clear studio:scene/{scene}/setup_apply" for scene in SETS] + ["schedule clear studio:g03/fall", "schedule clear studio:g05/pulse", "schedule clear studio:g05/unpower", "schedule clear studio:g07/open"])
    write("data/studio/function/start.mcfunction", owner_guard()+["execute unless score @s studio_scene = #scene studio_scene run return 0", "scoreboard players set @s studio_run 1"] + [f"execute if score @s studio_scene matches {i} run return run function studio:scene/{s}/start" for i,s in enumerate(SETS,1)])
    for scene in SETS:
        lines=owner_guard()+[f"execute unless score @s studio_scene matches {list(SETS).index(scene)+1} run return 0", f"tellraw @s {{\"text\":\"{scene.upper()} started.\",\"color\":\"aqua\"}}"]
        if scene == "g03": lines += ["schedule function studio:g03/fall 1t replace"]
        if scene == "g05": lines += ["schedule function studio:g05/pulse 1t replace"]
        if scene == "g07": lines += ["schedule function studio:g07/open 1t replace"]
        write(f"data/studio/function/scene/{scene}/start.mcfunction", lines)
    callback = lambda n: ["execute unless score #owner studio_lock matches 1.. run return 0", f"execute unless score #scene studio_scene matches {n} run return 0"]
    write("data/studio/function/g03/fall.mcfunction", callback(3)+["execute in minecraft:overworld run fill 80 79 0 82 79 2 minecraft:air"])
    write("data/studio/function/g05/pulse.mcfunction", callback(5)+["execute in minecraft:overworld run setblock 156 82 -1 minecraft:redstone_block", "schedule function studio:g05/unpower 2t replace"])
    write("data/studio/function/g05/unpower.mcfunction", callback(5)+["execute in minecraft:overworld run setblock 156 82 -1 minecraft:air"])
    write("data/studio/function/g07/open.mcfunction", callback(7)+["execute in minecraft:overworld run setblock 238 82 1 minecraft:lever[face=wall,facing=west,powered=false]"])
    write("data/studio/function/reset.mcfunction", owner_guard()+["execute unless score @s studio_scene = #scene studio_scene run return 0"]+[f"execute if score @s studio_scene matches {i} run return run function studio:scene/{s}/reset" for i,s in enumerate(SETS,1)])
    write("data/studio/function/stop.mcfunction", owner_guard()+["function studio:reset", "function studio:unload_active", "tag @s remove studio_owner", "scoreboard players set #owner studio_lock 0", "scoreboard players set #scene studio_scene 0", "scoreboard players set @s studio_scene 0", "scoreboard players set @s studio_run 0", "tellraw @s {\"text\":\"Studio released; world data was not deleted.\",\"color\":\"yellow\"}"])
    next_lines=owner_guard()+["execute unless score @s studio_scene = #scene studio_scene run return 0", "scoreboard players set @s studio_run 0"]
    for i, scene in enumerate(SETS,1):
        target = list(SETS)[i % len(SETS)]
        next_lines += [f"execute if score @s studio_scene matches {i} run return run function studio:scene/{target}/setup"]
    write("data/studio/function/next.mcfunction", next_lines)

def validate() -> None:
    assert list(SETS) == [f"g{i:02}" for i in range(1, 11)]
    assert all(DURATIONS[s] in (120,150,180) for s in SETS)
    assert any("minecraft:sticky_piston[facing=east]" in c for c in SETS["g07"])
    assert "g05" in CHUNKS and len(CHUNKS["g06"]) == 6
    assert not any("half=" in c or "minecraft:arrow]" in c for xs in SETS.values() for c in xs)

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
