# Integrar En El Servidor

Leer solo cuando el usuario pide implementar, no para proponer o explicar escenas.

## Fuentes Y Limites

- `docs/scenes/<ID>.json`: brief de diseno, NO lo consume el servidor. Validarlo no instala funciones.
- `docs/minecraft-clip-library.md`: guion tecnico/SET historico; leer solo ID solicitado.
- `docs/minecraft-clip-shooting-guide.md`: acciones humanas y camaras por ID.
- `Server/scene_controller.py`: fuente ejecutable actual (`SETS`, `DURATIONS`, `CHUNKS`, eventos y controles). Prima para sintaxis del datapack sobre ejemplos historicos de comandos.
- `Server/generated/studio/`: generado por `build`; nunca editar manualmente.
- `Server/tests/test_studio.py`: contratos actuales. Hoy restringe G01-G10; G11/C01 no se registran solo por crear un brief. Revisar validacion, orden, controles y zona disponible al extender IDs.

Conservar carpeta `Server` con mayuscula. En Windows `Server` y `server` son la misma carpeta: nunca eliminar uno como duplicado. No tocar `Server/data`, produccion, credenciales ni contenedores en marcha durante diseno.

## Procedimiento

1. Revisar el ID, SET y rama de evento elegidos. Para nueva escena, confirmar ubicacion libre y limites del laboratorio; no reusar coordenadas ocupadas.
2. Adaptar fuente Python, duracion y chunks. No copiar motor completo de control ni crear otro puente RCON.
3. Revisar setup repetido, reset durante/tras accion, cambio a otra escena, desconexion del operador y cancelacion de callbacks. No eliminar entidades ni forceloads ajenos.
4. Generar y probar sin iniciar Minecraft ni modificar el mundo. Si usa Docker, comprobar que el montaje de herramienta apunta a `Server/`.
5. Actualizar solo brief/ficha afectados con diferencias entre servidor y rodaje manual. Informar ensayo visual pendiente.

## Errores Que No Repetir

- `/schedule` pierde el ejecutor jugador; resolver propietario y dimension antes de usar `@s`.
- `next` debe seleccionar una sola escena, no reevaluar todos los IDs despues de cambiar el score.
- `/forceload` recibe coordenadas de BLOQUES, no indices de chunk: `block = chunk * 16`; negativos usan floor. Esperar carga y comprobar estado antes de construir.
- Limpiar panel/piston/head antes de reconstruir G07. Limpiar solo mob etiquetado de G09 antes de invocar otro.
- Flecha es item/entidad, no bloque. Dispensador: `item replace block ... container.0 with minecraft:arrow 64`.
- No inventar propiedades `half` de piston, `facing` de placa de presion ni comandos de Replay Mod. Verificar sintaxis Minecraft 1.21.11 antes de generar.

## Comprobaciones Desde La Raiz

```powershell
docker compose -f Server/docker-compose.yaml run --rm --build studio-builder validate
docker compose -f Server/docker-compose.yaml run --rm studio-builder build
docker compose -f Server/docker-compose.yaml run --rm --entrypoint sh studio-builder -c "python -m unittest discover -s tests -v"
docker compose -f Server/docker-compose.yaml config --quiet
```

Estas pruebas son estructurales; no prueban colisiones, tiempos reales, carga correcta de todos los comandos ni resultado visual. No subir estado del brief por aprobarlas.
