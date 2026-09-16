---
name: minecraft-clip-director
description: Use when designing, reviewing, blockouting, detailing, validating or implementing Minecraft scenes, minibiomes, filming compositions or visual-property families.
---

# Minecraft Clip Director

Responde en español. Distingue **familia**, **diseño**, **revisión visual** y **construcción instalada**. Un decorado no demuestra por sí solo una propiedad.

## Rutas

Ejecuta solo lo pedido. No añadas episodios, candidatos, familias, lore, contexto narrativo ni implementación no solicitados.

- **Diseñar familia:** lee `resources/recipes.md` y `resources/scene.example.json`; usa citas y solo el banco necesario.
- **Asignar pistas:** lee `resources/template.md` y los intervalos reales; no impongas duración universal.
- **Diseñar escena:** lee `resources/minibiomes.md`; entrega intención, cámara, blockout, acción, assets, ritmo y rechazo. No edites Server.
- **Revisar escena:** compara propósito y resultado. Por defecto no edites; devuelve defectos observables y corrección mínima.
- **Crear blockout:** implementa solo masas, recorrido, cámara y foco; sin decoración.
- **Detallar escena:** conserva geometría, cámara y acción aprobadas; añade solo elementos pertinentes.
- **Implementar/probar:** lee `resources/server.md`, generador, catálogo, manifest y tests actuales. Edita Server solo ante `genera`, `implementa`, `instala` o `prueba en Docker`.
- **Validar escena:** prueba geometría, mecánica, assets y carga. Sin capturas conserva `visual_pending`.

Si se piden varias rutas, ejecútalas en orden. Diseñar no autoriza instalar; implementar no autoriza publicar ni ejecutar setup sin permiso. No cambies modelo, proveedor o permisos.

## Contrato de escena

Antes del bioma fija: propósito, emoción concreta, acción y consecuencia reales, un elemento héroe, prohibidos, cámara, punto de interés y recorrido. El propósito decide el entorno: una cueva empieza por volumen, techo, acceso y oscuridad; los árboles no son candidatos por defecto.

## Puertas

Corrige la primera que falle:

1. **Relevancia:** cada elemento apoya acción, pertenencia ambiental, profundidad, silueta o guía; si no, elimínalo.
2. **Blockout:** masas, horizonte, recorrido y foco se leen desde cámara antes del detalle.
3. **Jugabilidad:** camino, línea visual, soporte, espacio y acción segura.
4. **Assets:** tags exactos, escala, cantidad, exclusiones y zona; nunca orden alfabético ni sustitución silenciosa.
5. **Ritmo:** anticipación, acción y consecuencia producen cambios visibles; ruido no equivale a impacto.
6. **Prueba:** tests demuestran funcionamiento; capturas reales demuestran imagen.

Usa `resources/minibiomes.md` para arquetipos, medidas y rechazo. `visual_pending` significa que faltan capturas, no aprobación.

## Fuentes vivas

No dupliques presets aquí. Lee `Server/scene_controller.py`, `Server/generated/studio/manifest.json`, el catálogo de assets y `Server/README.md`. Los briefs históricos no son fallback. El plan Markdown de escena no pertenece al JSON de familia.

## Familias

Una familia es un predicado compartido por >=2 targets con citas. Incluye universo y una cita por target (`episode_id`, texto, versión, fuente y `fact_ids` si existen). Separa ilustración, límites y `audiovisual_design`; no falsees causalidad.

Estados: `documented`, `mechanics_pending`, `candidate_preservation_pending`, `visual_pending`; nunca `verified` por una declaración. No recortes el universo para fabricar 3→2→1; `M_1` debe ser subconjunto estricto y un universo `provisional` no certifica.

## Entrega

- Diseño: contrato, blockout, assets, diferencias, ritmo y rechazo.
- Revisión: hallazgos por impacto, sin puntuaciones inventadas.
- Implementación: archivos, tests, manifest y carga.
- Validación: separa técnica de visual; sin capturas, `visual_pending`.
- Familia: ejecuta `scripts/validate_scene.py <familia> --episode-bank data/quiz-copy-episodes.json`.

`resources/usage.md` contiene comandos. No despliegues al mejorar solo esta skill.
