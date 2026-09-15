# Studio de paisajes Minecraft

Servidor Fabric local **Java 1.21.11**, datapack formato 81. La geometria se compila con Python estandar: no requiere IA para colocar bloques, mods de terreno ni servicios externos. Replay Mod y la captura siguen siendo tareas del cliente.

## Generacion reproducible

`landscape.py` define tres composiciones de 192x192 bloques. Cada columna tiene relleno desde Y-63 hasta la superficie; los bordes se unen al superflat en Y72 y la zona de accion queda a Y80. No se cambia el generador del mundo existente.

| ID | Paisaje | Prueba manual |
| --- | --- | --- |
| f02 | Colinas de robles, claro de entrenamiento, arco en ruinas y rocas apoyadas | Mace y trident frente a un dummy; reset lo repone |
| f03 | Macizo rocoso con abetos y santuario excavado, fachada, techo y pedestal | Colocar sea lantern y soul lantern; reset retira la luz anterior |
| f04 | Ribera curva contenida, abedules, puente y terraza de cultivos | Nether wart en arena de almas y sugar cane junto al canal de riego |

El generador resuelve relieve suave, transicion del claro, especies con copas diferentes, grupos de arboles y soporte de adornos. La semilla modifica variacion y distribucion sin cambiar la funcion de la escena. Las pruebas no certifican la verdad de pistas ni la calidad de una captura.

Desde la raiz del repositorio:

```powershell
docker compose -f Server/docker-compose.yaml run --rm --build studio-builder validate
docker compose -f Server/docker-compose.yaml run --rm studio-builder build --origin 120 1100 --pitch 1152 --seed 20260915
docker compose -f Server/docker-compose.yaml up -d mc
```

Esta es la ubicacion de la prueba nueva: f02 `(120,1100)`, f03 `(1272,1100)`, f04 `(2424,1100)`. Se eligio Z1100 para no reconstruir encima de los pisos antiguos. `build` solo escribe el datapack; el `setup` dentro de Minecraft construye el paisaje.

- `--origin X Z`: esquina de referencia del claro de f02. Omitirlo usa el origen historico `(120,14)`, no la ubicacion de prueba nueva.
- `--pitch N`: distancia entre escenas, minimo 192; por defecto 1152 para conservar la separacion historica. No agranda el bioma.
- `--seed N`: misma semilla y coordenadas producen los mismos bloques. Por defecto 20260915.

`Server/generated/studio/manifest.json` registra semilla, origen, limites, alturas, arboles, ticks y puntos de comprobacion con bloques esperados. Cada caja escribe X/Z `origen-96..origen+95` y Y `-63..143`. **Setup reemplaza todo ese volumen**, no solo el claro: usa un espacio reservado sin construcciones que quieras conservar. No trasladar un diseño a terreno normal sin revisar alturas y limites.

## Seguridad y respaldo

Antes de reemplazar escenas, para `mc` y respalda `Server/data/world` y el datapack generado en otra carpeta. No uses `down -v` ni borres `Server/data`. El respaldo previo a esta implementacion se guardo en `C:\Users\brian\AppData\Local\Temp\opencode\whatamicraft-before-landscapes-20260915-01.tar.gz`; contiene el mundo y su datapack anterior. El despliegue no borra los pisos viejos fuera de las cajas nuevas.

El servicio escucha solo en `127.0.0.1:25565`, con RCON apagado. `ONLINE_MODE: "FALSE"` no autentica identidades: no publiques el puerto. La consola por pipe solo es accesible mediante Docker local; no abre otro puerto. El mundo no pausa vacio para permitir construcciones por consola.

## Comandos en el juego

Conecta Java 1.21.11 a `localhost:25565` como OP. Tras regenerar el datapack usa `/reload`; despues selecciona una escena y espera el aviso listo:

```mcfunction
/function studio:help
/function studio:scene/f02/setup
/function studio:start
/function studio:reset
/function studio:next
/function studio:stop
```

Usa `scene/f03/setup` o `scene/f04/setup` para elegir directamente. `start` coloca al operador en el claro antes de cambiar modo y agrega el kit **sin borrar su inventario**. f02 usa survival: los golpes y la durabilidad son reales, y el dummy puede romperse. f03/f04 usan creativo.

`reset` reconstruye terreno, plantas y estructura; cancela la construccion pendiente y retira solo dummies etiquetados de esa caja. `next` selecciona una sola escena. `stop` cancela tareas y libera solo chunks adquiridos por el studio, sin demoler el paisaje. Las cargas previas de terceros se conservan, incluso si se reconstruye el pack con otro origen.

Solo un operador controla el studio; su identificador de sesion persiste si se desconecta. Un OP puede usar `/function studio:admin/release` tras confirmar que no interrumpe su toma. Un tag antiguo no autoriza al propietario anterior. Para entrar a una escena ya construida por consola, usa `/function studio:start` (no hace falta reconstruirla).

La construccion comprueba que los chunks cargaron, luego ejecuta un tick numerado por tick de juego (hasta 200 comandos y 32768 bloques por tick) repartidos en tres archivos encadenados por escena (`build0`/`build1`/`build2` de ~26.000 lineas cada uno): una pasada del juego no evalua mas lineas que su limite interno de 65536 comandos. Se mantienen como maximo 169 chunks por escena activa. El tiempo depende del servidor (unos minutos por escena). Solo se anuncia listo al terminar y coincidir los puntos de comprobacion.

```mcfunction
/scoreboard players get #ready studio_ready
/scoreboard players get #checks studio_ready
```

`#ready`: 0 construyendo, 1 listo, -1 fallo (chunks o puntos de comprobacion). Si falla, revisa logs y vuelve a ejecutar setup. Por escena existen `setup`, `start` y `reset` (mas `build0`/`build1`/`build2` internos encadenados): no los llames a mano para saltarte las comprobaciones.

## Verificacion

```powershell
docker compose -f Server/docker-compose.yaml run --rm --entrypoint python studio-builder -m unittest discover -s tests -v
docker exec -u 1000 server-mc-1 mc-send-to-console "function studio:scene/f02/setup"
docker exec -u 1000 server-mc-1 mc-send-to-console "scoreboard players get #ready studio_ready"
docker logs --tail 30 server-mc-1
```

La consola solo inicia setups sin un operador reclamado; no mueve jugadores ajenos. Las pruebas cubren continuidad del suelo, relieve, semillas, colocacion de arboles, contencion de agua, riego, limites por tick, referencias de funciones y cancelacion. Repetir setup/reset en Minecraft y revisar desde el cliente real sigue siendo necesario para juzgar la imagen, sombras y colisiones.
