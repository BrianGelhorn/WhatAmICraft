import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
import landscape

spec = importlib.util.spec_from_file_location("controller", ROOT / "scene_controller.py")
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


def placed_block(commands, position):
    """Evaluate a sampled voxel after all placements, without allocating a whole world."""
    x, y, z = position
    for command in reversed(commands):
        parts = command.split()
        if parts[0] == "setblock" and tuple(map(int, parts[1:4])) == (x, y, z):
            return parts[4].split("[")[0]
        if parts[0] == "fill":
            x1, y1, z1, x2, y2, z2 = map(int, parts[1:7])
            if x1 <= x <= x2 and y1 <= y <= y2 and z1 <= z <= z2:
                return parts[7].split("[")[0]
    return None


class StudioTests(unittest.TestCase):
    def test_heightmap_is_solid_smooth_and_reproducible(self):
        half, edge = landscape.HALF, landscape.HALF - 1
        for scene in controller.SCENES:
            with self.subTest(scene=scene):
                h = {(x, z): landscape.height(scene, controller.SEED, x, z)
                     for x in range(-half, half, 2) for z in range(-half, half, 2)}
                self.assertGreaterEqual(max(h.values()) - min(h.values()), 12)
                for (x, z), y in h.items():
                    if x in (-half, edge) or z in (-half, edge):
                        self.assertEqual(y, 72)
                    if (x + 2, z) in h:
                        self.assertLessEqual(abs(y - h[x + 2, z]), 12)
                    if (x, z + 2) in h:
                        self.assertLessEqual(abs(y - h[x, z + 2]), 12)
                x1, z1, x2, z2 = landscape.KEEP[scene]
                self.assertTrue(all(landscape.height(scene, controller.SEED, x, z) == 80
                                    for x in range(x1, x2+1) for z in range(z1, z2+1)))
                commands = landscape.terrain_commands(scene, controller.SEED, (0, 0))
                columns = {}
                for command in commands:
                    p = command.split()
                    if p[0] == "fill" and p[2] == "-63":
                        x, z, top = int(p[1]), int(p[3]), int(p[5])
                        self.assertEqual((p[1], p[3]), (p[4], p[6]))
                        columns[x, z] = top
                self.assertEqual(len(columns), landscape.SIZE * landscape.SIZE)
                self.assertTrue(all(columns[x, z] == y - 1 for (x, z), y in h.items()))
                self.assertEqual(commands, landscape.terrain_commands(scene, controller.SEED, (0, 0)))
                self.assertNotEqual(landscape.trees(scene, 11), landscape.trees(scene, 22))
        self.assertGreaterEqual(landscape.metadata("f03", controller.SEED, (0, 0))["heightmap"]["peak"], 100)

    def test_features_match_terrain_and_runtime_checkpoints(self):
        seed = controller.SEED
        for scene in controller.SCENES:
            commands = landscape.terrain_commands(scene, seed, (0, 0)) + landscape.feature_commands(scene, seed, (0, 0))
            info = landscape.metadata(scene, seed, (0, 0))
            for name, point in info["checkpoints"].items():
                with self.subTest(scene=scene, point=name):
                    self.assertEqual(placed_block(commands, point["pos"]), point["block"])
            self.assertGreaterEqual(len(landscape.trees(scene, seed)), 40)
            for x, z in landscape.trees(scene, seed):
                y = landscape.height(scene, seed, x, z)
                self.assertEqual(placed_block(commands, (x, y+1, z)), landscape.PALETTES[scene][2])
                self.assertNotIn(placed_block(commands, (x, y, z)), (None, "minecraft:air", "minecraft:water"))
                self.assertGreaterEqual(landscape._plot_distance(scene, x, z), 10)
            for p in ((6, 81, 1), (6, 82, 1)):
                self.assertEqual(placed_block(commands, p), "minecraft:air")

    def test_river_is_contained_and_cane_is_irrigated(self):
        commands = landscape.terrain_commands("f04", controller.SEED, (0, 0)) + landscape.feature_commands("f04", controller.SEED, (0, 0))
        water = set(landscape._river_cells())
        for x, z in water:
            self.assertEqual(placed_block(commands, (x, 79, z)), "minecraft:dirt")
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x+dx, z+dz) not in water:
                    self.assertNotIn(placed_block(commands, (x+dx, 80, z+dz)), (None, "minecraft:air", "minecraft:water"))
        self.assertEqual(placed_block(commands, (8, 80, 2)), "minecraft:sand")
        self.assertEqual(placed_block(commands, (8, 80, 1)), "minecraft:water")
        self.assertEqual(placed_block(commands, (8, 81, 2)), "minecraft:sugar_cane")

    def test_pack_ticks_bounds_references_and_lifecycle(self):
        old = controller.OUT
        self.addCleanup(setattr, controller, "OUT", old)
        with tempfile.TemporaryDirectory() as temp:
            controller.OUT = Path(temp) / "studio"
            controller.build()
            functions = controller.OUT / "data/studio/function"
            manifest = json.loads((controller.OUT / "manifest.json").read_text())
            self.assertEqual(manifest["seed"], controller.SEED)
            self.assertEqual(set(manifest["scenes"]), set(controller.SCENES))
            self.assertFalse((functions / "failed.mcfunction").exists())
            schedules = (functions / "stop_schedules.mcfunction").read_text()
            for scene, info in manifest["scenes"].items():
                self.assertLessEqual(info["chunk_count"], 169)
                self.assertGreater(info["tick_count"], 0)
                scene_dir = functions / f"scene/{scene}"
                self.assertFalse((scene_dir / "batch").exists())
                for gone in ("wait", "begin", "verify", "finish", "view", "build"):
                    self.assertFalse((scene_dir / f"{gone}.mcfunction").exists(), gone)
                for name in ("setup", "build0", "build1", "build2", "start", "reset"):
                    self.assertTrue((scene_dir / f"{name}.mcfunction").exists(), name)
                self.assertIn(f"schedule clear studio:scene/{scene}/build0", schedules)
                self.assertIn(f"schedule clear studio:scene/{scene}/build1", schedules)
                self.assertIn(f"schedule clear studio:scene/{scene}/build2", schedules)
                part0 = (scene_dir / "build0.mcfunction").read_text()
                part1 = (scene_dir / "build1.mcfunction").read_text()
                part2 = (scene_dir / "build2.mcfunction").read_text()
                for part in (part0, part1, part2):
                    self.assertLessEqual(len(part.splitlines()), 32000)
                ticks = {}
                for line in (part0 + "\n" + part1 + "\n" + part2).splitlines():
                    match = re.match(r"execute if score #cursor studio_ready matches (\d+) in minecraft:overworld run (\w+) (.*)", line)
                    if match:
                        ticks.setdefault(int(match.group(1)), []).append((match.group(2), match.group(3)))
                self.assertEqual(sorted(ticks), list(range(info["tick_count"])))
                expected = [(c.split()[0], " ".join(c.split()[1:])) for c in
                            landscape.terrain_commands(scene, controller.SEED, controller.origins()[scene]) +
                            landscape.feature_commands(scene, controller.SEED, controller.origins()[scene])]
                self.assertEqual(sorted(map(str, [c for group in ticks.values() for c in group])), sorted(map(str, expected)))
                for tick, group in ticks.items():
                    volume, count = 0, 0
                    for verb, rest in group:
                        parts = rest.split()
                        if verb == "fill":
                            x1, y1, z1, x2, y2, z2 = map(int, parts[:6])
                        elif verb == "summon":
                            x1, y1, z1 = map(int, parts[1:4])
                            x2, y2, z2 = x1, y1, z1
                        else:
                            x1, y1, z1 = map(int, parts[:3])
                            x2, y2, z2 = x1, y1, z1
                        bx1, bz1, bx2, bz2 = info["bounds"]
                        self.assertTrue(bx1 <= x1 <= x2 <= bx2 and bz1 <= z1 <= z2 <= bz2)
                        self.assertTrue(-63 <= y1 <= y2 <= 143)
                        cost = (x2-x1+1) * (y2-y1+1) * (z2-z1+1)
                        self.assertLessEqual(cost, 32768)
                        volume += cost
                        count += 1
                    self.assertLessEqual(volume, 32768)
                    self.assertLessEqual(count, 200)
                setup = (scene_dir / "setup.mcfunction").read_text()
                self.assertIn("function studio:stop_schedules", setup)
                self.assertIn("store success score #had_", setup)
                self.assertIn("store success score #force_", setup)
                self.assertIn("scoreboard players set #cursor studio_ready -1", setup)
                self.assertIn(f"schedule function studio:scene/{scene}/build0 1t replace", setup)
                self.assertIn("studio_scene " + str(controller.SCENES.index(scene)+1), setup)
                if scene == "f02":
                    self.assertIn("kill @e[type=minecraft:armor_stand,tag=studio_dummy", setup)
                self.assertIn("scoreboard players set #ready studio_ready 1", part2)
                self.assertIn("scoreboard players set #ready studio_ready -1", part2)
                self.assertIn(f"execute if score #ready studio_ready matches 0 run schedule function studio:scene/{scene}/build2 1t replace", part2)
                self.assertIn(f"schedule function studio:scene/{scene}/build1 1t replace", part0)
                self.assertIn(f"schedule function studio:scene/{scene}/build2 1t replace", part1)
                self.assertIn("studio:scene/" + scene + "/setup", (scene_dir / "reset.mcfunction").read_text())
            alltext = "\n".join(p.read_text() for p in functions.rglob("*.mcfunction"))
            for reference in re.findall(r"(?:function|schedule clear) studio:([\w/]+)", alltext):
                self.assertTrue((functions / (reference + ".mcfunction")).exists(), reference)
            self.assertNotIn("clear @s", alltext)
            self.assertNotIn("tp @a", alltext)
            self.assertIn("if loaded", alltext)
            self.assertEqual((functions / "next.mcfunction").read_text().count("run return run function studio:scene/"), 3)
            self.assertNotIn("studio:reset", (functions / "stop.mcfunction").read_text())
            self.assertIn("with storage studio:runtime loads[0]", (functions / "release_added.mcfunction").read_text())
            self.assertIn("$(x) $(z)", (functions / "release_one.mcfunction").read_text())
            self.assertIn("data modify storage studio:runtime loads append value", alltext)
            self.assertIn("unless score @s studio_owner_id = #owner studio_ready", alltext)
            start = (functions / "scene/f02/start.mcfunction").read_text()
            self.assertLess(start.index("tp @s"), start.index("gamemode survival @s"))
            oldfile = functions / "obsolete.mcfunction"
            oldfile.write_text("say obsolete")
            controller.build()
            self.assertFalse(oldfile.exists())

    def test_translation_nonoverlap_and_invalid_parameters(self):
        old_origin, old_pitch = controller.ORIGIN[:], controller.PITCH
        self.addCleanup(setattr, controller, "ORIGIN", old_origin)
        self.addCleanup(setattr, controller, "PITCH", old_pitch)
        controller.ORIGIN[:] = [-333, -77]
        controller.PITCH = 200
        controller.validate()
        origins = controller.origins()
        self.assertEqual(origins["f02"], (-333, -77))
        bounds = [landscape.metadata(s, 1, origin)["bounds"] for s, origin in origins.items()]
        self.assertTrue(all(a[2] < b[0] for a, b in zip(bounds, bounds[1:])))
        commands = landscape.terrain_commands("f02", 1, (-333, -77))
        self.assertIn("fill -333 -63 -77 -333 79 -77 minecraft:dirt", commands)
        controller.PITCH = 95
        with self.assertRaises(ValueError):
            controller.validate()

    def test_docker_keeps_local_isolation_and_real_version(self):
        compose = (ROOT / "docker-compose.yaml").read_text()
        for value in ('VERSION: "1.21.11"', 'ENABLE_RCON: "FALSE"', "127.0.0.1:25565:25565", "./data:/data"):
            self.assertIn(value, compose)
        self.assertNotIn("../data", compose)
        self.assertIn("!landscape.py", (ROOT / ".dockerignore").read_text())
        self.assertIn("landscape.py", (ROOT / "Dockerfile").read_text())


if __name__ == "__main__":
    unittest.main()
