---
name: minecraft-clip-director
description: Use when creating, reviewing or improving Minecraft scenes, minibiomes, terrain, filming compositions or visual-property families, and implementing authorized studio datapacks.
---

# Minecraft Clip Director

Responde en español. Distingue **familia de propiedades**, **diseño de escena** y **construcción instalada**. Una familia expresa un predicado compartido por >=2 targets con citas; no es un decorado. Nunca rebautices una escalera o puente como demostración de durabilidad.

## Etapas y alcance

Ejecuta las etapas que el usuario pidió explícitamente, sin pedir otra vez el mismo permiso. Diseñar no autoriza instalar; pedir una prueba en Docker sí autoriza esa implementación de prueba, no publicación ni certificación. No cambies modelo, proveedor o permisos.

- **Diseñar familia:** lee `resources/recipes.md`, `resources/scene.example.json` y solo los casos necesarios del banco. No requiere duración.
- **Crear/mejorar escena o minibioma:** lee `resources/minibiomes.md`. Diseña desde la cámara: relieve, foco, profundidad, acción y ensayo. No exige inventar episodio ni conjuntos de candidatos si solo se prueba un decorado.
- **Asignar a pistas:** lee `resources/template.md` y los intervalos reales. No fijes 155 frames ni inventes tres beats por familia.
- **Implementar/probar:** lee `resources/server.md`, el generador y sus tests actuales. Una prueba visual puede seguir provisional; no equivale a una asignación certificada.

No migres automáticamente `docs/scenes/`: sus briefs históricos no cumplen el contrato de familia. El plan de construcción es un documento aparte; no agregues campos al JSON que su validador no acepta.

## Calidad visual

No confundas neutro con plano. Mantén despejada la acción y compón primer plano, plano de acción y fondo; relieve asimétrico visible, vegetación agrupada y siluetas diferentes. Más superficie, ruido o árboles idénticos no mejoran el plano. En varias escenas cambia topografía, encuadre y distribución, no solo materiales.

Usa `resources/minibiomes.md` para medidas, ejemplos y criterios de rechazo. HUD y objetos reales sirven en pruebas explícitas; en un quiz no reveles la respuesta antes de tiempo. Decoración y entorno tampoco deben descartar candidatos compatibles.

## Contrato de familia

Incluye predicado, >=2 targets, universo conjunto y una cita por target (`episode_id`, texto literal, versión, fuente; `fact_ids` si existen). Separa parte ilustrada, límites y `audiovisual_design` (textura, sonido, entorno, cantidades, montaje). Nunca uses un objeto para probar otro ni falsees causalidad con montaje.

Las etiquetas son literales: `documented`, `mechanics_pending`, `candidate_preservation_pending`, `visual_pending`. Una declaración no es prueba mecánica: nunca marques `verified`. Registra versiones no vacías por caso: contenido generado nuevo exige Java 26.1; el ejemplo histórico usa 1.21.5 y captura Server 1.21.11. No hay migración automática.

El universo no se recorta para fabricar 3→2→1. En asignación, `clue_index` elige un `M_i` y exige solo `M_i ⊆ V`, con `M_1` siempre subconjunto estricto del universo (la pista 1 debe descartar a alguien); los tres `M_i` aún se validan con >=2, reducción estricta, >=2 tras dos pistas y target único tras tres. Universo `provisional` rechaza certificación. El validador solo comprueba estructura, citas y conjuntos declarados, no verdad semántica.

## Entrega

Para familias ejecuta `scripts/validate_scene.py <familia> --episode-bank data/quiz-copy-episodes.json`. Para escenas entrega plan, diferencias visuales y ensayo pendiente; para implementación añade tests y evidencia de carga. Sin capturas desde la cámara prevista no declares calidad visual comprobada. `resources/usage.md` contiene comandos. No despliegues al mejorar solo esta skill.
