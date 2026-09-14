# Skill: minecraft-clip-director

# Minecraft Clip Director

Responde en español. Primero diseña **familias visuales generales**, no escenas de buscar, esfuerzo o celebración ni briefs obligatorios por episodio/ballesta. Una familia expresa un predicado compartido por >=2 targets distintos, respaldado por citas de hechos/version/fuente; después, con autorización aparte, se asigna a pistas.

## Etapas y alcance

La autorización explícita de una etapa permite solo esa etapa. Tras editar, muestra resultado y pruebas y pide revisión; no avances a asignación, representación, Server, Remotion, render o publicación. No cambies modelo, proveedor o permisos.

- **Diseñar familia:** no requiere episodio ni duración. Lee selectivamente `recipes.md`, `scene.example.json` y, para las citas, solo los casos necesarios del banco.
- **Asignar a pistas:** autorización separada. Lee `template.md` y los intervalos del episodio real; el timing se resuelve aquí, nunca se fija a 155 ni se inventan tres beats para una familia.
- **Representar/integrar:** autorización separada. Lee `server.md` solo al implementar. Una familia no instala ni promete captura vanilla, UI Remotion, vídeo, render o soporte de fondo.

No leas ni migres `docs/scenes/`: los briefs históricos genéricos no son compatibles con este contrato y no hay fallback silencioso.

## Contrato de familia

Usa `resources/scene.example.json`. Incluye predicado, >=2 targets, universo conjunto de candidatos y una cita por target (`episode_id`, texto literal, versión, fuente; `fact_ids` si existen). Declara por separado: parte ilustrada, no demostrada y estos atributos audiovisuales prohibidos: textura, sonido, entorno, cantidades y montaje. No uses HUD ni target visible para “probar” una propiedad de otro objeto.

Las etiquetas son literales: `documented`, `mechanics_pending`, `candidate_preservation_pending`, `visual_pending`. Una declaración no es prueba mecánica: nunca marques `verified`. Registra versiones no vacías por caso: contenido generado nuevo exige Java 26.1; el ejemplo histórico usa 1.21.5 y captura Server 1.21.11. No hay migración automática.

El universo no se recorta para fabricar 3→2→1. En asignación, `clue_index` elige un `M_i` y exige solo `M_i ⊆ V`; los tres `M_i` aún se validan con >=2, reducción estricta, >=2 tras dos pistas y target único tras tres. Universo `provisional` rechaza certificación. El validador solo comprueba estructura, citas y conjuntos declarados, no verdad semántica.

## Entrega

Ejecuta `scripts/validate_scene.py <familia> --episode-bank data/quiz-copy-episodes.json`; la fuente es opcional y de solo lectura. Muestra familia, restricciones, estados pendientes y bloqueo de representación. `usage.md` contiene comandos; el ejemplo es didáctico, no instalado.
