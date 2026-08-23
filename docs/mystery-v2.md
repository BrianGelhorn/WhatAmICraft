# Minecraft Mystery V2

Formato vertical 1080×1920 a 30 fps para Shorts, Reels y TikTok. El reto empieza en el frame 0; no hay intro de logo independiente. La fuente editable es `data/mystery-v2-episodes.json`; React consume únicamente `src/generated/mystery-v2-episode.json`, producido por `scripts/produce_mystery_v2.py`.

## Tercera auditoría

- Se eliminó toda introducción separada: pregunta, categoría, silueta exacta y urgencia aparecen en el frame 0; la pista 1 empieza en el frame 35 (1,17 s).
- Se quitaron las tarjetas de pista. Cada pista reemplaza una o dos palabras clave y usa una mecánica visual propia: durabilidad/inventario, melee-ranged y Drowned/agua.
- El countdown sigue los timestamps reales de `three`, `two`, `one`; cada golpe de sonido comparte el mismo frame que su cambio visual.
- El reveal transforma la misma silueta en el asset final. El CTA de todas las variantes pide una única respuesta numérica: `1`, `2` o `3`.
- El último tramo vuelve a la posición, silueta, color y composición del hook para crear un loop reconocible.
- El hook principal se redujo a `CAN YOU NAME IT?`; la silueta oscila y pulsa desde el primer frame.
- El countdown usa el inicio real de cada palabra para escalar y cambiar de cian a dorado y naranja.
- El reveal demora el nombre seis frames respecto de la transformación visual para que la respuesta tenga un payoff legible.
- Las pistas usan únicamente contexto reconocible de Minecraft: el tridente se desgasta, ocupa un slot, golpea o se lanza contra un zombie y aparece equipado por un Drowned. Se eliminaron barras, flechas, scanlines y flashes de pantalla decorativos.
- El CTA mantiene `COMMENT 1, 2, OR 3` y ahora muestra también `HOW MANY HINTS DID YOU NEED?` dentro de la composición, no solo en la voz.
- La voz ElevenLabs se genera por bloque, se normaliza y conserva timestamps por palabra. Solo el countdown puede acelerarse, hasta `1.6x`, si la toma real no entra; el resto exige acortar el copy.
- Las voces se cachean por texto, voz y modelo, no por variante: las pistas compartidas no vuelven a consumir ElevenLabs cuando cambia únicamente el timeline.
- FAST, BALANCED y COMMENT BAIT comparten configuración, componentes y validaciones. El modo preview reduce resolución y partículas y evita blur de fondo. No se añadieron dependencias.

## Recetas visuales

Cada pista declara una receta en `hints[].visual`; Remotion decide la composición y el movimiento. No existe un fallback genérico: una receta desconocida o sin su asset requerido detiene la producción antes de generar voz.

- `item-state`: muestra estados verificables dentro de un slot de inventario; la durabilidad usa su indicador rotulado y el límite de stack muestra la cantidad `1`.
- `item-versus-entity`: enfrenta la respuesta con una entidad configurada y representa contacto o lanzamiento.
- `entity-holds-answer`: equipa la respuesta en una entidad configurada y puede activar un entorno como `water`.

Las recetas actuales son las únicas habilitadas porque ya tienen un caso visual revisado. Al incorporar una pista de receta, uso de herramienta, drop o dimensión se agrega una receta nueva con su propio episodio de prueba; no se simula con barras, flechas ni flashes decorativos.

## Guía visual

- Misterio/fondo: `#070B1A`; superficie: `#10172B`.
- Progreso: `#2DE2E6`; highlight: `#FFD166`; urgencia: `#FF6B35`; respuesta: `#6BFF95`; texto: blanco.
- Títulos: fuente pixel instalada por el proyecto, mínimo 68 px; texto auxiliar mínimo 27 px.
- Outline: 6 px; sombra dura para texto y glow solo para dirigir la mirada.
- Escenarios y tarjetas: bordes redondeados de 28–72 px, profundidad mediante sombra y movimiento ligado a la acción representada.
- Hooks: `displayText` funciona como contexto breve y `emphasisText` ocupa la jerarquía principal; en BALANCED, `NAME IT?` domina el primer frame.
- Contenido esencial entre 160 y 1.560 px verticales y con 72 px de margen lateral. Subtítulos no comparten la franja del CTA.

## Hipótesis y A/B tests

- FAST (15,5 s): menor tiempo al payoff aumenta finalización y repeticiones.
- BALANCED (16,5 s, principal): más lectura sin perder frecuencia de cambios mejora comprensión y finalización.
- COMMENT BAIT (16,9 s): hook de dificultad + respuesta `1/2/3` aumenta comentarios por 1.000 vistas.
- Variables aislables: `hookVariant`, `ctaVariant`, `visualIntensity`, duración de pista, copy hablado, color de urgencia y música. No cambiar más de una variable por cohorte.
- Métricas: retención a 1/3/5 s, porcentaje visto, finalización, repeticiones, comentarios/1.000 vistas y abandono por escena.

## Comandos

```bash
npm ci

# Validar fuente, assets, timings y las tres variantes sin gastar ElevenLabs
python scripts/produce_mystery_v2.py --all-variants --visual-only --dry-run
PYTHONPATH=scripts python scripts/test_mystery_v2.py
npm run lint

# Generar/cachar voz y timestamps reales
python scripts/produce_mystery_v2.py --all-variants --generate-audio

# Abrir Studio con la última configuración generada
npx remotion studio

# Preview silencioso 540x960 + contact sheet para iterar rápido
python scripts/produce_mystery_v2.py --variant balanced --preview --contact-sheet

# Render individual
python scripts/produce_mystery_v2.py --variant fast --generate-audio --render
python scripts/produce_mystery_v2.py --variant balanced --generate-audio --render
python scripts/produce_mystery_v2.py --variant comment_bait --generate-audio --render

# Render de las tres variantes
python scripts/produce_mystery_v2.py --all-variants --generate-audio --render

# Contact sheet del render final existente
python scripts/produce_mystery_v2.py --variant balanced --contact-sheet
```

Los videos salen en `out/previews/`. Audio y renders son artefactos locales ignorados por Git. Para revisar zonas seguras, escenas, timestamps, segmentos de voz y marcadores de retención, activar las opciones de `debug` en el JSON editable y volver a producir la configuración.

## Validaciones automáticas

El productor y `scripts/test_mystery_v2.py` rechazan: hook sin reto inmediato, primera pista posterior a 1,17 s, bloques de pista repetidos o con más de dos fragmentos, CTA no numérico o demasiado corto, orden hablado del countdown distinto de `3/2/1`, audio cortado o solapado, assets ausentes, identidad distinta entre respuesta/silueta/reveal, huecos de retención mayores a 1,5 s y componentes no deterministas.

Crossbow no se agregó como segundo episodio porque ya figura en `data/used-targets.json` y en el formato histórico. El contrato de deduplicación global impide reutilizarlo aunque cambie la plantilla; el test evita que entre accidentalmente al banco Mystery V2.
