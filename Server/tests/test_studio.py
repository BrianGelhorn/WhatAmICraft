import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("controller", ROOT / "scene_controller.py")
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)

class StudioTests(unittest.TestCase):
    def test_source_and_generated_pack(self):
        controller.validate()
        self.assertEqual(controller.PACK_FORMAT, 81)
        old = controller.OUT
        with tempfile.TemporaryDirectory() as temp:
            controller.OUT = Path(temp) / "studio"
            controller.build()
            functions = controller.OUT / "data/studio/function"
            for n in range(11, 14):
                self.assertTrue((functions / f"scene/g{n:02}/setup.mcfunction").exists())
                self.assertTrue((functions / f"scene/g{n:02}/reset.mcfunction").exists())
            for n in range(2, 5):
                self.assertTrue((functions / f"scene/f{n:02}/setup.mcfunction").exists())
                self.assertTrue((functions / f"scene/f{n:02}/reset.mcfunction").exists())
            self.assertIn("minecraft:ladder[facing=west]", (functions / "scene/g11/setup_apply_actor.mcfunction").read_text())
            self.assertIn("minecraft:oak_planks", (functions / "scene/g12/setup_apply_actor.mcfunction").read_text())
            self.assertIn("minecraft:sea_lantern", (functions / "scene/g13/setup_apply_actor.mcfunction").read_text())
            self.assertIn("minecraft:quartz_block", (functions / "scene/f02/setup_apply_actor.mcfunction").read_text())
            self.assertIn("summon minecraft:armor_stand", (functions / "scene/f02/setup_apply_actor.mcfunction").read_text())
            self.assertIn("kill @e[type=minecraft:armor_stand", (functions / "scene/f02/reset.mcfunction").read_text())
            self.assertIn("give @s minecraft:mace", (functions / "scene/f02/start.mcfunction").read_text())
            self.assertIn("gamemode survival @s", (functions / "scene/f02/start.mcfunction").read_text())
            self.assertIn("give @s minecraft:sea_lantern", (functions / "scene/f03/start.mcfunction").read_text())
            self.assertIn("give @s minecraft:nether_wart", (functions / "scene/f04/start.mcfunction").read_text())
            self.assertIn("gamemode creative @s", (functions / "stop.mcfunction").read_text())
            self.assertIn("168 81 14", (functions / "scene/f03/setup_apply_actor.mcfunction").read_text())
            self.assertIn("minecraft:soul_sand", (functions / "scene/f04/setup_apply_actor.mcfunction").read_text())
            self.assertIn("Action is manual", (functions / "scene/g11/start.mcfunction").read_text())
            self.assertNotIn("schedule function studio:", (functions / "scene/g12/start.mcfunction").read_text())
            self.assertIn("schedule clear studio:scene/g13/setup_apply", (functions / "stop_schedules.mcfunction").read_text())
            self.assertIn("execute as @a if score @s studio_owner_id = #owner studio_lock", (functions / "scene/g11/setup_apply.mcfunction").read_text())
            self.assertIn("scoreboard players operation #owner studio_lock", (functions / "claim.mcfunction").read_text())
            self.assertIn("scoreboard players set #owner studio_lock 0", (functions / "admin/release.mcfunction").read_text())
            self.assertIn("Studio scene reset to its initial state", (functions / "scene/g11/reset.mcfunction").read_text())
            next_scene = (functions / "next.mcfunction").read_text()
            self.assertEqual(next_scene.count("run function studio:scene/"), 6)
            self.assertNotIn("return run function", next_scene)
            self.assertIn("return 1", next_scene)
            start_scene = (functions / "start.mcfunction").read_text()
            self.assertNotIn("return run function", start_scene)
            self.assertIn("return 1", start_scene)
        controller.OUT = old

    def test_docker_is_isolated_and_no_rcon_listener(self):
        compose = (ROOT / "docker-compose.yaml").read_text()
        self.assertIn('TYPE: "FABRIC"', compose)
        self.assertIn('VERSION: "1.21.11"', compose)
        self.assertIn("127.0.0.1:25565:25565", compose)
        self.assertIn('ENABLE_RCON: "FALSE"', compose)
        self.assertNotIn("../data", compose)
        self.assertIn("./data:/data", compose)
