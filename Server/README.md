# Studio de rodaje Minecraft

Servidor Fabric aislado para **Java 1.21.11** y un datapack vanilla nativo. Replay Mod se instala solamente en el cliente de grabacion; el servidor no intenta controlar camaras, animaciones ni renders.

## Arranque (PowerShell, desde la raiz del repo)

```powershell
docker compose -f Server/docker-compose.yaml run --rm --build studio-builder validate
docker compose -f Server/docker-compose.yaml run --rm --build studio-builder build
docker compose -f Server/docker-compose.yaml up -d
docker compose -f Server/docker-compose.yaml logs -f mc
```

Conecta el cliente Java 1.21.11 a `localhost`. El puerto solo escucha en localhost; la configuracion local actual usa `ONLINE_MODE: "FALSE"` y RCON desactivado. En este modo no se autentican identidades de jugadores: no publiques el puerto ni lo expongas mediante tuneles. Para un servidor compartido, activa `ONLINE_MODE: "TRUE"` antes de habilitar acceso externo. Para parar sin borrar el mundo:

```powershell
docker compose -f Server/docker-compose.yaml down
# Nunca uses `down -v`; Server/data contiene el mundo persistente.
```

Antes de un rodaje, con el contenedor parado, copia `Server/data/world` a una carpeta de backup fuera de `Server/data`. No borres ni renombres `Server/data` (en Windows `Server` y `server` son el mismo directorio).

`Server/generated/` no se versiona: el paso `studio-builder build` es obligatorio en un clon nuevo antes de arrancar `mc`. Genera el datapack desde la fuente Python; no copia mundos ni credenciales.

## Operacion dentro del juego

Un operador debe estar en la zona reservada del laboratorio (Overworld, x -16..384, y 64..144, z -32..32) y tener permisos de operador. El pack no se ejecuta automaticamente: despues de `build`, entra al mundo y ejecuta `/reload` una vez si el servidor ya estaba encendido. Primero usa creativo y `/tp @s 0 90 -8`; despues ejecuta `claim`. RCON queda desactivado; para bootstrap de OP usa la consola local con `docker compose -f Server/docker-compose.yaml attach mc`, escribe `op TuJugador`, y separa con `Ctrl-P`, `Ctrl-Q` sin parar el servidor.

```mcfunction
/function studio:help
/function studio:claim
/function studio:scene/g11/setup
/function studio:scene/f02/setup
/function studio:start
/function studio:reset
/function studio:next
/function studio:stop
```

`claim` crea un bloqueo persistente por ID de scoreboard, incluso si el operador se desconecta. Si ese operador no puede volver, un OP que haya confirmado que esta offline puede ejecutar `/function studio:admin/release`. `setup` selecciona, forceloads y construye solo su caja reservada antes de avisar que esta lista. `start` marca el inicio de la toma y `reset` reconstruye el SET completo de la escena activa. `stop` cancela tareas, resetea, y elimina solamente el forceload de la caja de estudio activa. `next` usa retorno temprano y prepara exactamente una escena posterior G11..G13,F02..F04.

F02, F03 y F04 son escenarios neutros de prueba para las familias F02 (mace/trident), F03 (lectern/composter) y F04 (crossbow/fishing_rod): universos `provisional`, sin captura vanilla ni prueba mecanica. La actuacion es manual; el usuario sostiene y muestra los items el mismo.

G11, G12 y G13 requieren actuacion natural del jugador: no hay eventos automaticos. Las construcciones de G01..G10 ya no estan registradas; si quedan restos fisicos de sets viejos en el mundo, se limpian a mano o se regenera la zona con un nuevo `setup`.

Los SETs son las transcripciones estructuradas de `docs/minecraft-clip-library.md`; la guia de camara y las limitaciones de Replay Mod estan en `docs/minecraft-clip-shooting-guide.md`. Graba la accion real y decide las rutas de camara despues en Replay Mod: no hay API de Replay Mod ni bot en este proyecto.

## Comprobaciones

```powershell
docker compose -f Server/docker-compose.yaml run --rm --entrypoint sh studio-builder -c "python -m unittest discover -s tests -v"
docker compose -f Server/docker-compose.yaml config
```

Las pruebas validan el mapeo G01--G10, duraciones, referencias de funciones, resets/tareas programadas y el aislamiento del compose. No sustituyen un ensayo visual o de colisiones en Minecraft.
