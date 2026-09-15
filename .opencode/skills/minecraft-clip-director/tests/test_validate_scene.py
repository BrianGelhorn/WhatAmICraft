# Reconstructed 2026-09-14: the Sep-14 test file was lost with OneDrive and never
# pushed. These tests are rebuilt against the visual-property family contract
# (SKILL.md2126 familias), not the original file.
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


def valid_assignment(target="mace"):
    return {
        "episode_id": "mc-21",
        "clue_index": 1,
        "target_id": target,
        "candidate_universe_status": "provisional",
        "candidate_universe_ids": ["mace", "trident", "fishing_rod", "wind_charge"],
        "visual_candidate_ids": ["mace", "trident", "fishing_rod"],
        "clue_matches": [
            {"index": 1, "candidate_ids": ["mace", "trident", "fishing_rod"]},
            {"index": 2, "candidate_ids": ["mace", "trident"]},
            {"index": 3, "candidate_ids": ["mace", "fishing_rod"]},
        ],
        "certification": "refused_incomplete_universe",
    }


class FamilyTests(unittest.TestCase):
    def setUp(self):
        self.family = json.loads((ROOT / "resources/scene.example.json").read_text(encoding="utf-8"))

    def test_example(self):
        validator.validate(self.family)

    def test_rejects_bad_ids_and_targets(self):
        for key, value in (("id", "G08"), ("id", "  "), ("targets", ["mace"]), ("targets", ["mace", "mace"]), ("title", ""), ("predicate", "  ")):
            with self.subTest(key=key, value=value):
                family = copy.deepcopy(self.family)
                family[key] = value
                with self.assertRaises(ValueError):
                    validator.validate(family)
        family = copy.deepcopy(self.family)
        family["unexpected"] = "typo"
        with self.assertRaises(ValueError):
            validator.validate(family)

    def test_rejects_bad_status(self):
        for status in ({"documentation": "verified", "mechanics": "mechanics_pending", "candidate_preservation": "candidate_preservation_pending", "visual": "visual_pending"}, {"documentation": "documented"}):
            with self.subTest(status=status):
                family = copy.deepcopy(self.family)
                family["status"] = status
                with self.assertRaises(ValueError):
                    validator.validate(family)

    def test_rejects_bad_universe(self):
        family = copy.deepcopy(self.family)
        family["candidate_universe"]["candidate_ids"] = ["golden_apple"]
        with self.assertRaises(ValueError):
            validator.validate(family)
        family = copy.deepcopy(self.family)
        family["candidate_universe"]["status"] = "complete-ish"
        with self.assertRaises(ValueError):
            validator.validate(family)

    def test_rejects_bad_citations(self):
        for key, value in (("source", "docs/scenes/x.json"), ("clue_index", 4), ("version", ""), ("fact_ids", "mc-25")):
            with self.subTest(key=key, value=value):
                family = copy.deepcopy(self.family)
                family["source_cases"][0][key] = value
                with self.assertRaises(ValueError):
                    validator.validate(family)

    def test_rejects_bad_audiovisual_and_versions(self):
        family = copy.deepcopy(self.family)
        del family["audiovisual_design"]["montage"]
        with self.assertRaises(ValueError):
            validator.validate(family)
        family = copy.deepcopy(self.family)
        family["audiovisual_design"]["texture"] = "  "
        with self.assertRaises(ValueError):
            validator.validate(family)
        family = copy.deepcopy(self.family)
        family["case_versions"]["generated_content"] = ""
        with self.assertRaises(ValueError):
            validator.validate(family)
        family = copy.deepcopy(self.family)
        family["not_demonstrated"] = []
        with self.assertRaises(ValueError):
            validator.validate(family)

    def test_assignment_provisional_refused(self):
        family = copy.deepcopy(self.family)
        family["targets"] = ["mace", "trident"]
        family["source_cases"] = [
            {"target_id": "mace", "episode_id": "mc-21", "clue_index": 1, "clue_text": "I am a non-stackable weapon that loses durability through normal use.", "version": "1.21.5", "source": "data/quiz-copy-episodes.json", "fact_ids": []},
            {"target_id": "trident", "episode_id": "mc-22", "clue_index": 1, "clue_text": "I am a non-stackable weapon that loses durability through normal use.", "version": "1.21.5", "source": "data/quiz-copy-episodes.json", "fact_ids": []},
        ]
        family["candidate_universe"] = {"status": "provisional", "candidate_ids": ["mace", "trident", "fishing_rod"], "scope": "Solo citados mas un tercero declarado para el encadenado 3-2-1."}
        family["assignment"] = valid_assignment()
        validator.validate(family)

    def test_assignment_rejects_bad_sets(self):
        family = copy.deepcopy(self.family)
        family["assignment"] = valid_assignment()
        family["assignment"]["certification"] = "verified"
        with self.assertRaises(ValueError):
            validator.validate(family)
        family["assignment"] = valid_assignment()
        family["assignment"]["clue_matches"][0]["candidate_ids"] = ["mace", "unknown_target"]
        with self.assertRaises(ValueError):
            validator.validate(family)

    def test_assignment_rejects_trivial_first_clue(self):
        family = copy.deepcopy(self.family)
        assignment = valid_assignment()
        first = list(assignment["clue_matches"][0]["candidate_ids"])
        assignment["candidate_universe_ids"] = first
        assignment["visual_candidate_ids"] = first
        family["assignment"] = assignment
        with self.assertRaises(ValueError):
            validator.validate(family)

    def test_cli_readonly_and_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "family.json"
            for content, expected in ((json.dumps(self.family), 0), ("{", 1), ("null", 1)):
                brief.write_text(content, encoding="utf-8")
                result = subprocess.run([sys.executable, str(SCRIPT), str(brief)], capture_output=True, text=True)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertEqual(brief.read_text(encoding="utf-8"), content)
                self.assertEqual(len(list(Path(directory).iterdir())), 1)

    def test_skill_size_and_resources(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("minecraft-clip-director", skill)
        self.assertLess(len(skill.split()), 600)
        for file in ("recipes.md", "scene.example.json", "server.md", "usage.md", "template.md"):
            self.assertTrue((ROOT / "resources" / file).is_file())


if __name__ == "__main__":
    unittest.main()
