import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_scene.py"
spec = importlib.util.spec_from_file_location("validate_scene", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class SceneBriefTests(unittest.TestCase):
    def setUp(self):
        self.brief = json.loads((ROOT / "resources/scene.example.json").read_text(encoding="utf-8"))

    def test_example(self):
        validator.validate(self.brief)

    def test_rejects_invalid_contract_fields(self):
        for key, value in (("id", "G00"), ("recipe", "absorb_water"), ("recipe", []), ("fps", 20), ("duration_frames", True), ("hook_frame", 45), ("status", "aprobado_visual"), ("props", []), ("reset", []), ("spoiler_exclusions", []), ("output", "mc_reaction_loop_t01.mp4"), ("output", "../mc_reaction_scene_t01.mp4")):
            with self.subTest(key=key, value=value):
                brief = copy.deepcopy(self.brief)
                brief[key] = value
                with self.assertRaises(ValueError):
                    validator.validate(brief)
        self.brief["unexpected"] = "typo"
        with self.assertRaises(ValueError):
            validator.validate(self.brief)

    def test_rejects_duplicate_categories(self):
        self.brief["uses"][2]["category"] = " HERRAMIENTAS "
        with self.assertRaises(ValueError):
            validator.validate(self.brief)

    def test_rejects_gaps_overlaps_and_truncation(self):
        for index, key, value in ((1, "start", 31), (1, "start", 29), (2, "end", 178), (0, "end", -1), (0, "start", False)):
            with self.subTest(index=index, key=key, value=value):
                brief = copy.deepcopy(self.brief)
                brief["beats"][index][key] = value
                with self.assertRaises(ValueError):
                    validator.validate(brief)

    def test_manual_action_requires_instructions(self):
        self.brief["automation"]["manual_actions"] = []
        with self.assertRaises(ValueError):
            validator.validate(self.brief)

    def test_fixed_camera_and_invalid_vectors(self):
        for key, value in (("position", [280, 91, -4]), ("position", [282, float("inf"), -4]), ("look_at", [282, 91, -4]), ("frame", 180)):
            with self.subTest(key=key, value=value):
                brief = copy.deepcopy(self.brief)
                brief["camera"]["keyframes"][1][key] = value
                with self.assertRaises(ValueError):
                    validator.validate(brief)

    def test_linear_camera_allowed(self):
        self.brief["camera"]["movement"] = "linear"
        self.brief["camera"]["keyframes"][1]["position"] = [283, 91, -4]
        validator.validate(self.brief)

    def test_cli_readonly_and_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "brief.json"
            for content, expected in ((json.dumps(self.brief), 0), ("{", 1), ("null", 1)):
                brief.write_text(content, encoding="utf-8")
                result = subprocess.run([sys.executable, str(SCRIPT), str(brief)], capture_output=True, text=True)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertEqual(brief.read_text(encoding="utf-8"), content)
                self.assertEqual(len(list(Path(directory).iterdir())), 1)

    def test_skill_size_and_resources(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\nname: minecraft-clip-director\n"))
        self.assertLess(len(skill.split()), 600)
        for file in ("recipes.md", "scene.example.json", "server.md", "usage.md"):
            self.assertTrue((ROOT / "resources" / file).is_file())


if __name__ == "__main__":
    unittest.main()
