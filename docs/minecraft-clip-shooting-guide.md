# Guia operativa: grabar escena a escena

**Abri este archivo mientras grabas.** La [biblioteca tecnica](minecraft-clip-library.md) queda como referencia de construccion, comandos y encuadre. Estas fichas convierten las diez escenas generales en una lista de acciones, sin pedir una grabacion por item.

Estado: instrucciones para ensayo en Java 1.21.11. No hay replays ni renders aprobados todavia. Las coordenadas son puntos de partida revisados sobre el papel; comprobar colisiones y encuadre en juego antes de una toma definitiva.

## Antes de empezar

1. Usa un mundo de rodaje descartable, nunca tu mundo importante. Los comandos de construccion modifican bloques.
2. Comprueba Java 1.21.11, Replay Mod compatible y FFmpeg configurado en la maquina que exporta. Haz una prueba MP4 corta antes de construir todo.
3. Ejecuta [BASE](minecraft-clip-library.md#base-antes-de-construir) y despues solo el `SET` de la ficha elegida. Introduce los comandos uno por uno en el chat; no son un comando multilinea. Si llegas desde otra dimension, vuelve a Overworld primero.
4. Mantene vanilla, dia 6000 y clima claro. Sin musica, texto, nombres, overlays ni particulas artificiales en captura. El archivo final debe funcionar mudo.
5. Graba al jugador desde tu partida normal. Despues, en Replay Mod, elegis la camara externa: **no necesitas otra persona que filme**. La camara libre no controla mobs ni acciona mecanismos.
6. Deja 3 segundos quietos antes de actuar y 3 segundos despues de terminar. Son margenes del replay, no segundos vacios para poner al principio del video final.
7. Hace primero la accion a velocidad normal. No intentes pulsar teclas en un frame exacto: despues selecciona el inicio del clip para que el evento aparezca antes de 1.5 segundos.

**Vocabulario:** `t=0` es el inicio del archivo final; `f` son frames de video a 30 fps, no ticks del juego. `P` es posicion de camara; `T` es tiempo del replay. Por ejemplo, `P0/P6 fijos` significa crear dos keyframes de posicion iguales en t=0 y t=6. Tambien necesitas los keyframes temporales que hagan avanzar seis segundos de la grabacion.

**Exportacion comun:** 1080x1920, 30 fps constantes, H.264 MP4, sin musica ni texto; HUD, hotbar, crosshair, chat, coordenadas, nombres, inventario y subtitulos ocultos en la salida. FOV constante. Foley/sonido de juego por separado si se conserva. No shaders hasta aprobar la version limpia.

## Que ficha abrir

Orden recomendado por sencillez, no por posicion dentro del video:

| Orden | Ficha | Funcion | Archivo de uso |
|---:|---|---|---|
| 1 | [G02 Decision](#g02-decision) | Elegir entre opciones | 6 s / 180 f |
| 2 | [G10 Reaccion](#g10-reaccion) | Cierre humano sin target | 4 s / 120 f |
| 3 | [G01 Descubrimiento](#g01-descubrimiento) | Abrir algo sin mostrar contenido | 6 s / 180 f |
| 4 | [G08 Busqueda](#g08-busqueda) | Inspeccionar lugares | 6 s / 180 f |
| 5 | [G04 Recuperacion](#g04-recuperacion) | Fallo aparente que se resuelve | 5 s / 150 f |
| 6 | [G06 Escala](#g06-escala) | Descubrir un espacio grande | 6 s / 180 f |
| 7 | [G07 Apertura](#g07-apertura) | Dejar lugar para cualquier respuesta | 6 s / 180 f |
| 8 | [G03 Peligro](#g03-peligro) | Suelo que falla delante del jugador | 5 s / 150 f |
| 9 | [G05 Esquiva](#g05-esquiva) | Pasada cercana y resultado | 2 fuentes: 30 + 90 f |
| 10 | [G09 Aparicion](#g09-aparicion) | Descubrir presencia tras esquina | 5 s / 150 f |

Las partes 1/2/3 de cada tabla son momentos de **una misma actuacion continua**, no tres capturas independientes. Excepcion G05: una actuacion y dos camaras exportadas por separado; el corte se hace en Remotion.

## G01: Descubrimiento

**Reuso del mismo archivo:** pregunta sobre herramientas, comida o minerales. Es misterio narrativo; no significa que esos objetos se obtengan en ese cofre. No cambiar su contenido por episodio.

**Prepara:** un cofre vacio, plataforma y pared neutra. Sin mobs, equipo ni item visible en mano. Construccion: [SET-G01](minecraft-clip-library.md#set-g01-cofre-sin-respuesta).

**Antes de grabar:** colocate en `(0.5,81,-0.5)`, mirando al cofre. Comprueba que la tapa puede abrir. Deja 3 s de margen con cofre cerrado.

| Parte | Tiempo de salida | Lo que haces jugando | Lo que debe verse |
|---|---|---|---|
| 1 | 0-1 s / f0-29 | Usa el cofre una vez para abrirlo. | La tapa se levanta antes de f30. |
| 2 | 1-4 s / f30-119 | Deja la interfaz abierta; no muevas items ni al jugador. | Cofre abierto, sin revelar contenido; la GUI no sale en replay. |
| 3 | 4-6 s / f120-179 | Cierra la interfaz y quedate quieto. | La tapa vuelve a bajar; final limpio. |

**Despues, en Replay Mod:** camara oblicua en `(3,82.5,-4.5)`, mirar `(0.5,81.6,0.5)`, FOV 50. Mantener P0/P1 iguales; acercar lente 0.4 bloques entre t=1 y t=4; mantener P4/P6 iguales. Usar interpolacion lineal y tiempo real. El cuerpo no debe tapar tapa/bisagra. Texto futuro arriba; no entrar visualmente dentro del cofre.

**Exporta:** `mc_discovery_container_open_thirdoblique_vanilla_scene_t01.mp4`, 180 f. No loop. No agregar un premio en Minecraft; Remotion aporta la respuesta independiente.

**Repite si:** tapa tapada por cuerpo, GUI visible, item de respuesta reconocible o apertura posterior a 1.5 s. **Reset:** cerrar cofre y volver a marca. **Intentos orientativos:** 2-4.

## G02: Decision

**Reuso del mismo archivo:** decidir una respuesta de bloques, pociones o armaduras; los pasillos no representan recetas ni categorias concretas.

**Prepara:** dos accesos iguales y un divisor. Nada de iconos, carteles, colores rojo/verde ni props de respuesta. [SET-G02](minecraft-clip-library.md#set-g02-decision-entre-rutas).

**Antes de grabar:** colocate en `(40.5,81,-1.5)` mirando hacia los accesos (+Z). Mano vacia. Ensaya una falsa eleccion izquierda y termina a la derecha, sin entrar en el divisor.

| Parte | Tiempo de salida | Lo que haces jugando | Lo que debe verse |
|---|---|---|---|
| 1 | 0-1 s / f0-29 | Mira a izquierda y despues a derecha, con giros claros de unos 35 grados. | Duda desde el primer segundo; ambas entradas visibles. |
| 2 | 1-4 s / f30-119 | Da un paso corto hacia izquierda, frena y avanza por derecha hasta `(42.5,81,1.5)`. | Cambio de decision sin teletransportes ni carrera excesiva. |
| 3 | 4-6 s / f120-179 | Quedate en el umbral derecho mirando hacia dentro. | Eleccion hecha, sin mostrar si era correcta. |

**Despues, en Replay Mod:** camara trasera elevada `(40.5,85,-8)`, mirar `(40.5,82,1)`, FOV 60. P0/P6 iguales y T0/T6 a velocidad real. Sin paneo ni zoom. El cuerpo y las dos opciones deben caber en vertical. Esta es la version `scene`.

**Exporta:** `mc_decision_routes_choose_thirdrear_vanilla_scene_t01.mp4`, 180 f, no loop. El fondo bajo es una variante posterior: [ver camara tecnica de G02](minecraft-clip-library.md#g02-elegir-sin-saber). No usar el encuadre central detras de la tarjeta opaca de pistas.

**Repite si:** solo se ve una entrada, te chocas con divisor, no se percibe duda o cuerpo queda diminuto. **Reset:** repetir solo teleport de SET-G02. **Intentos:** 3-5.

## G03: Peligro

**Reuso del mismo archivo:** tension antes de resolver preguntas de herramientas, comida o pociones. La caida pertenece al escenario; no es una habilidad del item.

**Prepara:** borde firme, foso corto y arena sobre soporte. [SET-G03 y trigger/reset](minecraft-clip-library.md#set-g03-desprendimiento-escenografico). Nadie sobre la arena; el jugador permanece x<=79.

**Antes de grabar:** prueba el trigger SIN jugador cerca. Reconstrui soporte y arena. Colocate en `(79,81,1.5)`, sobre piedra firme mirando al hueco, y deja margen de grabacion.

| Parte | Tiempo de salida | Lo que haces jugando | Lo que debe verse |
|---|---|---|---|
| 1 | 0-1 s / f0-29 | Ejecuta una vez el trigger de SET-G03 para retirar soporte. Es puesta en escena por comando. | Arena se desprende delante del jugador antes de 1.5 s. |
| 2 | 1-3 s / f30-89 | Retrocede un bloque hasta x cercano a 78, siempre sobre firme. | Hueco real, bloques cayendo y retirada segura. |
| 3 | 3-5 s / f90-149 | Mira abajo y quedate quieto. | Resultado estable; no muerte ni objeto salvador. |

**Despues, en Replay Mod:** camara `(81.5,84,-8)`, mirar `(80.5,79.5,1.5)`, FOV 60. P0/P5 fijos, tiempo real. Debe verse el firme bajo los pies y el fondo del foso. Si usaste chat para el trigger, no incluir la GUI en salida ni presentar el comando como poder del target.

**Exporta:** `mc_danger_floor_collapse_thirdside_vanilla_scene_t01.mp4`, 150 f, sin loop ni explosion artificial.

**Repite si:** jugador pisa arena, soporte se retira antes de grabar, foso queda negro o no se ve diferencia entre firme y hueco. **Reset:** espera que termine la caida; ejecuta SOLO reset local de SET-G03. **Intentos:** 3-6.

## G04: Recuperacion

**Reuso del mismo archivo:** expectativa/acierto en episodios de bloques, minerales o comida. El jugador se salva con otro salto normal, no con equipo del target.

**Prepara:** dos plataformas, cornisa un bloque mas baja y suelo inferior. [SET-G04](minecraft-clip-library.md#set-g04-salto-basico). Supervivencia, sin efectos ni equipo especial.

**Antes de grabar:** ensaya la ruta a velocidad normal: primer salto corto a cornisa `(122.5,80,1.5)`; segundo salto a `(124.5,81,1.5)`. No hace falta un salto maximo. Si no sale, ajusta montaje antes de rodar y registra cambio.

| Parte | Tiempo de salida | Lo que haces jugando | Lo que debe verse |
|---|---|---|---|
| 1 | 0-1 s / f0-29 | Desde borde izquierdo haz salto corto, sin sprint, hacia cornisa inferior. | Parece que falta distancia; pies encuentran apoyo real. |
| 2 | 1-3 s / f30-89 | Una vez apoyado, salta a plataforma alta y frena. | Dos apoyos separados; recuperacion sin corte engañoso. |
| 3 | 3-5 s / f90-149 | Gira un poco hacia hueco, agachate una vez y quedate quieto. | Remate de alivio. |

**Despues, en Replay Mod:** camara lateral `(122,83,-8)`, mirar `(122,81.8,1.5)`, FOV 60. P0/P5 fijos. Elige T0 en primer despegue, dejando carrera previa fuera. Deben entrar ambos bordes y cornisa. No ocultar primer apoyo para fingir que el jugador se agarra de las manos.

**Exporta:** `mc_motion_gap_jump_thirdside_vanilla_scene_t01.mp4`, 150 f, no loop. No crear la corta si elimina uno de los dos apoyos necesarios para entenderlo.

**Repite si:** falta apoyo, jugador cae al suelo inferior, necesita vuelo/efectos o no termina en plataforma. **Reset:** teleport al inicio, comprobar salud. **Intentos:** 4-8.

## G05: Esquiva

**Reuso del mismo archivo:** tension en preguntas de bloques, alimentos o equipo como situacion narrativa. No implica que esos targets disparen flechas. Excluir si la propia flecha, el dispensador o su sonido revelan la respuesta.

**Prepara:** dispensador con flechas, pared receptora y carril lateral seguro. [SET-G05 y pulso individual](minecraft-clip-library.md#set-g05-linea-de-proyectil-controlada). Hay una actuacion, dos camaras y dos archivos; no pedir un ayudante que filme.

**Antes de grabar:** prueba trayectoria sin jugador. Reconstrui estado inicial, deja el trigger sin energia, colocate en `(160.5,81,1.8)` mirando -X. Tu carril es z>=1.8, apartado del eje de flechas z cercano a 0.5. El modo creativo no prueba que hayas esquivado: el replay debe mostrar ausencia de contacto.

| Parte | Tiempo de montaje | Lo que haces jugando | Lo que debe verse |
|---|---|---|---|
| 1 | 0-1 s / f0-29 | Dispara un pulso de SET-G05. Cierra chat y da un paso hacia +Z (izquierda si miras -X), sin cruzar linea de tiro. | Flecha pasa cerca de camara A y jugador se aparta. |
| 2 | 1-2 s / f30-59 | Quedate a salvo; gira la cabeza hacia pared si corresponde. | Desde camara B, flecha ya clavada. |
| 3 | 2-4 s / f60-119 | No hagas un segundo disparo; mantene resultado. | Pared e impacto estables. |

**Despues, en Replay Mod:** A en `(164,82.6,1.2)`, mirar `(156.5,82.3,0.5)`, FOV 65, fija. B en `(161.5,83,-6)`, mirar `(165,82.2,0.5)`, FOV 55, fija. No unirlas por spline: la pared esta detras de A. Elegir un intervalo real continuo; A muestra primer segundo, B los tres siguientes. Si vuelo o reaccion no coinciden, repetir ensayo o ajustar limites y actualizar metadatos; no inventar tiempo de vuelo.

**Exporta A:** `mc_danger_projectile_dodge_thirdoblique_vanilla_pass_t01.mp4`, 30 f.

**Exporta B:** `mc_danger_projectile_dodge_thirdside_vanilla_result_t01.mp4`, 90 f. Corte posterior en Remotion; sin fundido ni transicion horneados.

**Repite si:** proyectil invisible, contacto con jugador, fuente/GUI de comando tapa la accion o B no muestra flecha. **Reset:** retirar energia del trigger, limpiar solo flechas de SET-G05 y volver a marca. **Intentos:** 5-10. Si un operador solo no logra reaccion legible, grabar mas intentos; no ocultar el fallo con shake.

## G06: Escala

**Reuso del mismo archivo:** asombro antes de respuestas de minerales, armaduras o comida; no es una afirmacion del tamaño fisico del target.

**Prepara:** torre/columna abstracta, borde de oclusion y jugador para comparar tamaño. [SET-G06](minecraft-clip-library.md#set-g06-construccion-abstracta-de-escala). Nada de esculturas de items.

**Antes de grabar:** colocate en `(199,81,7)`, delante de la base, no dentro de bloques. Carga todo el escenario. Esta toma depende de camara posterior, no de una actuacion complicada.

| Parte | Tiempo de salida | Lo que haces jugando | Lo que debe verse en replay |
|---|---|---|---|
| 1 | 0-1 s / f0-29 | Quedate quieto junto a base. | La camara sale del borde cercano y descubre la estructura. |
| 2 | 1-4 s / f30-119 | Sigue quieto para dar referencia de escala. | Base, figura y coronacion visibles a la vez. |
| 3 | 4-6 s / f120-179 | Levanta levemente la mirada y mantenela. | Remate de asombro, sin movimiento extra. |

**Despues, en Replay Mod:** P0 `(197,89,-14)`, P1 `(199,89,-14)`, mirando `(200.5,91,8.5)`, FOV 65. Entre t=1 y t=4 podes subir 0.5 bloques solo si no corta base; P4/P6 iguales. Usa linea clara fuera de pared, no orbita. Si la torre no cabe, ajusta distancia antes de render final, no recortes la figura humana.

**Exporta:** `mc_scale_structure_reveal_thirdfree_vanilla_scene_t01.mp4`, 180 f. Vanilla primero, sin loop. Shader suave solamente como variante posterior si conserva lectura.

**Repite si:** figura dentro de bloques, cima/base cortadas, chunks vacios o no cambia oclusion en primer segundo. **Reset:** posicion del jugador; no reconstruir. **Intentos:** 2-4 rutas de camara.

## G07: Apertura

**Reuso del mismo archivo:** reveal de cualquier respuesta de herramientas, alimentos o bloques. El espacio queda vacio; icono y nombre se agregan como capas independientes, no como item fisico grabado.

**Prepara:** piston lateral, palanca, panel y nicho de un bloque con pedestal vacio. [SET-G07](minecraft-clip-library.md#set-g07-nicho-movil-sencillo). Es ventana de exhibicion, no puerta para atravesar.

**Antes de grabar:** con palanca extiende piston hasta que panel tape `(241,82,1)`. Comprueba que al quitar energia se retrae y abre. Operador en `(237.5,81,0.5)`, fuera de camara. No agregar respuesta al pedestal.

| Parte | Tiempo de salida | Lo que haces jugando | Lo que debe verse |
|---|---|---|---|
| 1 | 0-1 s / f0-29 | Quita energia con la palanca una vez. | Panel se retira, apertura antes de f30. |
| 2 | 1-4 s / f30-119 | No toques mas controles, no entres en cuadro. | Nicho abierto estable. |
| 3 | 4-6 s / f120-179 | Segui quieto; no vuelvas a cerrar todavia. | Espacio limpio para respuesta posterior. |

**Despues, en Replay Mod:** camara fija `(241.5,82.8,-6)`, mirar `(241.5,82,1.5)`, FOV 50. P0/P6 iguales; T0 antes de accionar. Sin travelling. Palanca y operador quedan intencionalmente fuera: el clip muestra apertura, no explica todo el circuito.

**Exporta:** `mc_reveal_passage_open_thirdfront_vanilla_scene_t01.mp4`, 180 f, no loop. No meter glow, etiquetas, contenido ni transicion en el archivo.

**Repite si:** piston no tira panel, operador entra en cuadro, nicho negro o el resultado no queda abierto. **Reset:** vuelve a energizar palanca fuera del intervalo util. **Intentos:** 3-6.

## G08: Busqueda

**Reuso del mismo archivo:** buscar respuesta de minerales, pociones o herramientas. Estantes/nicho no contienen recetas, ingredientes ni el target.

**Prepara:** dos estantes vacios, divisor y nicho compacto sin techo. [SET-G08](minecraft-clip-library.md#set-g08-sala-de-busqueda-sin-target). No añadir props para distinguir episodios.

**Antes de grabar:** empezas en `(280.5,81,0.5)`. Ensaya recorrido alrededor del divisor; no pases a traves de estantes. Marca mentalmente los tres lugares que vas a mirar.

| Parte | Tiempo de salida | Lo que haces jugando | Lo que debe verse |
|---|---|---|---|
| 1 | 0-1 s / f0-29 | Mira primer estante y gira al segundo; inicia paso corto por zona libre. | Intencion de buscar desde inicio. |
| 2 | 1-4 s / f30-119 | Avanza por centro hasta `(282.5,81,3.5)` y mira nicho a derecha. | Segunda inspeccion y nueva posibilidad. |
| 3 | 4-6 s / f120-179 | Primero move +X hasta x=283.5; despues +Z hasta z=4.5. Detenete antes del pedestal z=5. | Rodeas divisor y terminas mirando espacio vacio. |

**Despues, en Replay Mod:** camara fija `(282,91,-4)`, mirar `(282,81.5,3.5)`, FOV 65. P0/P6 iguales, tiempo real. Ajusta sin ampliar set a x=286: el nicho podria salirse del vertical. Deben verse los tres puntos de busqueda y los giros del cuerpo.

**Exporta:** `mc_search_room_scan_thirdtop_vanilla_scene_t01.mp4`, 180 f, no loop. Base protagonista. [Variante baja de fondo](minecraft-clip-library.md#g08-buscar-con-intencion) solo si pasa preview con tarjeta; no darla por aprobada.

**Repite si:** atraviesas/chocas con divisor, nicho fuera de cuadro, cuerpo pequeño o accion parece paseo sin inspeccion. **Reset:** teleport de SET-G08. **Intentos:** 3-5.

## G09: Aparicion

**Reuso del mismo archivo:** tension narrativa en preguntas de armaduras, alimentos o minerales. No demuestra que el zombie lleve/deje caer ninguno de ellos. Excluir si presencia o sonido adelantan una pista.

**Prepara:** sala techada, esquina, luz lateral y zombie etiquetado sin IA. [SET-G09](minecraft-clip-library.md#set-g09-aparicion-por-oclusion). El mob ya esta colocado; no aparece por summon en medio de la toma.

**Antes de grabar:** comprobar rostro hacia -Z, sin equipo distintivo, sin quemarse al sol. Dificultad no pacifica. Deja registrado al mob al menos 11 s (3 de margen + 5 utiles + 3 de salida); vos no necesitas actuar ni estar en cuadro.

| Parte | Tiempo de salida | Lo que haces jugando | Lo que debe verse en replay |
|---|---|---|---|
| 1 | 0-1 s / f0-29 | No toques al mob ni lo muevas. | Camara cruza esquina y revela rostro/cuerpo. |
| 2 | 1-3 s / f30-89 | Segui fuera del cuadro. | Presencia estable; sin ataque inventado. |
| 3 | 3-5 s / f90-149 | Mantene set sin cambios. | Camara se retira un poco conservando presencia visible. |

**Despues, en Replay Mod:** P0 `(318.5,82.6,-2)`; P1 `(322,82.6,-2)`; P3 igual; P5 `(322,82.6,-2.5)`. Mirar `(321.5,82,2.5)`, FOV 55. Ruta lineal. En P0 debe estar oculto; en P1 visible. No uses x=319.5 como final: sigue detras del divisor.

**Exporta:** `mc_mystery_corner_appear_thirdfree_vanilla_scene_t01.mp4`, 150 f, no loop. Vanilla y video mudo primero; nada de ataque/shake/falso ojo añadido.

**Repite si:** mob da espalda, quema, se ve antes de reveal, no se descubre al mover camara o render falla por carga. **Reset:** corregir posicion/occlusion; si hace falta reemplazarlo, eliminar SOLO el etiquetado de SET-G09 antes de invocar otro. **Intentos:** 2-5 rutas.

## G10: Reaccion

**Reuso del mismo archivo:** cierre de respuestas de comida, herramientas o bloques, sin equipo ni trofeo que cambie con el episodio.

**Prepara:** plataforma plana y pared mate. [SET-G10](minecraft-clip-library.md#set-g10-reaccion-neutra). Mano vacia, sin armadura llamativa, efectos ni emotes.

**Antes de grabar:** colocate en `(360.5,81,0.5)` mirando hacia camara futura (-Z). Ensaya un salto sin desplazarte y una sola agachada. No hace falta skin particular.

| Parte | Tiempo de salida | Lo que haces jugando | Lo que debe verse |
|---|---|---|---|
| 1 | 0-1 s / f0-29 | Salta una vez, sin avanzar ni mantener salto pulsado. | Celebracion desde primer segundo. |
| 2 | 1-2 s / f30-59 | Ya apoyado, agachate brevemente y volve a erguirte. | Gesto de satisfaccion reproducible en vanilla. |
| 3 | 2-4 s / f60-119 | Quedate quieto con orientacion inicial. | Final util para CTA; sin otro evento. |

**Despues, en Replay Mod:** camara `(360.5,82.6,-5.5)`, mirar `(360.5,82,0.5)`, FOV 50, P0/P4 iguales. T0 antes del salto, tiempo real. Deben caber pies y apice. No meter emote, movimiento imposible de brazos ni item superpuesto en mano.

**Exporta:** `mc_reaction_player_celebrate_thirdfront_vanilla_scene_t01.mp4`, 120 f. Base no ciclica. Solo generar variante `loop` despues de revisar tres repeticiones sin salto de postura, sombra ni idle.

**Repite si:** te desplazas, faltan pies/apice, haces dos saltos, postura final distinta o aparece equipo que identifica un target. **Reset:** teleport y orientacion inicial. **Intentos:** 3-6.

## Al terminar cada ficha

1. Mira el archivo silenciado y a velocidad real en tamaño de telefono.
2. Comprueba accion antes de 1.5 s, final completo y numero de frames. G05 tiene 30 + 90, no dos archivos de 120.
3. Registra replay, ruta de camara, tramo temporal elegido, props visibles y resultado del ensayo. Usa `pendiente_de_ensayo`, `ensayado` o `aprobado_visual` segun lo que realmente hiciste.
4. Para fondo, revisa el clip con los overlays concretos: tarjeta central de la plantilla puede taparlo. Si falla, usa como escena o reencuadra el replay; no grabes otra vez por item.
5. Confirma tres categorias de reuso del mismo archivo y cualquier exclusion por spoiler. No lo marques compatible con todos los episodios automaticamente.

Registro breve reutilizable:

```text
ID / toma:
Replay y ruta de camara:
Archivo(s), fps y frames:
Instante de evento en cada archivo:
Estado del ensayo:
Props visibles / exclusiones:
Tres categorias de uso sin cambiar props:
Fallo observado y ajuste necesario:
```

## No grabar por ahora

Las C01-C20 son la expansion conceptual, no veinte obligaciones extra de esta sesion. Antes de rodar una, pedir su ficha concreta con materiales, set, accion, camara, salida y reset. Si solo explica la habilidad exclusiva de un item, se descarta en vez de desarrollar el guion.

No producir como extras: balde recogiendo agua, esponja absorbiendo, cobre raspado ni otro equivalente. Cambiar el nombre a "transformacion generica" no los hace reutilizables para este objetivo.
