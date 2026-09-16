# Implementación y prueba

Lee este recurso únicamente cuando el usuario autoriza crear, implementar, instalar o probar. Diseñar o revisar no autoriza cambios en Server, Docker ni mundo. Aplica primero `minibiomes.md`.

## Estado vivo antes de editar

No uses ejemplos históricos como estado actual. Lee:

1. `Server/scene_controller.py`: IDs, origen, seed, kits, contexto y ciclo de vida.
2. `Server/landscape.py`: geometría y features reales.
3. `Server/generated/studio/manifest.json`: límites, checkpoints, revisión y assets instalados.
4. `Server/generated/studio/asset_catalog.json` o `Server/catalogs/all_assets.json`: tags, tamaños y fuentes.
5. `Server/docker-compose.yaml` y `Server/README.md`: versión, mounts y comandos.
6. `Server/tests/`: comportamiento que ya está protegido.

Registra la versión real por prueba. No migres servidor, mundo, formato de pack ni contenido silenciosamente.

## Alcance de implementación

- **Blockout:** masas, volumen, acceso, recorrido, cámara y foco. Materiales simples; sin assets decorativos ni microdetalle.
- **Detalle:** conserva blockout, cámara y acción aprobados. Añade paleta, vegetación, assets, sonido y acentos pertinentes.
- **Prueba técnica:** compila, valida manifest/referencias y carga el datapack; no construye una escena sin autorización para setup.
- **Prueba en mundo:** setup/reset/acción/stop dentro de la caja autorizada. Requiere respaldo y ausencia de una toma activa.

No mezcles etapas para ahorrar una revisión. Una escena rectangular detallada sigue siendo una escena rectangular.

## Seguridad

- Declara dimensión, caja X/Y/Z, chunks, cámara, recorrido y limpieza. Comprueba solapamientos entre sets.
- Antes de setup destructivo, detén o consulta el estado del operador, para el servidor si el respaldo lo requiere y respalda `Server/data/world` y el datapack.
- Nunca uses `down -v`, borres `Server/data` ni limpies fuera de la caja reservada.
- No teletransportes jugadores ajenos. Conserva claim, owner y cargas previas de terceros.
- Captura una sola vez los valores de contexto modificados y restaura en `stop`, liberación y fallo. No restablezcas reglas a ciegas tras reload/crash.
- Un montaje o `/reload` no autoriza `setup`.

## Construcción

1. Reutiliza helpers existentes; no copies miles de comandos ni inventes coordenadas de cada árbol.
2. Construye base, masas/volumen, superficie, elementos funcionales, assets grandes y detalle, en ese orden.
3. Usa variación determinista y registra seed/origen/revisión.
4. Coloca decoración sobre altura final y verifica soporte, gravedad, agua, hojas y colisiones.
5. Mantén libres cámara, línea visual, recorrido y zona de acción.
6. Filtra assets por política semántica, tamaño y zona antes de leer/colocar estructuras. Si no hay candidato, usa ninguno.
7. Divide por límites reales de comandos/bloques. Señala listo solo tras último lote y checkpoints.
8. Reset cancela tareas, asegura chunks y compara firma completa; una revisión distinta obliga build completo.

## Pruebas automáticas

Ejecuta las pruebas existentes y añade la prueba mínima que falle por el cambio. Cubre según aplique:

- continuidad de base, límites y volumen de `fill`;
- recorrido con suelo y dos bloques de aire;
- línea cámara-foco;
- ausencia de peligros no pedidos en la acción;
- techo/oclusión de cielo en cuevas;
- contención de agua y soporte de plantas;
- tags, tamaño, cantidad, exclusiones y zonas de assets en manifest;
- referencias de funciones y cancelación de schedules;
- setup/reset repetibles y checkpoints finales.

Los checks de un bloque no demuestran naturalidad. Para formas orgánicas prueba también variación de planta, anchura o techo; una gran caja de aire con cuatro estalactitas no pasa como cueva.

## Secuencia de verificación

1. Ejecuta unit tests del generador y skill.
2. Compila el datapack.
3. Revisa `manifest.json`: límites, comandos, assets, tags, fuentes y checkpoints.
4. Confirma que Docker ve exactamente las escenas y estructuras esperadas.
5. Consulta owner/escena activa antes de `/reload` o setup.
6. Recarga y revisa logs por funciones, IDs o estados rechazados.
7. Si fue autorizado: setup dos veces, recorrido, acción, reset, cambio de escena y stop.
8. Captura entrada, cámara principal, acción/consecuencia, lateral y 9:16 con overlays.

Entrega por separado:

- versión y comandos realmente ejecutados;
- tests y logs;
- manifest y política de assets;
- observaciones por captura;
- pendientes técnicos;
- `visual_pending` mientras falte revisión desde cliente.

Replay Mod pertenece al cliente. Construcción, actuación, cámara y exportación son etapas distintas. No declares render, mecánica ni calidad visual aprobados por un PASS estructural.
