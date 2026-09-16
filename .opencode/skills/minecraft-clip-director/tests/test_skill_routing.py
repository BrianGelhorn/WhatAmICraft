import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
PROJECT = ROOT.parents[2]


class SkillRoutingTests(unittest.TestCase):
    def test_scene_routes_are_explicit_and_isolated(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for route in ("Diseñar escena", "Revisar escena", "Crear blockout", "Detallar escena",
                      "Implementar/probar", "Validar escena"):
            self.assertIn(route, skill)
        self.assertIn("No añadas episodios, candidatos, familias, lore", skill)

    def test_resources_do_not_duplicate_live_scene_presets(self):
        text = "\n".join((ROOT / "resources" / name).read_text(encoding="utf-8")
                         for name in ("minibiomes.md", "server.md"))
        for scene in ("f02", "f03", "f04", "f11"):
            self.assertNotIn(scene, text)
        self.assertIn("Server/generated/studio/manifest.json", text)

    def test_command_distinguishes_review_from_implementation(self):
        command = (PROJECT / ".opencode" / "commands" / "escena.md").read_text(encoding="utf-8")
        self.assertIn("`diseña` y `revisa` no editan Server", command)
        self.assertIn("`genera`, `implementa`, `instala`", command)


if __name__ == "__main__":
    unittest.main()
