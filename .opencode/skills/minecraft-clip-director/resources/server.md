# Implementación posterior

Leer únicamente tras autorización expresa de representación/implementación. Una familia o su validación no consume Server, no instala datapacks, no captura vanilla y no aprueba render real.

La captura Server del ejemplo es Java 1.21.11; el banco histórico del ejemplo es 1.21.5 y contenido generado nuevo exige 26.1. Registrar versiones por caso, sin valores globales automáticos ni migración mecánica. Cualquier cambio en `Server`, Docker, mundo o Remotion requiere una etapa y autorización distintas.

## Antes de generar comandos

- Lee el generador, tests y compose actuales; no tomes una escena antigua ni este documento como prueba del estado instalado. Aplica `minibiomes.md` a la composición, no copies una plataforma plana cambiando su ID.
- Comprueba versión del servidor, runtime, formato del pack, IDs y estados de bloques. Si el destino no soporta la versión requerida, informa la incompatibilidad; no actualices servidor/mundo silenciosamente. Una prueba explícita sobre una versión histórica debe identificarse como tal, no como contenido nuevo validado para 26.1.
- Declara dimension y límites reales de escritura, limpieza, chunks y cámara. Una zona de control no limita los `fill`; comprobar solapamientos entre sets. Respalda el mundo con el servidor parado antes de reemplazar construcciones; no uses `down -v` ni borres fuera de la zona reservada.
- El plan Markdown de cada escena incluye: **atmósfera, composición, acción, hora, clima, dificultad/reglas, riesgos, snapshot/restauración y estado visual**. No cambies el JSON estricto de familia para transportarlo. Reutiliza una tabla simple del generador para presets; no inventes coordenadas con un modelo.

### Contextos concretos

| escena | contexto y composición | acción/riesgo |
| --- | --- | --- |
| f02 armas | crepúsculo congelado, ruinas, barricadas, cicatrices y árboles dañados fuera de una arena despejada | dummy real y ruta de ataque libre; sin mobs automáticos, fuego, TNT ni pérdida forzada de inventario |
| f03 luz | noche congelada, santuario sobrio de piedra cubierto, baffle de entrada y pedestales sin bloques emisivos | el jugador coloca la luz real y compara antes/después; comprobar techo/volumen y no prometer nivel de luz o captura sin ensayo |
| f04 cultivo | día congelado, ribera tranquila, parcela con agua, arena de almas y arena separadas | wart solo en arena de almas y caña junto al agua; no sugerir que crecen naturalmente juntas |

Captura una vez, antes del primer preset, solo los valores que se modifican. Restaura en `stop`/liberación y tras fallo de setup; no sobrescribas el snapshot al cambiar escena. Si no hay una API/consulta reversible para clima o dificultad, no los cambies y documenta el límite. En Java 1.21.11 verifica los IDs contra el servidor actual: los usados aquí son `minecraft:advance_time` y `minecraft:spawn_mobs` (snake_case); no supongas nombres camelCase. Reload/crash puede dejar el preset activo: conserva el snapshot y requiere una liberación explícita, no restablezcas reglas a ciegas al cargar.

## Construcción acotada

1. Calcula chunks afectados y bloques por comando según los límites de la versión/configuración real. No fuerces miles de chunks ni eleves límites globales para una toma pequeña. Divide en lotes y libera solo las cargas añadidas por esta prueba.
2. Limpia únicamente bloques/entidades propiedad del set en su caja autorizada. Construye base y volumen, superficie con relieve, elementos funcionales, vegetación sobre altura final y detalles, en ese orden. Reutiliza helpers existentes si resuelven esas operaciones.
3. Usa variación determinista; verifica soporte de plantas, agua, hojas y bloques afectados por gravedad. Mantén libres cámara y recorrido del actor. Las coordenadas de adornos deben seguir la superficie final, no una Y fija heredada.
4. Señala listo después del último lote ejecutado; un `schedule` o una espera fija no prueba que `fill`/`forceload` funcionaron. Revisa errores de carga, comandos y chunks en logs/consola. No confundas segundos, ticks y frames de vídeo.
5. Reset debe cancelar tareas pendientes, asegurar chunks requeridos y restaurar estado reproducible; su firma incluye revisión de generador/contenido y escena, además de semilla/origen/pitch. Una firma vieja obliga build completo. Cambiar escena no puede encadenar varias selecciones en la misma llamada. No teletransportes jugadores ajenos; conserva bloqueos/propiedad existentes. La ejecución interna/consola no puede saltar el claim de propietario.

## Ensayo y entrega

Ejecuta tests del generador y valida referencias del datapack. Después verifica dentro del servidor: setup dos veces, acción, reset, cambio de escena y stop; sin restos, tareas tardías ni cargas abandonadas. Consulta primero jugador/owner/escena: no hagas reload o setup sobre una toma activa. Montar archivos no demuestra que Minecraft aceptó las funciones.

Revisa desde la cámara prevista los criterios de `minibiomes.md`, con capturas reales y overlays cuando corresponda. Replay Mod es del cliente: especifica por separado construcción, actuación manual, cámara y exportación. Entrega versión, comandos realmente instalados, resultado de tests/logs y lo que falta ensayar. No declares render, mecánica o calidad visual aprobados por un PASS estructural.
