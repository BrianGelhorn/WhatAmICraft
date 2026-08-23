# Minecraft Mystery V2

Formato vertical 1080×1920 a 30 fps para Shorts, Reels y TikTok. El reto empieza en el frame 0; no hay intro de logo independiente. La fuente editable es `data/mystery-v2-episodes.json`; React consume únicamente `src/generated/mystery-v2-episode.json`, producido por `scripts/produce_mystery_v2.py`.

## Qué cambió

- Se reemplazó el hook de seis segundos y las tarjetas estáticas por un reto inmediato con silueta exacta, categoría, pregunta, urgencia y progreso.
- Cada pista combina copy progresivo, visual específico y transformación: durabilidad/inventario, combate melee-ranged y Drowned/agua.
- Countdown, reveal, CTA y puente de loop son escenas propias; el reveal transforma la misma silueta en el asset final.
- La voz ElevenLabs se genera por bloque, se normaliza y usa timestamps reales por palabra. El productor rechaza audios que se corten o solapen.
- FAST, BALANCED y COMMENT BAIT comparten componentes y cambian solo por configuración.

## Guía visual

- Misterio/fondo: `#091225`; superficie: `#111B32`.
- Progreso: `#63D471`; highlight: `#FFD34F`; urgencia: `#FF6B35`; respuesta: `#7CFF6B`; texto: blanco.
- Títulos: fuente pixel instalada por el proyecto, mínimo 72 px; texto auxiliar mínimo 34 px.
- Outline: 4–6 px; sombra dura de 8–12 px; tarjetas de 28 px de radio.
- Contenido esencial entre 160 y 1.560 px verticales y con 72 px de margen lateral. Subtítulos no comparten la franja del CTA.

## Hipótesis y A/B tests

- FAST (15 s): menor tiempo al payoff aumenta finalización y repeticiones.
- BALANCED (19,5 s, principal): más lectura sin perder frecuencia de cambios mejora comprensión y finalización.
- COMMENT BAIT (18,7 s): hook de dificultad + respuesta `1/2/3` aumenta comentarios por 1.000 vistas.
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
