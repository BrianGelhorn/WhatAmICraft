#!/usr/bin/env python3
"""Compile deterministic landscapes into a bounded Java 1.21.11 datapack."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import landscape
import asset_importer

ROOT = Path(__file__).parent
OUT = ROOT / "generated" / "studio"
PACK_FORMAT = 81
ORIGIN = [120, 14]
PITCH = 1152
SEED = 20260915
CONTENT_REVISION = "scene-assets-1"
SCENES = ("f02", "f03", "f04", "f08", "f09", "f10", "f11")
KITS = {
    "f02": ["minecraft:mace", "minecraft:trident"],
    "f03": ["minecraft:sea_lantern", "minecraft:soul_lantern"],
    "f04": ["minecraft:nether_wart", "minecraft:sugar_cane"],
    "f08": ["minecraft:amethyst_block", "minecraft:calcite"],
    "f09": ["minecraft:goat_horn", "minecraft:recovery_compass"],
    "f10": ["minecraft:kelp", "minecraft:glow_berries"],
    "f11": [],
}
BRIEFS = {
    "f02": "Ataca al dummy en la arena despejada. Reset repone el dummy; no certifica mecanicas.",
    "f03": "Entra al santuario oscuro y coloca una luz real en cada pedestal. Reset retira la anterior.",
    "f04": "Planta wart en arena de almas y cana en la arena junto al canal de agua; son sustratos distintos.",
    "f08": "Colocá amethyst y calcita reales en sus pedestales y comparalos. Reset repone la muestra.",
    "f09": "Sostené y usá cuerno y brújula mostrando el HUD sin barra de durabilidad.",
    "f10": "Plantá kelp en la arena bajo el agua y mostrá las bayas en mano. Reset restaura la pileta.",
    "f11": "Recorré el bosque fúngico y compará las variantes colocadas. Los assets vienen del catálogo del bundle.",
}
CONTEXTS = {
    # spawn_mobs and advance_time are the Java 1.21.11 namespaced snake-case IDs.
    "f02": {"atmosphere": "crepusculo de batalla", "composition": "ruinas y barricadas alrededor de arena libre", "action": "ataque real al dummy", "time": 14000, "weather": "unchanged", "difficulty": "unchanged", "gamerules": {"minecraft:advance_time": False, "minecraft:spawn_mobs": False}, "risks": "sin mobs, fuego, TNT ni perdida forzada"},
    "f03": {"atmosphere": "noche sobria para prueba de luz", "composition": "santuario cubierto, baffle y pedestales oscuros", "action": "colocar luz real y comparar", "time": 18000, "weather": "unchanged", "difficulty": "unchanged", "gamerules": {"minecraft:advance_time": False, "minecraft:spawn_mobs": False}, "risks": "sin decoracion emisiva; requiere ensayo visual"},
    "f04": {"atmosphere": "dia calmo de cultivo", "composition": "ribera, parcela y canal", "action": "cultivo con sustratos separados", "time": 1000, "weather": "unchanged", "difficulty": "unchanged", "gamerules": {"minecraft:advance_time": False, "minecraft:spawn_mobs": False}, "risks": "wart y cana no comparten sustrato natural"},
    "f08": {"atmosphere": "mediodía neutro de cantera", "composition": "pedestales de muestra sobre piedra", "action": "comparar bloques reales en pedestales", "time": 6000, "weather": "unchanged", "difficulty": "unchanged", "gamerules": {"minecraft:advance_time": False, "minecraft:spawn_mobs": False}, "risks": "sin mena identificable en el fondo; requiere ensayo visual"},
    "f09": {"atmosphere": "atardecer de uso en mano", "composition": "senda de pradera sin estructuras", "action": "sostener y usar items mostrando HUD", "time": 14000, "weather": "unchanged", "difficulty": "unchanged", "gamerules": {"minecraft:advance_time": False, "minecraft:spawn_mobs": False}, "risks": "HUD sin barra a la vista; inventario limpio"},
    "f10": {"atmosphere": "mañana húmeda de ribera", "composition": "pileta contenida con arena", "action": "plantar kelp bajo agua y mostrar bayas", "time": 1000, "weather": "unchanged", "difficulty": "unchanged", "gamerules": {"minecraft:advance_time": False, "minecraft:spawn_mobs": False}, "risks": "bayas en mano, no enredadera; agua contenida"},
    "f11": {"atmosphere": "bosque húmedo al amanecer", "composition": "claro de podzol con hongos variados", "action": "comparar formas y escalas de los assets", "time": 1000, "weather": "unchanged", "difficulty": "unchanged", "gamerules": {"minecraft:advance_time": False, "minecraft:spawn_mobs": False}, "risks": "escena experimental; assets externos convertidos al build"},
}


def origins():
    return {s: (ORIGIN[0] + i * PITCH, ORIGIN[1]) for i, s in enumerate(SCENES)}


def chunks(scene):
    ox, oz = origins()[scene]
    half = landscape.HALF
    return [(x, z) for x in range((ox - half) // 16, (ox + half - 1) // 16 + 1)
            for z in range((oz - half) // 16, (oz + half - 1) // 16 + 1)]


def write(rel, lines):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def schedule_ticks(commands, max_volume=32768, max_count=200):
    """Number each command with the tick that may run it.

    Returns (ticks, total): tick number -> commands, and the first free tick.
    One guarded build file runs a single tick per game tick, so a scene needs
    only setup/start/reset instead of hundreds of batch files.
    """
    ticks, tick, volume, count = {}, 0, 0, 0
    for command in commands:
        words = command.split()
        cost = 1
        if words[0] == "fill":
            x1, y1, z1, x2, y2, z2 = map(int, words[1:7])
            cost = (x2 - x1 + 1) * (y2 - y1 + 1) * (z2 - z1 + 1)
            if not 0 < cost <= max_volume:
                raise ValueError(f"Invalid fill volume: {command}")
        if count >= max_count or volume + cost > max_volume:
            tick += 1
            volume, count = 0, 0
        ticks.setdefault(tick, []).append(command)
        volume += cost
        count += 1
    return ticks, tick + 1


def operator_guard():
    # The claim score persists when the owner disconnects; console can explicitly release it.
    return [
        'execute unless dimension minecraft:overworld run return 0',
        'execute if score #claimed studio_ready matches 1 unless score @s studio_owner_id = #owner studio_ready run tellraw @s {"text":"Studio ocupado. Usa el operador original o studio:admin/release.","color":"red"}',
        'execute if score #claimed studio_ready matches 1 unless score @s studio_owner_id = #owner studio_ready run return 0',
    ]


def build():
    validate()
    # Do not replace the bind-mounted root or delete anything outside our generated functions.
    functions = OUT / "data/studio/function"
    if OUT.name != "studio" or "world" in OUT.resolve().parts or functions.is_symlink():
        raise ValueError("Refusing unsafe generated output")
    if functions.exists():
        shutil.rmtree(functions)
    catalog = asset_importer.import_bundle(OUT)
    write("pack.mcmeta", [json.dumps({"pack": {"pack_format": PACK_FORMAT,
          "description": "WhatAmICraft deterministic mountain studio (Java 1.21.11)"}})])
    write("data/minecraft/tags/function/load.json", ['{"values":["studio:load"]}'])
    # Persist actual acquired coordinates: a later build can relocate the same scene IDs.
    write("data/studio/function/release_one.mcfunction", ["$execute in minecraft:overworld run forceload remove $(x) $(z)"])
    write("data/studio/function/release_added.mcfunction", [
        "execute unless data storage studio:runtime loads[0] run return 0",
        "function studio:release_one with storage studio:runtime loads[0]",
        "data remove storage studio:runtime loads[0]",
        "return run function studio:release_added",
    ])
    write("data/studio/function/load.mcfunction", [
        "scoreboard objectives add studio_scene dummy", "scoreboard objectives add studio_ready dummy",
        "scoreboard objectives add studio_force dummy", "scoreboard objectives add studio_owner_id dummy", "function studio:stop_schedules",
        "function studio:release_added", "scoreboard players set #ready studio_ready 0",
        "scoreboard players set #scene studio_scene 0", "scoreboard players set #buildkey studio_ready 0",
        'tellraw @a[tag=studio_owner] {"text":"Studio recargado; ejecuta setup. No se borro el mundo.","color":"yellow"}',
    ])
    write("data/studio/function/context/capture.mcfunction", [
        "execute if score #context_saved studio_ready matches 1 run return 0",
        "execute store result storage studio:runtime context.daytime int 1 run time query daytime",
        "execute store result score #context_advance studio_ready run gamerule minecraft:advance_time",
        "execute store result score #context_spawn studio_ready run gamerule minecraft:spawn_mobs",
        "scoreboard players set #context_saved studio_ready 1",
    ])
    write("data/studio/function/context/restore_time.mcfunction", ["$time set $(daytime)"])
    write("data/studio/function/context/restore.mcfunction", [
        "execute unless score #context_saved studio_ready matches 1 run return 0",
        "function studio:context/restore_time with storage studio:runtime context",
        "execute if score #context_advance studio_ready matches 1 run gamerule minecraft:advance_time true",
        "execute if score #context_advance studio_ready matches 0 run gamerule minecraft:advance_time false",
        "execute if score #context_spawn studio_ready matches 1 run gamerule minecraft:spawn_mobs true",
        "execute if score #context_spawn studio_ready matches 0 run gamerule minecraft:spawn_mobs false",
        "data remove storage studio:runtime context",
        "scoreboard players set #context_saved studio_ready 0",
    ])
    for scene, context in CONTEXTS.items():
        write(f"data/studio/function/context/{scene}.mcfunction", [
            "function studio:context/capture",
            f"time set {context['time']}",
            *[f"gamerule {rule} {'true' if value else 'false'}" for rule, value in context["gamerules"].items()],
        ])
    write("data/studio/function/help.mcfunction", [
        'tellraw @s {"text":"Studio: scene/f02/setup (colinas), f03/setup (santuario), f04/setup (ribera), f08/setup (cantera), f09/setup (pradera), f10/setup (pileta), f11/setup (bosque fungico). Luego start, reset, next o stop. Inventario conservado.","color":"gold"}',
        'tellraw @s {"text":"Estado: scoreboard players get #ready studio_ready. 0=cargando, 1=listo, -1=fallo. Solo se edita la caja 192x192 autorizada.","color":"gray"}',
    ])
    write("data/studio/function/claim.mcfunction", operator_guard() + [
        "execute unless entity @s[type=minecraft:player] run return 0",
        "execute unless score #claimed studio_ready matches 1 run scoreboard players add #serial studio_ready 1",
        "execute unless score #claimed studio_ready matches 1 run scoreboard players operation #owner studio_ready = #serial studio_ready",
        "scoreboard players operation @s studio_owner_id = #owner studio_ready",
        "tag @s add studio_owner", "scoreboard players set #claimed studio_ready 1",
        "scoreboard players operation @s studio_scene = #scene studio_scene",
    ])
    cleanup = ["function studio:stop_schedules", "function studio:release_added", "function studio:context/restore",
               "scoreboard players set #scene studio_scene 0", "scoreboard players set #ready studio_ready 0"]
    write("data/studio/function/stop.mcfunction", operator_guard() + cleanup + [
        "tag @s remove studio_owner", "scoreboard players set #claimed studio_ready 0",
        "scoreboard players set #buildkey studio_ready 0",
        'tellraw @s {"text":"Studio detenido. Paisaje e inventario conservados.","color":"yellow"}',
    ])
    write("data/studio/function/admin/release.mcfunction", cleanup + [
        "tag @a[tag=studio_owner] remove studio_owner", "scoreboard players set #claimed studio_ready 0",
        "scoreboard players set #buildkey studio_ready 0",
        'tellraw @a {"text":"Operador de studio liberado por administrador.","color":"yellow"}',
    ])
    manifest = {"seed": SEED, "version": "1.21.11", "origins": origins(), "scenes": {}}
    schedules = []
    for index, scene in enumerate(SCENES, 1):
        ox, oz = origins()[scene]
        commands = landscape.terrain_commands(scene, SEED, (ox, oz)) + landscape.feature_commands(scene, SEED, (ox, oz))
        asset_commands, asset_info = asset_importer.placement_commands(scene, SEED, (ox, oz), catalog, landscape.height, OUT / asset_importer.STRUCTURE_DIR)
        commands += asset_commands
        ticks, total = schedule_ticks(commands)
        info = landscape.metadata(scene, SEED, (ox, oz))
        if asset_info:
            info["assets"] = asset_info["assets"]
            info["asset_placement"] = asset_info["placement"]
            info["asset_source"] = asset_importer.find_source().name if asset_importer.find_source() else None
            info["checkpoints"]["asset_marker"] = {"block": asset_info["block"], "pos": asset_info["pos"]}
        info.update(tick_count=total, command_count=len(commands), write_y=[-63, 131], chunk_count=len(chunks(scene)), context=CONTEXTS[scene], content_revision=CONTENT_REVISION)
        manifest["scenes"][scene] = info
        prefix = f"data/studio/function/scene/{scene}/"
        if asset_info:
            write(prefix + "assets.mcfunction", operator_guard() + asset_commands)
        schedules.append(f"schedule clear studio:scene/{scene}/build0")
        schedules.append(f"schedule clear studio:scene/{scene}/build1")
        schedules.append(f"schedule clear studio:scene/{scene}/build2")
        force = []
        for n, (cx, cz) in enumerate(chunks(scene)):
            force += [f"scoreboard players set #force_{scene}_{n} studio_force 0",
                      f"execute in minecraft:overworld store success score #had_{scene}_{n} studio_force run forceload query {cx * 16} {cz * 16}",
                      f"execute if score #had_{scene}_{n} studio_force matches 0 in minecraft:overworld store success score #force_{scene}_{n} studio_force run forceload add {cx * 16} {cz * 16}",
                      f"execute if score #force_{scene}_{n} studio_force matches 1 run data modify storage studio:runtime loads append value {{x:{cx * 16},z:{cz * 16}}}",
                      f"execute if score #had_{scene}_{n} studio_force matches 0 unless score #force_{scene}_{n} studio_force matches 1 run scoreboard players set #force_failed studio_ready 1"]
        write(prefix + "setup.mcfunction", operator_guard() + [
            "function studio:stop_schedules", "function studio:release_added",
            "data remove storage studio:runtime built",
            "data modify storage studio:runtime loads set value []",
            "tag @a[tag=studio_owner] remove studio_owner",
            f"scoreboard players set #scene studio_scene {index}",
            "function studio:claim",
            f"function studio:context/{scene}",
            "execute if entity @s[type=minecraft:player] run gamemode creative @s",
            f"execute if entity @s[type=minecraft:player] run tp @s {ox + 6} 145 {oz - 15} 0 65",
            "scoreboard players set #buildkey studio_ready 1",
            "scoreboard players set #ready studio_ready 0", "scoreboard players set #wait studio_ready 0",
            "scoreboard players set #force_failed studio_ready 0",
            "scoreboard players set #cursor studio_ready -1",
            "scoreboard players set #soft studio_ready 0",
            f'tellraw @s {{"text":"Construyendo {scene.upper()}: relieve, estructura y vegetacion, semilla {SEED}. Espera el aviso listo.","color":"yellow"}}',
        ] + force + [
            "execute if score #force_failed studio_ready matches 1 run scoreboard players set #ready studio_ready -1",
            "execute if score #force_failed studio_ready matches 1 run function studio:context/restore",
            "execute if score #force_failed studio_ready matches 1 run function studio:release_added",
            "execute if score #force_failed studio_ready matches 1 run scoreboard players set #buildkey studio_ready 0",
            "execute if score #force_failed studio_ready matches 1 run tellraw @a[tag=studio_owner] {\"text\":\"Studio fallo: forceload rechazado. Revisa logs y repeti setup.\",\"color\":\"red\"}",
            "execute if score #force_failed studio_ready matches 1 run return 0",
            f"schedule function studio:scene/{scene}/build0 1t replace",
        ])
        nchunks = len(chunks(scene))
        # Three chained parts: one pass evaluates every line of its file, and
        # each guarded `execute` costs several chain slots, so the ~80k lines
        # of a scene are split until every part stays under ~30k evaluated
        # lines (proven live against the engine's 65k chain cap).
        ordered = sorted(ticks.items())
        sizes = [(tick, len(group) + (1 if tick and tick % 25 == 0 else 0)) for tick, group in ordered]
        third = sum(n for _, n in sizes) / 3
        splits, acc = [], 0
        for tick, n in sizes:
            acc += n
            if len(splits) < 2 and acc >= third * (len(splits) + 1) and total - (tick + 1) >= 2 - len(splits):
                splits.append(tick + 1)
        while len(splits) < 2:
            splits.append(total - (2 - len(splits)))
        s1, s2 = splits
        if not 0 < s1 < s2 < total:
            raise ValueError(f"Cannot split {scene} into three safe parts")

        def slices(lo, hi):
            lines = []
            for tick, group in ordered:
                if not lo <= tick < hi:
                    continue
                for command in group:
                    lines.append(f"execute if score #cursor studio_ready matches {tick} in minecraft:overworld run {command}")
                if tick and tick % 25 == 0:
                    lines.append(f"execute if score #cursor studio_ready matches {tick} run tellraw @a[tag=studio_owner] {{\"text\":\"{scene.upper()}: {tick * 100 // total}%\",\"color\":\"gray\"}}")
            return lines

        def advance(name, hi, nxt):
            return [
                f"execute unless score #cursor studio_ready matches {hi}.. run scoreboard players add #cursor studio_ready 1",
                f"execute if score #cursor studio_ready matches {hi}.. if score #ready studio_ready matches 0 run schedule function studio:scene/{scene}/{nxt} 1t replace",
                f"execute if score #ready studio_ready matches 0 unless score #cursor studio_ready matches {hi}.. run schedule function studio:scene/{scene}/{name} 1t replace",
            ]

        info.update(splits=[s1, s2])
        nterrain = len(landscape.terrain_commands(scene, SEED, (ox, oz)))
        seen, soft_tick = 0, 0
        for tick in sorted(ticks):
            if seen + len(ticks[tick]) > nterrain:
                soft_tick = tick
                break
            seen += len(ticks[tick])
        info.update(soft_tick=soft_tick)
        part0 = ["execute unless score #buildkey studio_ready matches 1 run return 0",
                 f"execute unless score #scene studio_scene matches {index} run return 0",
                 "execute if score #cursor studio_ready matches -1 run scoreboard players set #loaded studio_ready 0"]
        part0 += [f"execute if score #cursor studio_ready matches -1 in minecraft:overworld if loaded {cx * 16 + 8} 80 {cz * 16 + 8} run scoreboard players add #loaded studio_ready 1" for cx, cz in chunks(scene)]
        if scene == "f02":
            part0.append(f"execute if score #cursor studio_ready matches -1 if score #loaded studio_ready matches {nchunks} in minecraft:overworld run kill @e[type=minecraft:armor_stand,tag=studio_dummy,x={ox-96},y=73,z={oz-96},dx=191,dy=58,dz=191]")
        part0 += [
            f"execute if score #cursor studio_ready matches -1 if score #loaded studio_ready matches {nchunks} run scoreboard players operation #cursor studio_ready = #soft studio_ready",
            "execute if score #cursor studio_ready matches -1 run scoreboard players add #wait studio_ready 1",
            "execute if score #cursor studio_ready matches -1 if score #wait studio_ready matches 60.. run scoreboard players set #ready studio_ready -1",
            "execute if score #cursor studio_ready matches -1 if score #wait studio_ready matches 60.. run scoreboard players set #buildkey studio_ready 0",
            "execute if score #cursor studio_ready matches -1 if score #wait studio_ready matches 60.. run function studio:context/restore",
            "execute if score #cursor studio_ready matches -1 if score #wait studio_ready matches 60.. run function studio:release_added",
            f"execute if score #cursor studio_ready matches -1 if score #wait studio_ready matches 60.. run tellraw @a[tag=studio_owner] {{\"text\":\"{scene.upper()} fallo: chunks sin cargar. Revisa logs y repeti setup.\",\"color\":\"red\"}}",
            "execute if score #cursor studio_ready matches -1 if score #wait studio_ready matches 60.. run return 0",
            f"execute if score #cursor studio_ready matches -1 run schedule function studio:scene/{scene}/build0 10t replace",
            "execute if score #cursor studio_ready matches -1 run return 0",
        ]
        part0 += slices(0, s1) + advance("build0", s1, "build1")
        write(prefix + "build0.mcfunction", part0)
        part1 = ["execute unless score #buildkey studio_ready matches 1 run return 0",
                 f"execute unless score #scene studio_scene matches {index} run return 0"]
        part1 += slices(s1, s2) + advance("build1", s2, "build2")
        write(prefix + "build1.mcfunction", part1)
        part2 = ["execute unless score #buildkey studio_ready matches 1 run return 0",
                 f"execute unless score #scene studio_scene matches {index} run return 0"]
        part2 += slices(s2, total)
        nchecks = len(info["checkpoints"])
        part2.append(f"execute unless score #cursor studio_ready matches {total}.. run scoreboard players add #cursor studio_ready 1")
        part2.append(f"execute if score #cursor studio_ready matches {total}.. run scoreboard players set #checks studio_ready 0")
        for point in info["checkpoints"].values():
            x, y, z = point["pos"]
            part2.append(f"execute if score #cursor studio_ready matches {total}.. in minecraft:overworld if block {x} {y} {z} {point['block']} run scoreboard players add #checks studio_ready 1")
        part2 += [
            f"execute if score #cursor studio_ready matches {total}.. unless score #checks studio_ready matches {nchecks} run scoreboard players set #ready studio_ready -1",
            f"execute if score #cursor studio_ready matches {total}.. unless score #checks studio_ready matches {nchecks} run function studio:context/restore",
            f"execute if score #cursor studio_ready matches {total}.. unless score #checks studio_ready matches {nchecks} run function studio:release_added",
            f"execute if score #cursor studio_ready matches {total}.. unless score #checks studio_ready matches {nchecks} run tellraw @a[tag=studio_owner] {{\"text\":\"{scene.upper()} fallo: verificacion. Revisa logs y repeti setup.\",\"color\":\"red\"}}",
            f"execute if score #cursor studio_ready matches {total}.. if score #checks studio_ready matches {nchecks} run scoreboard players set #ready studio_ready 1",
            f"execute if score #cursor studio_ready matches {total}.. if score #checks studio_ready matches {nchecks} run data modify storage studio:runtime built set value {{seed:{SEED},ox:{ox},oz:{oz},pitch:{PITCH},scene:\"{scene}\",revision:\"{CONTENT_REVISION}\"}}",
            f"execute if score #cursor studio_ready matches {total}.. if score #checks studio_ready matches {nchecks} as @a[tag=studio_owner] if score @s studio_owner_id = #owner studio_ready in minecraft:overworld run tp @s {ox + 6.5} 81 {oz + 1.5} 0 0",
            f"execute if score #cursor studio_ready matches {total}.. if score #checks studio_ready matches {nchecks} run tellraw @a[tag=studio_owner] {{\"text\":\"{scene.upper()} listo. Usa studio:start.\",\"color\":\"green\"}}",
            "execute unless score #ready studio_ready matches 0 run scoreboard players set #buildkey studio_ready 0",
            f"execute if score #ready studio_ready matches 0 run schedule function studio:scene/{scene}/build2 1t replace",
        ]
        for part in (part0, part1, part2):
            if len(part) > 32000:
                raise ValueError(f"{scene} part exceeds safe evaluated lines per pass")
        write(prefix + "build2.mcfunction", part2)
        write(prefix + "start.mcfunction", operator_guard() + [
            f"execute unless score #scene studio_scene matches {index} run return 0",
            "execute unless score #ready studio_ready matches 1 run return 0",
            "function studio:claim",
            f"function studio:context/{scene}",
            f"tp @s {ox + 6.5} 81 {oz + 1.5} 0 0",
        ] + (["gamemode survival @s"] if scene == "f02" else ["gamemode creative @s"]) +
            [f"give @s {item} 1" for item in KITS[scene]] +
            [f'tellraw @s {{"text":"{BRIEFS[scene]} Inventario conservado.","color":"aqua"}}'])
        write(prefix + "reset.mcfunction", operator_guard() + [
            f"execute unless score #scene studio_scene matches {index} run return run function studio:scene/{scene}/setup",
            "scoreboard players set #buildkey studio_ready 1",
            f"execute if data storage studio:runtime {{built:{{seed:{SEED},ox:{ox},oz:{oz},pitch:{PITCH},scene:\"{scene}\",revision:\"{CONTENT_REVISION}\"}}}} run return run function studio:scene/{scene}/soft",
            f"return run function studio:scene/{scene}/setup",
        ])
        soft = ["execute unless score #buildkey studio_ready matches 1 run return 0",
                f"execute unless score #scene studio_scene matches {index} run return 0",
                "function studio:stop_schedules", "function studio:release_added",
                "data remove storage studio:runtime built",
                "data modify storage studio:runtime loads set value []",
                "scoreboard players set #force_failed studio_ready 0",
                f"function studio:context/{scene}"]
        soft += force + [
            "execute if score #force_failed studio_ready matches 1 run scoreboard players set #ready studio_ready -1",
            "execute if score #force_failed studio_ready matches 1 run scoreboard players set #buildkey studio_ready 0",
            "execute if score #force_failed studio_ready matches 1 run function studio:context/restore",
            "execute if score #force_failed studio_ready matches 1 run function studio:release_added",
            "execute if score #force_failed studio_ready matches 1 run tellraw @a[tag=studio_owner] {\"text\":\"Studio fallo: forceload rechazado. Revisa logs y repeti setup.\",\"color\":\"red\"}",
            "execute if score #force_failed studio_ready matches 1 run return 0",
            f"scoreboard players set #soft studio_ready {soft_tick}",
            "scoreboard players set #cursor studio_ready -1",
            "scoreboard players set #ready studio_ready 0",
            "scoreboard players set #wait studio_ready 0",
            f"schedule function studio:scene/{scene}/build0 1t replace",
        ]
        write(prefix + "soft.mcfunction", soft)
    manifest["asset_catalog_count"] = len(catalog)
    write("manifest.json", [json.dumps(manifest, indent=2, sort_keys=True)])
    write("data/studio/function/stop_schedules.mcfunction", schedules)
    for action in ("start", "reset", "next"):
        lines = operator_guard()
        for i, scene in enumerate(SCENES, 1):
            target = f"{SCENES[i % len(SCENES)]}/setup" if action == "next" else f"{scene}/{action}"
            lines.append(f"execute if score #scene studio_scene matches {i} run return run function studio:scene/{target}")
        write(f"data/studio/function/{action}.mcfunction", lines + ["return 0"])


def validate():
    if PITCH < landscape.SIZE or len(ORIGIN) != 2:
        raise ValueError("Pitch must cover the landscape size; origin requires X Z")
    for scene, (ox, oz) in origins().items():
        if max(abs(ox), abs(oz)) + landscape.HALF >= 29999984 or len(chunks(scene)) > 256:
            raise ValueError("Scene exceeds world or chunk loading bounds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "validate"), nargs="?", default="build")
    parser.add_argument("--origin", nargs=2, type=int, default=ORIGIN, help="Action terrace origin X Z")
    parser.add_argument("--pitch", type=int, default=PITCH, help="Scene spacing (minimum 192)")
    parser.add_argument("--seed", type=int, default=SEED, help="Deterministic terrain and vegetation seed")
    args = parser.parse_args()
    ORIGIN[:] = args.origin
    PITCH, SEED = args.pitch, args.seed
    validate()
    if args.command == "build":
        build()
        print(f"Built {OUT}")
    else:
        print("Scene source is valid")
