# Uso

Reiniciar OpenCode después de actualizar la skill o el comando. No fija modelo ni proveedor.

```text
/escena diseña una familia de propiedades compartidas; no asignes episodio ni representes
/escena revisa las citas y el universo de F01 sin editar
/escena asigna F01 a un episodio real; valida M_i y V antes de proponer timing
```

El ejemplo es didáctico y no está instalado. Los briefs históricos de `docs/scenes/` no se migran ni son compatibles; no hay fallback.

Con Python local:

```powershell
python .opencode/skills/minecraft-clip-director/scripts/validate_scene.py .opencode/skills/minecraft-clip-director/resources/scene.example.json --episode-bank data/quiz-copy-episodes.json
python -m unittest discover -s .opencode/skills/minecraft-clip-director/tests -v
```

`--episode-bank` solo contrasta IDs, texto literal y versión de las citas. El resultado no prueba semántica, mecánica, conservación real de candidatos, visual, UI, captura ni render.
