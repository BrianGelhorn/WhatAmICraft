# Uso

Reiniciar OpenCode después de actualizar la skill o el comando. No fija modelo ni proveedor.

```text
/escena diseña una familia de propiedades compartidas; no asignes episodio ni representes
/escena revisa las citas y el universo de F01 sin editar
/escena asigna F01 a un episodio real; valida M_i y V antes de proponer timing
/escena diseña tres minibiomas con relieve y siluetas distintas, cámara vertical y una zona de acción despejada; no instales nada
/escena mejora el minibioma de una escena existente usando minibiomes.md; compara relieve, profundidad y vegetación antes de editar
/escena implementa el diseño aprobado como prueba en Docker; revisa versión, respalda el mundo y comprueba setup/reset; no publiques
```

El ejemplo es didáctico y no está instalado. Los briefs históricos de `docs/scenes/` no se migran ni son compatibles; no hay fallback.

Con Python local:

```powershell
python .opencode/skills/minecraft-clip-director/scripts/validate_scene.py .opencode/skills/minecraft-clip-director/resources/scene.example.json --episode-bank data/quiz-copy-episodes.json
python -m unittest discover -s .opencode/skills/minecraft-clip-director/tests -v
```

`--episode-bank` solo contrasta IDs, texto literal y versión de las citas. El resultado no prueba semántica, mecánica, conservación real de candidatos, visual, UI, captura ni render.

Los planes de escena/minibioma usan `minibiomes.md`, no el validador JSON de familias. Pide cámara, alturas y distribución concretas; no basta con "más natural". Una prueba de decorado no requiere inventar una asignación de pistas.

Sin Python local, desde la raíz recuperada del proyecto, pruebas en Docker con montaje de solo lectura (no arranca Minecraft):

```powershell
docker run --rm --network none --mount "type=bind,source=$($PWD.Path),target=/r,readonly" -w /r -e PYTHONDONTWRITEBYTECODE=1 python:3.12-slim python -m unittest discover -s .opencode/skills/minecraft-clip-director/tests -v
```

Modificar esta skill no cambia el datapack cargado. Reinicia OpenCode desde el proyecto correcto para cargar sus instrucciones nuevas; luego solicita la reconstrucción de escenas si corresponde.
