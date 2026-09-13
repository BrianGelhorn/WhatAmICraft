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
            for n in range(1, 11):
                self.assertTrue((functions / f"scene/g{n:02}/setup.mcfunction").exists())
                self.assertTrue((functions / f"scene/g{n:02}/reset.mcfunction").exists())
            self.assertIn("sticky_piston[facing=east]", (functions / "scene/g07/setup_apply_actor.mcfunction").read_text())
            self.assertIn("schedule function studio:g05/pulse 1t replace", (functions / "scene/g05/start.mcfunction").read_text())
            self.assertIn("schedule clear studio:g03/fall", (functions / "stop_schedules.mcfunction").read_text())
            self.assertIn("schedule clear studio:g05/unpower", (functions / "stop_schedules.mcfunction").read_text())
            self.assertIn("kill @e[type=minecraft:arrow,x=154", (functions / "scene/g05/reset.mcfunction").read_text())
            self.assertIn("item replace block 156 82 0 container.0 with minecraft:arrow 64", (functions / "scene/g05/setup_apply_actor.mcfunction").read_text())
            self.assertIn("execute as @a if score @s studio_owner_id = #owner studio_lock", (functions / "scene/g01/setup_apply.mcfunction").read_text())
            self.assertIn("summon minecraft:zombie", (functions / "scene/g09/reset.mcfunction").read_text())
            self.assertIn("scoreboard players operation #owner studio_lock", (functions / "claim.mcfunction").read_text())
            self.assertIn("scoreboard players set #owner studio_lock 0", (functions / "admin/release.mcfunction").read_text())
            self.assertIn("Studio scene reset to its initial state", (functions / "scene/g01/reset.mcfunction").read_text())
            next_scene = (functions / "next.mcfunction").read_text()
            self.assertEqual(next_scene.count("return run function studio:scene/"), 10)
            self.assertNotIn("run function studio:scene/", next_scene.replace("return run function studio:scene/", ""))
        controller.OUT = old

    def test_docker_is_isolated_and_no_rcon_listener(self):
        compose = (ROOT / "docker-compose.yaml").read_text()
        self.assertIn('TYPE: "FABRIC"', compose)
        self.assertIn('VERSION: "1.21.11"', compose)
        self.assertIn("127.0.0.1:25565:25565", compose)
        self.assertIn('ENABLE_RCON: "FALSE"', compose)
        self.assertNotIn("../data", compose)
        self.assertIn("./data:/data", compose)
