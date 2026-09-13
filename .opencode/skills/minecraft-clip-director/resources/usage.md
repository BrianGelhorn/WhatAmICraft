# Uso Con Modelos Basicos

Reiniciar OpenCode despues de instalar/actualizar la skill y el comando. Elegir el modelo disponible que quieras en la interfaz: no se fija proveedor, coste ni modelo en archivos del proyecto.

## Pedidos Cortos

```text
/escena explica G08
/escena crea una escena de duda, 5 segundos, camara fija, sin mobs
/escena ajusta solo la camara de G08 para ver mejor el nicho
/escena implementa en Server el brief docs/scenes/G11.json
```

El ultimo requiere un brief existente y ampliar explicitamente el registro actual G01-G10. No es una funcion que el servidor ya tenga.

Para limitar trabajo: indicar `solo guion`, `solo camara`, `sin modificar Server` o `implementar`. Para comparar modelos usar conversaciones nuevas con el mismo pedido: la skill no elimina el historial de un chat largo.

## Recursos Bajo Demanda

| Recurso | Se usa para |
|---|---|
| `SKILL.md` | Reglas/ruta corta, menos de 600 palabras |
| `recipes.md` | Elegir entre nueve situaciones y evitar mecanicas exclusivas |
| `scene.example.json` | Contrato y ejemplo completo basado en G08, no plantilla vacia |
| `validate_scene.py` | Comprobar campos, tiempos, camara y nombres sin gastar razonamiento en aritmetica |
| `server.md` | Integrar un brief en datapack sin reescribir controles |

El JSON es un **brief de diseno de una sola toma**, no un importador ni ejecutor. El servidor no lo consume. `setup`, `reset` y acciones son instrucciones de diseno; el validador no ejecuta comandos ni Minecraft.

## Validar Sin Docker

Desde la raiz del repositorio, con Python 3 instalado:

```powershell
python .opencode/skills/minecraft-clip-director/scripts/validate_scene.py .opencode/skills/minecraft-clip-director/resources/scene.example.json
python -m unittest discover -s .opencode/skills/minecraft-clip-director/tests -v
```

Para un brief real, reemplazar el ultimo argumento de la primera orden por `docs/scenes/<ID>.json`.

## Validar Sin Python Local

Desde la raiz del repositorio, con Docker disponible (imagen Python descargada antes si falta):

```powershell
docker run --rm --network none --mount "type=bind,source=${PWD},target=/repo,readonly" -w /repo -e PYTHONDONTWRITEBYTECODE=1 python:3.12-slim python .opencode/skills/minecraft-clip-director/scripts/validate_scene.py .opencode/skills/minecraft-clip-director/resources/scene.example.json
docker run --rm --network none --mount "type=bind,source=${PWD},target=/repo,readonly" -w /repo -e PYTHONDONTWRITEBYTECODE=1 python:3.12-slim python -m unittest discover -s .opencode/skills/minecraft-clip-director/tests -v
```

Montaje de solo lectura, sin servidor ni mundo ejecutandose. PASS confirma estructura; no confirma calidad narrativa, versiones de comandos, reuso semantico, colisiones ni render.

## Comparacion Honesta

Probar los mismos tres pedidos en sesiones nuevas, con y sin skill: busqueda sin mobs, reveal neutro, y una propuesta prohibida de esponja absorbiendo. El ultimo debe rechazar esa mecanica y ofrecer una situacion reutilizable.

Registrar modelo, tokens de entrada/salida mostrados por OpenCode, tiempo, reintentos, errores del validador y revision de los seis criterios de `recipes.md`. Comparar calidad con ensayo visual de al menos una escena. Elegir el modelo mas economico que pase estos controles en tus pruebas; no asumir equivalencia de calidad ni ahorro medido antes de hacerlo.

El ahorro esperado proviene de no repetir contexto y corregir errores mecanicos por script. Un ejemplo JSON tiene mas coste que una pregunta simple: la ruta de explicacion no debe cargarlo.
