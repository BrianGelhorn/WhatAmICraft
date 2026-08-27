# WhatAmICraft

Sistema de producción del quiz definitivo de Minecraft. Existe una sola plantilla de video: `QuizCapasCopy`, con exactamente tres pistas, audio normalizado y miniaturas oficiales verticales.

## Fuente editable

- Episodios: `data/quiz-copy-episodes.json`
- Validación: `schemas/quiz-copy-episode.schema.json`
- Productor: `scripts/produce_quiz_copy.py`
- Config generada: `src/generated/quiz-copy-episode.json`
- Videos: `out/episodes/*.mp4`
- Miniaturas: `out/thumbnails/<tipo>/<variante>/*.jpg` (por ejemplo, `out/thumbnails/food/default/`)

## Comandos

```powershell
npm run dev
python scripts/produce_quiz_copy.py --episode mc-03 --dry-run
python scripts/produce_quiz_copy.py --episode mc-03 --render
python scripts/produce_quiz_copy.py --episode mc-03 --thumbnails-only
```

En el mini‑PC, los mismos comandos se ejecutan dentro del servicio `producer`:

```bash
docker compose run --rm producer --episode mc-03 --dry-run
docker compose run --rm producer --episode mc-03 --render
```

El dashboard privado administra revisión, publicación y estadísticas. Las miniaturas verticales se organizan por tipo y variante; YouTube recibe la miniatura vertical correspondiente.

Para cambiar la plantilla de producción sin mezclar versiones, seguí el flujo de [releases de plantillas](docs/template-releases.md). Cada episodio renderizado conserva props y hashes propios; no se debe sobrescribir la configuración global durante una producción.

## Biblioteca musical

En la sección `Música` del dashboard del mini‑PC, pegá un link de YouTube, elegí la plantilla y escribí uno o varios comienzos, por ejemplo `0:32, 1:15, 2:08`. La fuente se descarga una sola vez y cada momento se convierte en un fragmento de 2 minutos. También podés guardar uno o varios comienzos para cada canción original de Minecraft. Cada combinación de canción y comienzo participa como una opción del sorteo; el reel usa solamente el tramo que necesita. Importá únicamente audio que tengas permiso de reutilizar.
