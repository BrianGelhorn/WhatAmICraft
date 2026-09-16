# Uso

Reinicia OpenCode después de modificar esta skill o el comando. No fija modelo ni proveedor. Las rutas visuales siguen `minibiomes.md`.

## Escenas

```text
/escena diseña f03 como cueva para una prueba de luz; sin vegetación; no implementes
/escena revisa f03 contra su propósito y arquetipo; no edites
/escena crea solo el blockout de f03: volumen, recorrido y cámara; sin detalle
/escena detalla el blockout aprobado de f03 sin cambiar geometría ni acción
/escena implementa f03 como prueba en Docker; compila y recarga, no ejecutes setup
/escena prueba f03 en el mundo; respalda, valida setup/reset y deja visual_pending
/escena valida geometría, recorrido, peligros, assets y manifest de f03
/escena diseña tres minibiomas con propósitos, siluetas y cámaras distintas; no instales
```

## Familias y pistas

```text
/escena diseña una familia de propiedades compartidas; no asignes episodio ni representes
/escena revisa las citas y el universo de F01 sin editar
/escena asigna F01 a un episodio real; valida M_i y V antes de proponer timing
```

Una petición de escena no requiere familia, episodio ni candidatos. Un blockout no incluye detalle. `revisa` no edita. `implementa` modifica archivos pero no construye el mundo salvo autorización explícita para setup.

Para familias:

```powershell
python .opencode/skills/minecraft-clip-director/scripts/validate_scene.py <familia.json> --episode-bank data/quiz-copy-episodes.json
python -m unittest discover -s .opencode/skills/minecraft-clip-director/tests -v
```

Sin Python local:

```powershell
docker run --rm --network none --mount "type=bind,source=$($PWD.Path),target=/r,readonly" -w /r -e PYTHONDONTWRITEBYTECODE=1 python:3.12-slim python -m unittest discover -s .opencode/skills/minecraft-clip-director/tests -v
```

Modificar la skill no cambia el datapack. Reinicia OpenCode para cargar sus instrucciones nuevas; reconstruye escenas solo si se solicita por separado.
