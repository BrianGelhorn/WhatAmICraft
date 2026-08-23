# Minecraft Mystery V2

Formato vertical 1080×1920 a 30 fps para Shorts, Reels y TikTok. El reto empieza en el frame 0; no hay intro de logo independiente. La fuente editable es `data/mystery-v2-episodes.json`; React consume únicamente `src/generated/mystery-v2-episode.json`, producido por `scripts/produce_mystery_v2.py`.

## Segunda auditoría

- Se eliminó toda introducción separada: pregunta, categoría, silueta exacta y urgencia aparecen en el frame 0; la pista 1 empieza en el frame 35 (1,17 s).
- Se quitaron las tarjetas de pista. Cada pista reemplaza una o dos palabras clave y usa una mecánica visual propia: durabilidad/inventario, melee-ranged y Drowned/agua.
- El countdown sigue los timestamps reales de `three`, `two`, `one`; cada golpe de sonido comparte el mismo frame que su cambio visual.
- El reveal transforma la misma silueta en el asset final. El CTA de todas las variantes pide una única respuesta numérica: `1`, `2` o `3`.
- El último tramo vuelve a la posición, silueta, color y composición del hook para crear un loop reconocible.
- La voz ElevenLabs se genera por bloque, se normaliza y conserva timestamps por palabra. Solo el countdown puede acelerarse, hasta `1.6x`, si la toma real no entra; el resto exige acortar el copy.
- FAST, BALANCED y COMMENT BAIT comparten configuración, componentes y validaciones. No se añadieron dependencias.

## Guía visual

- Misterio/fondo: `#070B1A`; superficie: `#10172B`.
- Progreso: `#2DE2E6`; highlight: `#FFD166`; urgencia: `#FF6B35`; respuesta: `#6BFF95`; texto: blanco.
- Títulos: fuente pixel instalada por el proyecto, mínimo 68 px; texto auxiliar mínimo 27 px.
- Outline: 6 px; sombra dura para texto y glow solo para dirigir la mirada.
- Contenido esencial entre 160 y 1.560 px verticales y con 72 px de margen lateral. Subtítulos no comparten la franja del CTA.

## Hipótesis y A/B tests

- FAST (15,8 s): menor tiempo al payoff aumenta finalización y repeticiones.
- BALANCED (18,1 s, principal): más lectura sin perder frecuencia de cambios mejora comprensión y finalización.
- COMMENT BAIT (17,2 s): hook de dificultad + respuesta `1/2/3` aumenta comentarios por 1.000 vistas.
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

# Render individual
python scripts/produce_mystery_v2.py --variant fast --generate-audio --render
python scripts/produce_mystery_v2.py --variant balanced --generate-audio --render
python scripts/produce_mystery_v2.py --variant comment_bait --generate-audio --render

# Render de las tres variantes
python scripts/produce_mystery_v2.py --all-variants --generate-audio --render
```

Los videos salen en `out/previews/`. Audio y renders son artefactos locales ignorados por Git. Para revisar zonas seguras, escenas, timestamps, segmentos de voz y marcadores de retención, activar las opciones de `debug` en el JSON editable y volver a producir la configuración.

## Validaciones automáticas

El productor y `scripts/test_mystery_v2.py` rechazan: hook sin reto inmediato, primera pista posterior a 1,17 s, bloques de pista repetidos o con más de dos fragmentos, CTA no numérico o demasiado corto, orden hablado del countdown distinto de `3/2/1`, audio cortado o solapado, assets ausentes, identidad distinta entre respuesta/silueta/reveal, huecos de retención mayores a 1,5 s y componentes no deterministas.
