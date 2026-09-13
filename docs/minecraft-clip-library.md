# Biblioteca general de escenas Minecraft

Guia de direccion creativa, guion tecnico y rodaje para Replay Mod y Remotion.

**Objetivo:** grabar por funcion narrativa y familia de uso, NO por item ni por episodio. Base propuesta: **30 escenas reutilizables: 10 generales + 20 contextuales**. Primer lote desarrollado: las diez generales, con guiones completos. Los veinte conceptos de ampliacion tienen accion de rodaje y restricciones, pero todavia requieren desarrollo tecnico individual.

**Estado:** documento de produccion y ensayo, no biblioteca ya capturada ni automatizacion implementada. Perfil: Minecraft Java Edition 1.21.11; entrega 1080x1920, 9:16, 30 fps. Comandos, rutas y montajes no ejecutados dentro del juego: `pendiente_de_ensayo`.

## Rodaje paso a paso

**Para grabar, empezar por [la guia operativa escena a escena](minecraft-clip-shooting-guide.md), no por las tablas de estrategia.** Contiene las diez fichas G01-G10: materiales, preparacion, acciones en orden, camara, archivos a entregar, reset y motivos para repetir. Las C01-C20 siguen siendo propuestas de ampliacion; no son tareas de rodaje listas hasta disponer de ficha completa y superar el filtro de reutilizacion.

Cada ficha separa lo que haces jugando de lo que haces despues en Replay Mod. Una persona puede interpretar al jugador y elegir luego una camara externa: no necesita un segundo jugador que filme. Los mecanismos que requieren un trigger tienen su propia advertencia.

Para mantener este formato en futuras solicitudes esta la skill de proyecto [`minecraft-clip-director`](../.opencode/skills/minecraft-clip-director/SKILL.md). Lee solo la ficha solicitada y sus dependencias; no necesita cargar toda esta biblioteca por cada cambio.

## Indice

1. [Resumen de la estrategia visual](#1-resumen-de-la-estrategia-visual)
2. [Reglas de estilo generales](#2-reglas-de-estilo-generales)
3. [Matriz de cobertura de Minecraft](#3-matriz-de-cobertura-de-minecraft)
4. [Lista priorizada de clips](#4-lista-priorizada-de-clips)
5. [Primer lote de guiones tecnicos completos](#5-primer-lote-de-guiones-tecnicos-completos)
6. [Variantes recomendadas](#6-variantes-recomendadas)
7. [Mundos, construcciones y preparaciones](#7-mundos-construcciones-y-preparaciones)
8. [Lista de comandos de Minecraft](#8-lista-de-comandos-de-minecraft)
9. [Convencion de nombres de archivos](#9-convencion-de-nombres-de-archivos)
10. [Checklist de grabacion](#10-checklist-de-grabacion)
11. [Checklist de control de calidad](#11-checklist-de-control-de-calidad)
12. [Que diez clips grabar primero](#12-que-diez-clips-grabar-primero)

## 1. Resumen de la estrategia visual

### La unidad de la biblioteca es una escena, no un objeto

Una escena de **descubrimiento**, **decision**, **busqueda**, **peligro**, **precision** o **recompensa** sirve para cientos de respuestas distintas. En cambio, una escena de "la esponja absorbe agua" representa una mecanica estrecha: no debe ser la base de una biblioteca general.

Los objetos que aparezcan durante el rodaje son utileria fija. No se sustituyen por la respuesta de cada episodio. Un MP4 de Minecraft no permite cambiar automaticamente el objeto que sostiene el jugador; eso exigiria otra captura o una composicion especifica. La respuesta exacta sigue siendo un icono/nombre/asset independiente en Remotion.

Tres niveles de uso:

| Nivel | Que aporta | Ejemplo | Regla de uso |
|---|---|---|---|
| General, G01-G10 | Emocion y ritmo, sin describir propiedades del target | Elegir entre caminos; superar un salto | Puede acompañar muchas categorias, con control de spoilers y encuadre |
| Contextual, C01-C20 | Ambiente de una familia amplia | Taller, cultivo, oceano, transporte | Solo si el contexto no contradice ni adelanta la pista |
| Evidencia especifica | Una propiedad exacta demostrada | Item concreto absorbiendo agua | Excluida de esta biblioteca; no convertirla en tarea de rodaje |

### Filtro obligatorio de reutilizacion

Antes de aceptar una escena, escribir tres categorias distintas de episodios en las que sirve **el mismo archivo**, con los mismos props y sin atribuirles sus mecanicas. Son ejemplos de uso narrativo, no pruebas mecanicas ni porcentajes de cobertura.

- Aceptar: elegir caminos, buscar un lugar, reaccionar, descubrir un espacio, esquivar un peligro, mostrar escala. La respuesta se compone por separado.
- Rechazar: llenar un balde, absorber agua con esponja, raspar oxidacion del cobre o mostrar una conducta exclusiva de un mob como idea central. No se salva la propuesta llamandola "contextual".
- Tener un cofre, una flecha o un mob de utileria no vuelve exclusiva la escena: lo importante es que cuente una situacion y no enseñe la propiedad de ese prop como si correspondiera a otro target.
- Si hay que cambiar el item en mano, el mob, la receta o el bloque cada vez que cambia la respuesta, la escena no pasa. Reencuadrar el mismo replay si puede pasar; recapturar por respuesta no.
- Si un target coincide con un prop visible o el contexto da una pista falsa, elegir otra escena. Reutilizable no significa seguro en todos los episodios.

**Cobertura basica significa poder montar un episodio atractivo para cualquier categoria sin pedir otra grabacion. No significa demostrar en gameplay todas las propiedades de todos los items.** Para esa primera meta, diez escenas generales ya forman un piso util; veinte contextuales agregan variedad semantica. No se promete un porcentaje de cobertura del registro de 1.21.11 sin auditarlo.

### Paquete minimo y ampliacion

- Etapa A: diez escenas generales. Rodarlas una vez; obtener un encuadre protagonista y otro con espacio para texto cuando aporte valor.
- Etapa B: veinte escenas contextuales. Rodarlas por familia y reutilizarlas, no por respuesta. Evitar grabar veinte variantes del mismo gesto de abrir cofres.
- Presupuesto orientativo: 30 acciones base, aproximadamente 40-50 archivos utiles incluyendo reencuadres. Es una estimacion editorial, no una obligacion de duplicar todo.
- Cuando falta una familia o hay duda, volver a una general compatible; no forzar una toma que atribuya una propiedad falsa.
- Renovar por desgaste visual y resultados reales de publicacion, no por cada nuevo episodio.

### Supuestos, fuentes y compatibilidad

- Minecraft Java 1.21.11, mundo local de ensayo separado de cualquier mundo valioso.
- Fabric, Fabric API y Replay Mod. Sodium e Iris opcionales. Ningun guion requiere mods adicionales.
- Replay Mod debe encontrar un ejecutable de FFmpeg para exportar MP4. Comprobar su configuracion en el equipo de captura: tener FFmpeg en el mini PC o en Remotion no lo configura automaticamente en Minecraft. FFmpeg es una herramienta externa, no un mod adicional.
- La pagina oficial de Replay Mod ofrece `1.21.11-2.6.27`. Debe probarse la combinacion exacta con loader, Sodium, Iris y shaderpack antes de rodar.
- Fuente principal de referencias: `public/mc-assets/item-assets/` y `public/mc-assets/entity-assets/`. El README del paquete indica una version posterior a 1.21.11; un PNG no valida ni mecanica ni version.
- Los facts de `transfer/facts/` y `data/new-clues-20260815/` incluyen datos historicos de 1.21.5. No se reutilizan como certificacion de 1.21.11.
- No se ha medido el hardware de captura ni el tiempo de render. Vanilla y 1080x1920 son la base; 2160x3840 es opcional.
- Este documento no afirma haber observado un render productivo reciente del mini PC. El HTML del dashboard por si solo no confirma videos, tareas ni release activa.
- Se conservaran replay y ruta de camara. El archivo final no lleva texto, musica, logos ni transiciones de edicion.
- Calidad editorial no equivale a viralidad. Un hook claro es una hipotesis que se contrasta con retencion real.

### Etapa 1: clasificacion por potencial audiovisual

No hace falta clasificar cada item individualmente: se clasifican sus posibilidades visuales y se asignan familias de escena. Los grupos se superponen.

| Potencial | Grupos de elementos | Escenas generales/contextuales | Por que funciona |
|---|---|---|---|
| Visual alto | Bloques con estados, luz, fluidos, particulas, entidades con silueta clara | C08 propiedades, C20 transformacion, G07 apertura | Cambios de forma/estado legibles a tamaño de telefono |
| Sorpresa alta | Colision, gravedad, ocultacion, comportamiento de mobs | G03 suelo inestable, G09 aparicion, C11 interaccion | Invierte una expectativa simple sin texto |
| Accion alta | Herramientas, armas, proyectiles, transportes, mecanismos | G04 salto, G05 esquiva, C01 mineria, C17 transporte | Causa, trayectoria y consecuencia |
| Hooks altos | Objetos hacia lente, impactos, apariciones, cambios de escala | G05, G09, G06, C18 proyectiles | Evento importante en los primeros 15-45 frames |
| Fondos altos | Actividad localizada, recorridos repetibles, estaciones de trabajo | G02 decision, G08 busqueda, C02 taller, C16 redstone | Movimiento claro sin ocupar toda la zona de texto |
| Reveals altos | Contenedores, accesos, estructuras, espacios antes ocultos | G01 cofre, G07 acceso, C15 estructura | La oclusion crea expectativa y la apertura la resuelve |
| Transiciones altas | Superficies cercanas, agua, pasadas laterales, particulas controladas | G06 borde cercano, C12 agua, C18 proyectil | El propio movimiento permite cortar despues en Remotion |
| Bajo aislado | Ingredientes, minerales, bloques comunes, equipo quieto, decoracion | G02/G08 para ritmo; C02/C08 para contexto | El item quieto no sostiene una toma; la escena aporta intencion |

Items visualmente raros no reciben prioridad automatica. Un estado complejo e ilegible puede rendir peor que una decision clara frente a dos rutas. La rareza es una herramienta, no el objetivo.

## 2. Reglas de estilo generales

### Lenguaje visual

- Un foco principal por plano. No poner un mob, un salto y una explosion compitiendo simultaneamente.
- Primer frame ya comprometido con una accion: mano cerca del cofre, pie sobre borde, flecha entrando o cuerpo decidiendo.
- Evento fuerte entre 0.5 y 1.5 s; puede ocurrir antes si sigue siendo entendible. No intro de paseo o logo.
- Cada clip debe tener inicio limpio, causa visible y resultado; no necesariamente tres cortes. La mayoria se resuelve en una toma continua.
- Vanilla reconocible, texturas normales, misma skin sencilla en la sesion, pero ningun guion depende de esa skin.
- No mas de dos clips consecutivos con misma familia de camara. Las orbitas no son el movimiento por defecto.
- La accion debe entenderse muda. Audio de juego/Foley separado; nada de musica incrustada.
- Particulas naturales solo cuando ayudan. No resolver un mal plano con humo, bloom o blur.
- No simular una mecanica falsa invirtiendo el video. Un loop necesita continuidad de estado y movimiento, no solo encuadres iguales.
- No llamar "generico" a un clip que muestra y usa el target exacto antes del reveal. Registrar siempre que aparece.

### Fondos frente a escenas completas

En el codigo local de `QuizCapasCopy`, la tarjeta de pista ocupa aproximadamente x=60-1020, y=430-1110. Poner la accion en el centro detras de esa tarjeta puede ocultarla por completo. El encuadre de fondo debe probarse en la plantilla real, no aprobarse solo en un reproductor.

| Entrega | Encuadre | Uso |
|---|---|---|
| `scene` | Accion grande en zona central, titulo arriba | Hook, respiro visual, reveal, evidencia si se valida |
| `background` | Accion baja o lateral, espacio negativo comprobado | Narracion, pista o decision que no requiera interpretar todos los detalles |
| `transition` | Paso/oclusion natural aprovechable | Corte posterior; el MP4 sigue sin wipe ni fundido |
| `impact` | Evento corto con causa visible | Acento breve, nunca fondo repetido debajo de lectura larga |
| `reveal` | Espacio que se descubre | El icono/nombre exacto se añade en Remotion, no en Minecraft |
| `loop` | Ciclo real verificado | Fondo repetible; no asignarlo solo porque el plano sea fijo |

### Zonas seguras orientativas

Coordenadas de pantalla: origen arriba a izquierda. Son margenes conservadores, no reglas permanentes de cada plataforma.

| Zona | Rectangulo | Requisito |
|---|---|---|
| Titulo | x=120-860, y=200-460 | Fondo uniforme o poco detallado |
| Accion de escena | x=120-860, y=480-1400 | Sujeto, recorrido y punto de contacto dentro |
| Accion baja de fondo | x=180-800, y=1140-1480 | Solo para acciones suficientemente grandes y sencillas |
| Subtitulo/CTA | x=120-860, y=1400-1540 | No compartir con manos, pies ni golpe esencial |
| Riesgo de UI | y<160, y>1600, x>900 | Nada imprescindible |

No se pueden ocupar a la vez la accion baja y el CTA. Cada plantilla decide cual desplazar o suprimir. Para una accion que necesita toda la pantalla, usar `scene` en vez de empequeñecerla hasta que deje de leerse.

### Tiempo, fisica y Replay Mod

- Frames de salida a 30 fps; rangos inclusivos. `0-29` = 30 frames = 1 s. Un clip de 180 frames termina en 179.
- Minecraft normalmente simula a 20 ticks/s. No confundir ticks de juego con frames de video.
- Los tiempos de guion son objetivos de montaje. Ensayar la accion real y seleccionar el comienzo del replay para que el evento caiga temprano. No se garantiza una trayectoria fisica por escribir un frame.
- Registrar al menos 3 s antes y despues de la accion. Esos margenes quedan en el replay/master, NO al principio del archivo de uso.
- Replay Mod separa keyframes de posicion/orientacion y keyframes temporales. Convertir frame final a segundos mediante `f/30`.
- FOV constante por toma. No se asume animacion nativa de FOV por keyframes: el acercamiento es travelling o crop moderado posterior.
- Rutas lineales para velocidad constante. Spline cubica solo tras comprobar sobrepasos y paredes. El easing se consigue por espaciado de puntos; no inventar una interfaz Bezier de Remotion dentro de Replay Mod.
- Primera persona: keyframes de espectador de la misma entidad. Probar manos/arco. Menus e inventario no se consideran reproducibles fielmente; por eso no hay guiones dependientes de GUI.
- No planificar rebobinado temporal dentro de una ruta. Reinicios de set quedan fuera de toma.
- Exportacion nativa de audio no es requisito del flujo. Entrega muda y Foley/ambiente aparte; no instalar addons de audio no permitidos.
- Si el exportador incluye un frame extra en el limite final, recortarlo al verificar la entrega.

### Contrato propuesto para Remotion

Entrega principal: MP4 H.264, `yuv420p`, SDR, 1080x1920, 30 fps constantes, sin texto ni musica. Master opcional 2160x3840 o secuencia de imagenes; no es necesario renderizar todo a 4K. Motion blur y profundidad de campo apagados en el master reutilizable.

`cover` solamente si la relacion/crop preserva la accion; `contain` cuando un panel distinto cortaria lo importante. No estirar. Oscurecimiento y mascara solo en composicion. Blur nunca sobre causa, sujeto ni resultado.

Ficha ilustrativa, no esquema implementado:

```json
{
  "id": "G07",
  "file": "mc_reveal_passage_open_thirdfront_vanilla_scene_t01.mp4",
  "gameVersion": "1.21.11",
  "role": "narrative",
  "fps": 30,
  "durationInFrames": 180,
  "width": 1080,
  "height": 1920,
  "use": "reveal",
  "loopable": false,
  "muted": true,
  "fit": "cover",
  "eventFrame": 24,
  "visibleElements": ["stone_bricks", "gray_concrete"],
  "impliedMechanics": ["opening"],
  "safeTextRect": {"x": 120, "y": 200, "width": 740, "height": 240},
  "validation": "pending_in_game"
}
```

El `eventFrame` se ajusta al archivo real. Guardar hash del asset, tramo elegido, crop y velocidad en props por render; nunca sortear dentro de React. No convertir esta propuesta en cambios de produccion sin canary y revision de release.

## 3. Matriz de cobertura de Minecraft

### Etapa 2: cobertura basica frente a evidencia

Las generales acompañan la pregunta, el tiempo de decision y la respuesta; las contextuales solo entran cuando hay compatibilidad. **No asignar automaticamente por `guessType`: el banco local contiene categorias heterogeneas**, por ejemplo items que funcionalmente son comida, arma o mecanismo. Se necesitan etiquetas funcionales o revision, conservando la categoria historica.

| Familia de conocimiento | Base general sugerida | Contexto opcional | Limite que evita falsa evidencia |
|---|---|---|---|
| Items utilizables | G02, G08, G10 | C02, C08 | No demostrar un uso que el target no tiene |
| Bloques | G03, G06, G07 | C01, C02, C20 | El bloque de utileria no es la respuesta |
| Variantes de bloques | G02, G08 | C08, C20 | Una variante puede tener otra mecanica |
| Herramientas | G04, G08 | C01, C05 | No atribuir mineria/raspado a todas |
| Armas | G05, G09 | C18, C11 | Distinguir arma del jugador y proyectil de mob |
| Armaduras | G04, G10 | C09 | No equipar el target por episodio; toma ilustrativa fija |
| Comida | G01, G02 | C06, C07 | No insinuar cultivo o preparacion de todos los alimentos |
| Pociones | G02, G08 | C07, C08 | No asociar color visual a efecto sin comprobacion |
| Encantamientos | G07, G10 | C04, C08 | Contexto de magia no demuestra compatibilidad ni nivel |
| Redstone | G02, G07 | C16 | Circuito debe funcionar; no todo bloque transmite señal |
| Transportes | G04, G06 | C17, C12 | Mover camara no demuestra velocidad del vehiculo |
| Proyectiles | G05, G04 | C18 | No usar flecha como prueba de lanzamiento de otro item |
| Objetos raros | G01, G07 | C15, C14 | Rareza no implica procedencia en End/cofres |
| Objetos de progresion | G06, G07 | C02, C15 | No inventar receta ni requisito de avance |
| Mobs pasivos | G08, G10 | C11, C19 | No atribuir hostilidad de otro mob |
| Mobs neutrales | G02, G09 | C11 | Su conducta depende de condiciones |
| Mobs hostiles | G05, G09 | C11, C19 | No mostrar el target exacto antes de tiempo |
| Jefes | G06, G09 | C14, C15 | Escala narrativa no demuestra vida/daño |
| Entidades especiales | G02, G06 | C17, C19 | No confundir bloque, item y entidad |
| Particulas | G07, G09 | C04, C08 | No hacerlas decoracion que finja una mecanica |
| Efectos de estado | G04, G10 | C08 | Grabar efecto real o usar ilustracion claramente separada |
| Estructuras | G06, G08 | C15 | No toda respuesta aparece alli |
| Biomas | G06, G08 | C06, C12, C15 | Paisaje puede adelantar pistas de origen |
| Dimensiones | G06, G07 | C13, C14 | No asignarlas por color o popularidad |
| Mecanicas de juego | G02, G03 | C08, C16, C20 | Ensayar version/condiciones, no guiarlas por intuicion |
| Eventos naturales | G03, G09 | C08 tormenta | Un rayo por comando no es aparicion natural documentada |
| Interacciones | G01-G10 segun rol | C01-C20 segun hecho | Una escena universal no es una prueba universal |

### Matriz de variedad audiovisual

| Eje | Escenas | Diferencia de accion |
|---|---|---|
| Items | G01, G02, C02, C07 | Descubrir, elegir, preparar, consumir |
| Bloques | G03, G07, C01, C20 | Caer, abrir paso, romper, cambiar estado |
| Mobs | G09, C10, C11, C19 | Aparecer, encuentro, interaccion, converger |
| Estructuras | G06, G08, C15 | Escala, busqueda, revelar acceso |
| Biomas | C06, C12, C15 | Recoleccion, inmersion, descubrimiento |
| Dimensiones | C13, C14 | Cruce seguro y perspectiva del vacio |
| Redstone | G07, C16 | Abrir espacio y repetir un ciclo |
| Combate | G05, C11, C18 | Esquivar, interactuar, acertar |
| Movimiento | G04, C12, C17 | Salto, cambio de medio, velocidad |
| Transformacion | G03, G07, C20 | Estado del entorno, acceso, material |
| Peligro | G03, G05, G09 | Suelo, trayectoria, aparicion |
| Humor | G02, G04, C19 | Duda, recuperacion, caos concentrado |
| Misterio | G01, G08, G09 | Contenedor, ocultacion, amenaza |
| Escala | G06, C14, C15 | Persona/edificio, vacio, estructura |
| Descubrimiento | G01, G07, C15 | Abrir objeto, abrir espacio, descubrir lugar |

### Como medir cobertura sin inventar porcentajes

Para cada target del catalogo 1.21.11, registrar: una escena de hook elegible, dos alternativas de fondo, una de decision y una de cierre; ademas, familias contextuales verificadas si existen. Si solo tiene generales, su cobertura narrativa es completa pero su cobertura mecanica puede ser nula. Reportar esas dos medidas por separado.

No se ha ejecutado esa auditoria exhaustiva. El diseño cubre las 27 familias a nivel narrativo; no certifica todos sus elementos. La cantidad de 30 es una propuesta basica de produccion, no un minimo matematico demostrado.

## 4. Lista priorizada de clips

### Etapa 3: conceptos generales

I = intensidad 1-5. Dificultad B/M/A = baja/media/alta. Comandos O=opcionales, R=recomendados para preparar/reset. Ninguno requiere shaders. V=variante suave opcional. Los tiempos son entregas de uso, sin margenes de captura. No hay una respuesta fija asociada a ningun ID.

| ID | Funcion / principal / secundarios | Emocion | Hook temprano | I | Uso | Duracion | Dif. | Cmd. | Shader | Mobs | Reuso |
|---|---|---|---|---:|---|---|---|---|---|---|---|
| G01 | Descubrir contenedor / jugador / cofre, pared | Curiosidad, recompensa | H04: mano abre antes de f30 | 2 | scene, reveal | 6 s / 180 f | B | O | No | No | Alto; no mostrar contenido ni atribuir loot |
| G02 | Elegir ruta / jugador / dos accesos simetricos | Tension, humor | H10/H20: cambia de decision en f15 | 2 | background, scene | 6 s / 180 f | B | O | No | No | Alto; no depende del target |
| G03 | El suelo falla / arena de utileria / jugador, hueco seguro | Peligro, sorpresa | H07/H06: se desprende antes de f24 | 4 | impact, scene | 5 s / 150 f | M | R | No | No | Alto narrativo; no prueba de propiedades del target |
| G04 | Salto que funciona / jugador / plataformas | Tension, satisfaccion | H14/H09: ya en vuelo en f0-15 | 4 | scene, impact | 5 s / 150 f | M | O | No | No | Alto; sin item especial para salvarse |
| G05 | Trayectoria esquivada / flecha / jugador, pared | Velocidad, peligro | H01/H08: proyectil pasa cerca de lente | 4 | impact, transition | 4 s / 120 f | M | R | No | No | Alto narrativo; excluir targets que la flecha spoilee |
| G06 | Descubrir la escala / columna / jugador, borde cercano | Escala, descubrimiento | H05/H13: columna completa aparece en f30 | 3 | reveal, scene | 6 s / 180 f | B | O | V | No | Alto; construccion sin forma de target |
| G07 | Se abre el acceso / mecanismo / pedestal vacio | Misterio, recompensa | H12/H06: pared se retira antes de f30 | 3 | reveal, scene | 6 s / 180 f | M | R | No | No | Alto; respuesta añadida solo en Remotion |
| G08 | Buscar y encontrar espacio / jugador / estanterias, nicho | Curiosidad | H16/H13: cenital y giro decidido antes de f30 | 2 | background, scene | 6 s / 180 f | B | O | No | No | Alto; sin receta ni objeto de respuesta |
| G09 | Algo aparece / mob de utileria / esquina, luz | Misterio, peligro | H03/H19: aparece por borde antes de f30 | 4 | scene, impact | 5 s / 150 f | M | R | V | 1 zombie | Alto narrativo, condicionado por spoilers de mob |
| G10 | Reaccion de acierto / jugador / plataforma neutra | Recompensa, satisfaccion | H15/H09: salto corto antes de f15 | 2 | loop, background | 4 s / 120 f | B | O | No | No | Alto; sin mostrar respuesta ni victoria falsa |

### Conceptos contextuales por familia

Cada fila define una accion reutilizable en muchos episodios. La utileria concreta se mantiene entre usos: no se recaptura para cada item. Uso contextual requiere revision de compatibilidad, aunque no se abra ningun inventario.

| ID | Familia / principal / secundarios | Emocion | Hook | I | Uso | Duracion | Dif. | Cmd. | Shader | Mobs | Reuso |
|---|---|---|---|---:|---|---|---|---|---|---|---|
| C01 | Mineria / jugador / herramienta comun, pared mixta | Poder, descubrimiento | H02 rotura temprana | 3 | scene, background | 6 s / 180 f | B | O | No | No | Herramientas, bloques, minerales compatibles |
| C02 | Taller y construccion / jugador / bancos, bloques de utileria | Satisfaccion | H16 macro de colocacion | 2 | background, scene | 6 s / 180 f | B | O | No | No | Materiales, bloques, items de fabricacion |
| C03 | Procesamiento / horno encendido / almacen, jugador | Expectativa | H19 encendido tras quietud breve | 2 | background | 6 s / 180 f | B | O | V | No | Solo procesamiento compatible; no toda receta |
| C04 | Encantamiento / libro de mesa / jugador, bibliotecas | Rareza, poder | H04 libro se abre con aproximacion | 3 | scene, background | 6 s / 180 f | B | O | V | No | Encantamientos y equipo compatible |
| C05 | Reparacion y preparacion / jugador / yunque, equipo | Expectativa | H20 equipo se acerca a estacion | 2 | background | 6 s / 180 f | B | O | No | No | Contexto, no recuperacion de durabilidad sin GUI |
| C06 | Cultivo y recoleccion / jugador / plantas y recipientes | Satisfaccion | H06 cosecha cambia entorno | 2 | scene, background | 6 s / 180 f | B | O | No | No | Plantas/alimentos compatibles, no todos |
| C07 | Consumo y preparacion / jugador / mesa de comida o pocion | Curiosidad | H11 accion breve produce reaccion | 2 | scene | 5 s / 150 f | B | O | No | No | Dos subvariantes fijas: comer y beber; no por item |
| C08 | Propiedades y estados / sujeto / luz, lluvia o particulas reales | Transformacion | H19/H20 cambio de estado temprano | 3 | background, scene | 6 s / 180 f | M | R | V | No | Seleccionar subvariante verificada, no efecto universal |
| C09 | Equipamiento / jugador / armadura sencilla, soporte | Poder | H10 contraste antes/despues | 3 | scene | 5 s / 150 f | M | O | No | No | Equipo; dos tomas fijas, no armadura del target |
| C10 | Encuentro comercial / aldeano / mostrador, jugador | Curiosidad | H03 aldeano aparece al girar | 2 | background, scene | 6 s / 180 f | M | O | No | 1 aldeano | Contexto social; no afirmar oferta concreta |
| C11 | Liberar un paso / jugador / porton, animal de utileria | Sorpresa | H11 abrir paso descubre presencia | 3 | scene | 6 s / 180 f | M | R | No | 1 animal | Encuentro/liberacion; sin conducta exclusiva |
| C12 | Entorno acuatico / jugador o camara / superficie, agua | Descubrimiento | H13 inmersion revela espacio | 3 | background, transition | 6 s / 180 f | M | O | V | No esenciales | Agua, pesca, exploracion cuando sean compatibles |
| C13 | Otra dimension / jugador / portal y Nether | Misterio | H12 oclusion deja ver entorno | 3 | scene, transition | 6 s / 180 f | M | O | V | No esenciales | Nether solo si no adelanta origen |
| C14 | Vacio y altura / construccion End / jugador, borde | Escala, peligro | H05 cambio de escala | 4 | scene, reveal | 6 s / 180 f | M | O | No | No esenciales | End/progresion, no todo item raro |
| C15 | Descubrimiento de estructura / acceso / terreno, jugador | Descubrimiento | H13 camino revela entrada | 3 | reveal, background | 7 s / 210 f | M | O | V | No esenciales | Variantes de lugar por familia, no target |
| C16 | Mecanismo repetible / piston / redstone, panel movil | Satisfaccion | H15 extension-retorno | 2 | loop, background | 4 s / 120 f | M | R | No | No | Mecanismos compatibles; ciclo real |
| C17 | Transporte / barco o vagoneta / pista, jugador | Velocidad | H08 accion directa desde inicio | 4 | background, scene | 7 s / 210 f | M | O | No | Vehiculo | Dos medios fijos cubren transporte basico |
| C18 | Proyectiles y precision / proyectil / blanco, jugador | Poder | H02/H18 impacto temprano | 4 | impact, scene | 4 s / 120 f | M | R | No | No | Subvariantes arco/lanzable, sin cambiar por target |
| C19 | Encuentro colectivo / varios mobs / punto de interes | Caos controlado, humor | H17 convergencia | 3 | scene, background | 6 s / 180 f | M | R | No | 3-5 | Grupo visible como un unico foco |
| C20 | Cambio de entorno / sala vacia y sala preparada / jugador | Transformacion | H06 comparacion por corte temprano | 3 | scene | 6 s / 180 f | B | O | No | No | Antes/despues editorial, no mecanica de un item |

### Accion concreta para rodar las contextuales

Estas recetas breves evitan convertir las familias en ideas vagas. Antes de ampliar el primer lote, desarrollar coordenadas y ensayo de cada una con el mismo formato de la seccion 5.

| ID | Rodaje base reutilizable | Restriccion |
|---|---|---|
| C01 | Plano lateral: romper 3 bloques de piedra de una pared; el tercero deja ver un hueco ya construido. Primera rotura en f15-25; sostener hueco 2 s. | Herramienta visible fija; no sustituirla por otra en cada quiz ni llamar mineral al hueco |
| C02 | Cenital oblicua: colocar tres bloques para completar un borde; tercero cierra figura sencilla. Primero en f12, siguiente f45, ultimo f80. | No GUI ni receta inventada; tampoco se demuestra que cualquier item se fabrique |
| C03 | Frontal de horno: preparar combustible/entrada fuera del clip; empezar justo antes de encendido, mostrar jugador retirando mano y llama visible. | No mostrar salida falsa ni comprimir coccion como si fuera instantanea |
| C04 | Camara a altura del libro: jugador se acerca y libro se abre; desplazamiento de 0.5 bloques deja ver bibliotecas. | Libro abierto no prueba que el item sea encantable ni que un encantamiento se aplique |
| C05 | Lateral: jugador llega al yunque con herramienta en mano, se detiene y mira superficie; corte tras gesto de preparacion. | Es ambiente, no reparacion efectiva; no añadir barra de durabilidad falsa |
| C06 | Plano bajo: cosechar una hilera corta de trigo maduro; luego plano alto del hueco y drops reales. | Dos cortes en Remotion; no aplicar a plantas que no se comportan como trigo |
| C07 | Dos tomas fijas: jugador come pan / bebe una pocion definida. Empezar con animacion ya en marcha para completar temprano. | Registrar item y efecto reales; no atribuirlos a otra respuesta; no confiar en color |
| C08 | Tres tomas de familia: encendido de luz por circuito; lluvia tras preparar clima; efecto visible real en jugador con condiciones registradas. | No mezclar los tres eventos en un clip; tormenta no implica rayo inmediato |
| C09 | Dos tomas, mismo suelo y camara: jugador sin armadura y equipado con set comun. Misma postura; corte comparativo posterior. | No fingir equipamiento en tiempo real si Replay Mod no reproduce la accion; no GUI |
| C10 | Travelling de 1 bloque rodea esquina de mostrador y descubre aldeano; jugador se detiene frente a el. | No es comercio consumado ni garantiza una oferta del target |
| C11 | Jugador abre porton y deja ver un animal comun detras; se aparta para dejar paso. Abrir antes de f30, sostener encuentro 2 s. No hace falta que el animal cruce. | Mismo animal/archivo para encuentro, sorpresa y liberacion en distintas categorias; no enseñar una conducta exclusiva ni prometer IA sincronizada |
| C12 | Camara baja atraviesa superficie en primeros 30 f y descubre arco de piedra submarino; se detiene antes de entrar. | No agua profunda negra; no prometer datos de oxigeno con HUD oculto |
| C13 | Dos intervalos reales de un replay: aproximacion al portal y salida en Nether. Corte se decide en Remotion. | No trayectoria spline atravesando dimensiones ni teletransporte continuo falso |
| C14 | Travelling lateral corto descubre vacio bajo un puente en End; jugador quieto da escala. | End real, chunks cargados, sin caida al vacio necesaria |
| C15 | Pasar junto a pared cercana y revelar acceso de estructura: una toma ruina, otra fortaleza y otra edificio Overworld. | Ampliacion por entorno, no una estructura por respuesta |
| C16 | Un piston mueve panel un bloque y vuelve; camara fija, dos ciclos reales, seleccionar uno con estados iguales. | Sin mobs/items aleatorios; verificar union del loop |
| C17 | Barco sobre pista ancha de hielo y vagoneta en curva amplia: entrar en movimiento y revelar salida. | Dos assets fijos, velocidad real, accion centrada para texto superior |
| C18 | Flecha a blanco y lanzable a pared, dos tomas laterales; vuelo completo corto y contacto antes de 1 s. | El blanco no produce explosion salvo mecanismo real documentado |
| C19 | 3-5 gallinas se acercan a jugador sosteniendo semillas; cenital fija mantiene convergencia como un solo foco. | IA no sincronizable al frame; excluir si semillas/gallina adelantan respuesta |
| C20 | Grabar sala vacia y la misma sala preparada con bancos/estantes neutros, camara fija identica. Dos fuentes; Remotion corta de antes a despues cerca de f20 y mantiene resultado. | La decoracion es fija, sin recetas ni target. Progreso, preparacion y descubrimiento: no fingir transformacion instantanea del juego ni reconstruir por episodio |

### Distribucion de los veinte hooks

| Tipo | Escena que lo cubre |
|---|---|
| H01 Objeto hacia camara | G05 |
| H02 Impacto primer segundo | C01, C18 |
| H03 Mob repentino | G09, C10 |
| H04 Acercamiento a detalle | G01, C04 |
| H05 Cambio de escala | G06, C14 |
| H06 Transformacion | G03, G07, C20 |
| H07 Peligro inminente | G03 |
| H08 Primera persona activa | G05 variante, C17 |
| H09 Tercera persona llamativa | G04, G10 |
| H10 Comparacion | G02, C09 |
| H11 Inofensivo, resultado inesperado | C11 |
| H12 Reveal por oclusion | G07, C13 |
| H13 Movimiento que revela | G06, G08, C12, C15 |
| H14 Fallo que termina bien | G04 |
| H15 Loop visual | G10, C16, condicionado a QA |
| H16 Cenital o macro | G08, C02 |
| H17 Convergencia | C19 |
| H18 Objeto pequeno/reaccion mayor | C18 con mecanismo de apertura real como variante; no explosion inventada |
| H19 Quietud/evento fuerte | G09, C03, C08 |
| H20 Pregunta sin texto | G02, C05 |

No forzar los veinte hooks en los diez primeros clips. El catalogo completo distribuye el lenguaje visual sin hacer veinte versiones de una explosion.

## 5. Primer lote de guiones tecnicos completos

### Etapa 4: convenciones de rodaje

Cada guion representa una **situacion general**. Cofre, flecha, arena, piston o zombie son utileria fija, no el target del episodio. No hace falta volver a grabar cuando cambie la respuesta.

Coordenadas de mundo en bloques; Y de camara = centro de lente, Y del jugador = pies. Coordenadas de pantalla en pixeles. Velocidades de camara son aproximadas y reproducibles; las de fisica real no se inventan. Frames de accion son objetivos que se ajustan al seleccionar el intervalo grabado. Todos los comandos referenciados estan en la seccion 8.

### G01: Descubrir algo guardado

#### Identificacion

- ID: `G01`. Nombre corto: Descubrimiento.
- Archivo: `mc_discovery_container_open_thirdoblique_vanilla_scene_t01.mp4`.
- Categorias: busqueda, recompensa, misterio; uso narrativo para items, bloques, comida, equipo y objetos raros.
- Principal: jugador que abre un contenedor. Secundarios: cofre de utileria, pared y suelo neutros.
- Emocion: curiosidad resuelta. Intensidad: 2/5.
- Uso: `scene`, `reveal`; `background` solo variante baja. Duracion: 6 s / 180 f. Corta: 3 s / 90 f; larga: principal. No loop.

#### Idea central

Alguien encuentra y abre algo que podria contener una respuesta, sin enseñar un objeto especifico ni afirmar que se obtiene alli.

#### Hook

F0: cofre cerrado ocupa centro bajo, mano preparada junto a tapa. F0-15: acercamiento de camara y accion de abrir. La tapa abre antes de f30 y detiene el scroll. Pregunta: "que hay dentro?". Evitar caminata de aproximacion, GUI, loot visible o brillo dorado ficticio saliendo del cofre.

#### Guion por escena

| Escena | Duracion | Inicial | Final | Objetivo narrativo |
|---|---|---:|---:|---|
| 1 | 1 s / 30 f | 0 | 29 | Apertura inmediata |
| 2 | 3 s / 90 f | 30 | 119 | Mantener expectativa con interior no visible |
| 3 | 2 s / 60 f | 120 | 179 | Cierre limpio para editar respuesta |

**Escena 1.** Accion exacta: jugador junto a (0.5,81,-0.5) abre cofre en (0,81,0). Inicial tapa cerrada; final abierta, jugador en mismo sitio. Direccion de tapa hacia atras/arriba; velocidad de animacion normal, sin rampa; mano gesto corto hacia +Z. Mobs ninguno. Bloques: solo estado visual de tapa. Interaccion real de apertura, particulas ninguna. Iluminacion frontal neutra, hora 6000, despejado, set de llanura; fondo pared mate a 5 bloques. Profundidad mano/cofre/pared, foco tapa. Transicion continua. Aislada: se entiende que abre un contenedor.

**Escena 2.** Mantener interfaz abierta en partida, aunque no se muestre en replay; cofre abierto. Inicial/final sujeto inmovil. Camara avanza 0.4 bloques en 3 s, 0.13 b/s constante; sin aceleracion del jugador. Mobs ninguno, bloques sin otro cambio, particulas ninguna. Misma luz/hora/clima; fondo y profundidad estables. Punto de atencion borde de tapa, no contenido. Transicion: frenar camara con puntos proximos. Aislada: espera de descubrimiento, no prueba de botin.

**Escena 3.** Cerrar interfaz fuera de la vista de camara; tapa regresa. Inicial abierta, final cerrada; sujeto sigue junto al cofre, velocidad normal de tapa y reposo final. Sin mobs, particulas ni otros cambios. Luz, entorno, clima y hora constantes, profundidad de tres planos. Foco tapa cerrandose. Salida por corte; no fundido incrustado. Aislada: cierre neutro util para montaje, no una segunda sorpresa.

#### Camara

Tercera persona oblicua libre. Lente inicial (3,82.5,-4.5), altura 1.5 sobre suelo, distancia ~5.5 al cofre. Orientacion -X/+Z; mirar (0.5,81.6,0.5). Travelling 0.4 bloques hacia sujeto entre f30-119; paneo/tilt solo correctivos menores de 3 grados. Sin zoom, orbita ni seguimiento. Ruta lineal con frenado por espaciado; velocidad 0.13 b/s. FOV 50 -> 50 constante. Camara estable, shake ninguno. Texto arriba y a izquierda, nunca sobre tapa.

#### Composicion vertical

Cofre centro (530,1100), ancho 430-520 px; manos en x=250-700. Texto x=120-860,y=200-460. Evitar zonas de UI derecha/inferior. Fondo: segunda ruta con cofre en y=1290 y pared superior simple. Escena: encuadre principal. Variante izquierda si overlay derecho lo permite, no duplicar por cada target. Mantener tapa entera y no mirar dentro.

#### Shaders y estetica

Shaders apagados, recomendado ninguno. Sombras suaves vanilla, contraste medio, saturacion nativa. Llanura/set, dia 6000, clima claro, sin niebla ni iluminacion artificial necesaria. Un shader oscuro oculta bisagra/tapa; no aporta reutilizacion suficiente.

#### HUD y elementos de interfaz

Ocultar HUD, hotbar, crosshair, chat, nombres, coordenadas, inventario y subtitulos. Particulas excesivas: no agregar. La GUI existe para accionar cofre, pero no debe aparecer en el archivo final ni se requiere que Replay Mod la reproduzca.

#### Audio

Apertura/cierre naturales como Foley separado; acento de apertura objetivo f15-25, cierre despues de f120 segun toma. Ambiente exterior bajo. Video mudo y entendible, sin musica incorporada. Dejar espacio a voz; no efecto de "premio recibido" porque no se muestra ninguno.

#### Preparacion dentro de Minecraft

Set `SET-G01`, cofre vacio y pared sencilla. Mundo laboratorio superflat recomendado, dia/clima bloqueados, sin mobs ni IA. Inventario mano vacia. Orden: construir, comprobar cofre abre sin bloque opaco encima, ensayar encuadre, grabar. 2-4 intentos. Reset: cerrar cofre; no reponer items ni target. No usar el clip como evidencia de que una respuesta aparece en cofres.

#### Instrucciones de Replay Mod

Registrar 3 s previo, apertura, espera y cierre. Marcar apertura real y elegir T0 antes de ella para que ocurra antes de f30. P0 inicial, P1 igual en t=1, P4 adelantada, P6 igual. T0/T6 avanzan seis segundos reales como base. Foco borde de tapa. Repetir solo si brazo o pared tapa apertura. Render vanilla protagonista y reencuadre bajo del mismo replay. La respuesta se añade despues en Remotion, nunca al cofre.

#### Variantes

Protagonista, baja de fondo y corta con una apertura. No primera persona que dependa del inventario; no glow añadido, no mas particulas, no loop falso. No grabar una version por categoria de item.

#### Diseno para Remotion

180 f/30 fps/9:16; `scene`/`reveal`, no loop. `cover` con crop aprobado o `contain` en panel. Sin blur ni mascara en fuente; oscurecimiento solo zona de texto. Mudo. Master 2160x3840 opcional. Sincronizar apertura con expectativa; icono de respuesta como overlay independiente, sin fingir que estaba dentro del cofre.

### G02: Elegir sin saber

#### Identificacion

- ID: `G02`. Nombre corto: Decision.
- Archivo: `mc_decision_routes_choose_thirdrear_vanilla_scene_t01.mp4`.
- Categorias: decision, comparacion, tension, humor; compatible narrativamente con cualquier categoria.
- Principal: jugador. Secundarios: dos accesos iguales, divisor central, iluminacion pareja.
- Emocion: duda seguida de eleccion. Intensidad: 2/5.
- Uso: `background`, `scene`. Duracion 6 s / 180 f. Corta 3 s / 90 f; larga principal. No loop.

#### Idea central

El jugador vacila entre dos opciones visualmente equivalentes y finalmente se compromete con una.

#### Hook

F0: jugador ya entre dos rutas. F0-15: giro rapido de cabeza/cuerpo a izquierda y cambio hacia derecha. Estimulo: decision visible, no paseo. Pregunta: "cual elegirias?". Evitar un camino claramente iluminado y otro mortal: eso volveria trivial la eleccion.

#### Guion por escena

| Escena | Duracion | Inicial | Final | Objetivo narrativo |
|---|---|---:|---:|---|
| 1 | 1 s / 30 f | 0 | 29 | Mostrar opciones y duda |
| 2 | 3 s / 90 f | 30 | 119 | Comprometerse con una ruta |
| 3 | 2 s / 60 f | 120 | 179 | Llegar al umbral y sostener |

**Escena 1.** Jugador inicial (40.5,81,-1.5), final mismo sitio con orientacion cambiada; mira entrada izquierda y derecha sin mover mucho pies. Giros ~35 grados a cada lado, velocidad manual rapida pero legible; aceleracion normal de input. Mobs ninguno, bloques fijos, sin particulas. Dia 6000 claro, luz pareja; set de dos corredores iguales. Fondo paredes grises, profundidad jugador/divisor/finales. Foco cuerpo entre opciones. Continuidad. Aislada: duda identificable.

**Escena 2.** Dar un paso corto hacia izquierda, detenerse y elegir derecha. Inicio centro; final (42.5,81,1.5), segun geometria del set. Movimiento +X/+Z a velocidad de caminar, pausa de 0.3 s y cambio de direccion; no velocidad sobrehumana. Mobs ninguno; bloques y particulas sin cambios. Misma luz, hora, clima y entorno. Fondo simetrico mantiene comparacion, profundidad por umbrales. Foco trayectoria elegida. Transicion continua sin cortar a otra toma. Aislada: eleccion reconocible, sin objetos de respuesta.

**Escena 3.** Detenerse en umbral derecho, mirar hacia el interior. Inicio y final casi iguales, desaceleracion normal y reposo. Mobs ninguno; bloques estables, particulas ninguna. Luz/clima/hora constantes; fondo del corredor elegido visible sin premio. Foco jugador ya orientado. Corte limpio, no revelar "correcto" en Minecraft. Aislada: expectativa abierta para countdown o respuesta posterior.

#### Camara

Tercera persona trasera elevada, lente (40.5,85,-8), altura 4 sobre suelo, distancia ~7 al jugador inicial. Mirar (40.5,82,1), orientacion +Z, tilt descendente. Sin paneo, zoom, travelling, orbita ni seguimiento en base; FOV 60 -> 60. P0/P6 iguales, lineal, velocidad 0, easing no aplica. Estable, sin shake. Mantener ambas rutas en cuadro y franja superior de texto.

Esta ruta base es `scene`, no fondo aprobado para la tarjeta central. Candidata `background`: lente fija (40.5,91,-20), mirada (40.5,86,2), FOV 60. Al mirar por encima del set, jugador y bifurcacion se desplazan hacia la franja baja. Medir en preview: cuerpo, cambio de ruta y ambos umbrales utiles deben quedar entre y=1140-1480 y ser legibles. Si se hacen demasiado pequenos, descartar fondo y usar como escena; no ocultar una accion importante debajo de la tarjeta.

#### Composicion vertical

Composicion `scene` objetivo: jugador en x=500,y=1170; entradas x=280 y x=730, y=800-1250. Este cuadro no sirve detras de la tarjeta central actual. La ruta de fondo alternativa tiene su propia composicion baja y aprobacion pendiente; no basta con llamarla background. Nada importante x>900 o y>1550. Variante de eleccion izquierda util como segunda accion, no necesaria por episodio. Los pixeles son objetivos de encuadre, no una proyeccion garantizada por las coordenadas propuestas.

#### Shaders y estetica

Apagados, ninguno recomendado. Sombras suaves, contraste medio, saturacion vanilla. Dia 6000 claro en llanura, sin niebla. Luz artificial solo si techo hace un lado oscuro; ambas rutas iguales. No usar color rojo/verde para sugerir respuesta sin texto.

#### HUD y elementos de interfaz

Ocultar HUD, hotbar, crosshair, chat, nombres, coordenadas, inventario y subtitulos. Sin particulas añadidas. Mano vacia, skin neutra; ningun numero ni cartel sobre las rutas.

#### Audio

Pasos y roce, Foley separado. Acento suave al cambio de decision hacia f45-65, no golpe de explosion. Ambiente bajo. Funciona en silencio, con huecos para voz y musica. No sonidos de fallo/acierto incrustados.

#### Preparacion dentro de Minecraft

Set `SET-G02`, dos pasillos iguales, sin trampas. Superflat recomendado, sin mobs ni IA, dia/clima bloqueados. Inventario vacio de utileria visible. Orden: construir simetria, marcar ruta mental, ensayar giros, grabar. 3-5 intentos. Reset posicion/orientacion; mundo no cambia. No necesita items de ninguna familia especifica.

#### Instrucciones de Replay Mod

Registrar pausa inicial, giros, paso falso y eleccion. P0/P6 fijos; T0 comienza justo antes del primer giro, no antes de acercarse al cruce. Foco entre rutas, velocidad real. Repetir si un giro no mueve el cuerpo o la ruta sale del recorte. Render fondo y escena desde mismo replay. No agregar leyendas en captura; opciones quedan para Remotion si la plantilla las necesita.

#### Variantes

Camara trasera fija, cenital moderada si mejora lectura, eleccion izquierda opcional. Variante corta elimina la espera final, no la duda. No shader, no camara nerviosa ni loop que haga caminar al reves.

#### Diseno para Remotion

180 f/30 fps/vertical; base `scene`, variante `background` pendiente de preview, no loop. `cover` solo manteniendo dos opciones; `contain` si panel estrecho. Oscurecer zona de titulo, blur ninguno sobre rutas; mascara opcional del panel, no en archivo. Mudo; 4K opcional. Alinear cambio de decision con pregunta o invitacion a elegir, sin atribuir una mecanica al target.

### G03: El suelo deja de ser seguro

#### Identificacion

- ID: `G03`. Nombre corto: Peligro bajo los pies.
- Archivo: `mc_danger_floor_collapse_thirdside_vanilla_scene_t01.mp4`.
- Categorias: peligro, tension, entorno, fracaso aparente.
- Principal: suelo escenografico que cae. Secundarios: jugador, arena fija de utileria, borde seguro.
- Emocion: sorpresa y alivio. Intensidad: 4/5.
- Uso: `scene`, `impact`. Duracion 5 s / 150 f. Corta 2 s / 60 f; larga principal. No loop.

#### Idea central

Un espacio que parecia transitable desaparece justo delante del jugador, que se queda en el borde seguro.

#### Hook

F0: pie del jugador cerca del limite, suelo suspendido visible. F0-15: primer desprendimiento; antes de f24 se abre el hueco. Pregunta: "va a caer?". Evitar matar al jugador, mostrar comandos o afirmar que el item de la adivinanza rompe el suelo.

#### Guion por escena

| Escena | Duracion | Inicial | Final | Objetivo narrativo |
|---|---|---:|---:|---|
| 1 | 1 s / 30 f | 0 | 29 | Suelo comienza a fallar |
| 2 | 2 s / 60 f | 30 | 89 | Hueco y retirada |
| 3 | 2 s / 60 f | 90 | 149 | Confirmar supervivencia sin item salvador |

**Escena 1.** Jugador inicial/final junto a (79,81,1.5), siempre sobre piedra firme. Arena x=80-82,y=80,z=0-2 pierde soporte inferior por trigger escenografico registrado. Bloques caen -Y, aceleracion de gravedad; no se fija altura por frames. Mobs ninguno; particulas nativas, no explosion. Dia 6000 despejado, llanura/set con foso limitado; fondo pared neutra. Profundidad borde/suelo/fondo. Foco linea que se abre. Continuidad. Aislada: peligro espacial evidente.

**Escena 2.** Jugador retrocede un bloque sobre firme; arena cae al fondo del foso, sin afectar plataforma segura. Inicio cerca de borde, final x~78; direccion -X, paso breve rapido y desaceleracion. Mobs ninguno; bloques se asientan por fisica real, particulas naturales. Misma luz, clima y hora; fondo estable y profundidad acentuada por hueco. Foco distancia pie/borde. Continuidad. Aislada: retirada preventiva, no poder especial.

**Escena 3.** Jugador mira abajo y se queda. Posiciones inicial/final iguales, velocidad cero salvo cabeza; bloques reposan, sin mobs ni nuevas particulas. Luz y entorno constantes, foso iluminado para no parecer vacio infinito. Foco hueco y cuerpo. Salida corte limpio, reset fuera de archivo. Aislada: pausa tensa util para decision.

#### Camara

Tercera persona lateral elevada, lente (81.5,84,-8), altura 3 sobre plataforma, distancia 8-10 a accion. Mirada (80.5,79.5,1.5), orientacion +Z y tilt descendente. Sin zoom, travelling, orbita ni seguimiento; paneo ninguno, tilt fijo. P0/P5 iguales, lineal, velocidad 0. FOV 60 -> 60 constante. Estable; shake solo opcional en Remotion 2 px/3 f al desprender, nunca en master. Texto arriba sin tapar borde.

#### Composicion vertical

Jugador x=300,y=1000; hueco x=500-800,y=1050-1400. Un solo foco compuesto: relacion cuerpo/hueco. Titulo arriba; no CTA sobre foso. Fondo no recomendado bajo tarjeta central; variante baja solo si ambos siguen legibles. Escena protagonista base. No recortar el firme y hacer parecer que flota.

#### Shaders y estetica

Apagados, ninguno recomendado. Contraste medio, arena clara contra piedra oscura; saturacion nativa. Dia 6000 claro, sin niebla. Iluminacion artificial en foso si necesario, fuera de cuadro. Evitar sombras negras que oculten profundidad real.

#### HUD y elementos de interfaz

Ocultar HUD, hotbar, crosshair, chat, nombres, coordenadas, inventario y subtitulos. Particulas naturales de bloques, sin extras. No mostrar command block ni operador auxiliar.

#### Audio

Desprendimiento/caida de bloques como Foley separado, golpe objetivo f15-24 y caida posterior segun toma. Ambiente bajo. Video mudo; no explosion TNT ni grito de daño que no ocurre. Espacio libre para narracion de tension.

#### Preparacion dentro de Minecraft

Set `SET-G03`, foso poco profundo, plataforma firme y arena sobre soporte removible. Superflat recomendado; dia/clima fijos; sin mobs ni IA. Inventario no necesario. Orden: construir foso, firme y soporte, colocar arena, probar trigger sin jugador, situar jugador seguro, grabar. 3-6 intentos. Trigger de command block manual opcional para retirar SOLO soporte especificado; no es una mecanica del target, es escenografia. Reset reconstruye soporte y arena fuera de toma.

#### Instrucciones de Replay Mod

Grabar estado previo y caida completa. Si se dispara trigger desde chat, mantener jugador seguro, ocultar GUI en camara libre y comprobar que no aparece mensaje. P0/P5 fijos, foco borde/foso. T0 se elige antes de desprendimiento; tiempo real para caida, no reversa. Repetir si arena cae antes del registro o jugador pisa zona inestable. Exportar limpia; reconstruccion no forma parte del clip.

#### Variantes

Lateral principal, cenital para leer hueco y corta del desprendimiento. Sin muerte, sin victimizar mob, sin item salvador. No mas particulas. No loop: la reconstruccion implicaria otra accion.

#### Diseno para Remotion

150 f/30 fps/9:16; `scene`/`impact`, no loop. `cover` solo con cuerpo y firme dentro; `contain` si panel recorta foso. Sin blur ni mascara; oscurecer solo texto. Mudo, 4K opcional. Sincronizar amenaza con apertura de hueco; no superponer target en mano fingiendo que lo produjo.

### G04: El salto se resuelve

#### Identificacion

- ID: `G04`. Nombre corto: Casi falla.
- Archivo: `mc_motion_gap_jump_thirdside_vanilla_scene_t01.mp4`.
- Categorias: movimiento, tension, satisfaccion, humor.
- Principal: jugador sin equipo especial. Secundarios: dos plataformas y suelo seguro inferior.
- Emocion: incertidumbre seguida de alivio. Intensidad 4/5.
- Uso: `scene`, `impact`. Duracion 5 s / 150 f. Corta 2 s / 60 f; larga principal. No loop.

#### Idea central

El jugador no alcanza la plataforma alta, cae sobre una cornisa inferior y consigue subir con un segundo salto normal, sin objeto salvador.

#### Hook

F0: jugador ya despegando del borde. F0-15: cuerpo va hacia plataforma alta, pero queda corto; antes de f30 o poco despues aterriza en cornisa inferior visible. Pregunta: "fallo o todavia puede subir?". Evitar cuatro segundos de carrera, esconder la cornisa para falsear fisica o afirmar clutch con un item que no aparece.

#### Guion por escena

| Escena | Duracion | Inicial | Final | Objetivo narrativo |
|---|---|---:|---:|---|
| 1 | 1 s / 30 f | 0 | 29 | Salto corto y recepcion inferior |
| 2 | 2 s / 60 f | 30 | 89 | Segundo salto y recuperacion |
| 3 | 2 s / 60 f | 90 | 149 | Reaccion minima de alivio |

**Escena 1.** Jugador sale de plataforma izquierda x=118-120, pies y=81, hacia plataforma alta x=123-126. Su salto corto termina sobre cornisa x=122 con superficie y=80, un bloque mas baja. Inicio en borde; final pies en cornisa, no colgando de una animacion inexistente. Direccion +X/-Y, salto normal sin sprint ajustado en ensayo. Mobs ninguno; bloques inmoviles; particulas nativas discretas. Dia 6000 claro, set abierto, fondo neutro. Profundidad borde/cuerpo/cornisa/plataforma. Foco pies al quedar cortos. Continuidad. Aislada: fallo aparente con apoyo real visible.

**Escena 2.** Desde cornisa (122.5,80,1.5), hacer segundo salto normal hacia plataforma (124.5,81,1.5) y frenar. Inicio mas bajo, final recupera altura original; aceleracion de salto real y desaceleracion al aterrizar. Mobs ninguno, bloques no cambian, particulas solo si se producen. Misma luz, hora/clima, entorno y profundidad. Foco cambio de altura y pies apoyados. Continuidad. Aislada: recuperacion legible, no habilidad de ningun objeto.

**Escena 3.** Jugador gira levemente hacia hueco y hace una unica agachada breve. Inicio/final plataforma derecha, movimiento de postura normal sin traslacion importante. Sin mobs ni cambios de bloques, sin particulas extras. Luz/clima/hora estables, fondo neutro. Foco postura de alivio. Corte limpio, no regreso en reversa. Aislada: remate ligero para CTA.

#### Camara

Tercera persona lateral, lente (122,83,-8), altura 2 sobre plataformas, distancia 9-10 al recorrido. Mira (122,81.8,1.5), orientacion +Z. Base fija, sin paneo/tilt variable, zoom, travelling, orbita o seguimiento. Ruta P0/P5 igual, velocidad 0, easing no aplica. FOV 60 -> 60 constante. Estable; shake opcional de 2 f en Remotion tras aterrizaje. Texto superior libre.

#### Composicion vertical

Despegue x=240,y=1080; destino x=720,y=1080; cornisa baja visible entre ambos hacia y=1230; apice dentro de y=700. Son objetivos a ajustar en preview. Mostrar ambos bordes, cornisa y suelo inferior. Texto y=200-460, nunca sobre pies. Fondo solo si plantilla no oculta recorrido; protagonista recomendada. Segunda toma con direccion inversa opcional, no invertir archivo.

#### Shaders y estetica

Apagados. Contraste medio, saturacion vanilla, sombras suaves. Llanura, dia 6000, despejado, sin niebla ni luz artificial. No lens effects que distorsionen distancia entre bordes.

#### HUD y elementos de interfaz

Ocultar HUD, hotbar, crosshair, chat, nombres, coordenadas, inventario y subtitulos. Sin particulas adicionales. Mano vacia, sin elytra ni efectos de salto; escena no depende de skin.

#### Audio

Pasos y dos aterrizajes, Foley separado; primer contacto objetivo f25-40 y segundo dentro de f45-89 segun ensayo. Ambiente exterior bajo. Mudo funcional, sin grito ni fanfarria horneada. Dejar palabra de acierto para segundo aterrizaje, no confundir apoyo inferior con final del reto.

#### Preparacion dentro de Minecraft

Set `SET-G04`, gap basico, cornisa un bloque mas baja y suelo firme inferior. No hace falta resistencia ni vuelo. Superflat, supervivencia, sin mobs/IA, dia/clima fijos. Inventario mano vacia. Orden: construir, ensayar caer sobre cornisa y subir un bloque, comprobar ambos contactos, grabar. 4-8 intentos. Reset teleport al inicio. No ajustar dano ni efectos para falsear exito; si no sale, ensanchar cornisa conservando el cambio de altura.

#### Instrucciones de Replay Mod

Registrar primer salto, apoyo inferior, segundo salto y postura final. T0 se elige en primer despegue. P0/P5 fijos; foco incluye cornisa y destino. Tiempo real; no cortar un apoyo para fingir salvacion imposible. Repetir cuando pies no apoyan claramente. Corta solo si conserva ambos apoyos; de lo contrario usar principal. Slow motion solo rerender de replay con duracion nueva, no promesa de fisica mas lenta.

#### Variantes

Lateral principal, primera persona como complemento si muestra ambos bordes, corta del salto. Variante baja no prioritaria si pierde causa. Sin shaders, sin loop ni multiplicacion de particulas.

#### Diseno para Remotion

150 f/30 fps/vertical; `scene`/`impact`. `cover` preservando bordes, `contain` si panel estrecho. No loop, blur ni mascara necesarios. Oscurecimiento localizado superior. Mudo; master 4K opcional para ajustes leves. Sincronizar resolucion de voz con aterrizaje, no el despegue.

### G05: Algo pasa demasiado cerca

#### Identificacion

- ID: `G05`. Nombre corto: Esquiva.
- Archivos: `mc_danger_projectile_dodge_thirdoblique_vanilla_pass_t01.mp4` (30 f) y `mc_danger_projectile_dodge_thirdside_vanilla_result_t01.mp4` (90 f). El clip editorial de 120 f se arma en Remotion, sin hornear el corte.
- Categorias: peligro, velocidad, proyectiles, transicion narrativa.
- Principal: trayectoria de flecha de utileria. Secundarios: jugador, pared receptora, dispensador fuera de cuadro.
- Emocion: amenaza inmediata. Intensidad 4/5.
- Uso: `impact`, `transition`, `scene`. Duracion 4 s / 120 f. Corta 2 s / 60 f; larga principal. No loop.

#### Idea central

Un proyectil cruza cerca de la camara y el jugador se aparta, sin asociar esa accion al objeto que se esta adivinando.

#### Hook

F0: linea de tiro preparada con cuerpo ligeramente a un lado. F0-15: flecha se aproxima y cruza cerca de lente. Impacto en pared antes de f30. Pregunta: "le dio?". Evitar un disparo lejano de dos pixeles o un golpe que realmente hiera al jugador cuando el guion dice esquiva.

#### Guion por escena

| Escena | Duracion | Inicial | Final | Objetivo narrativo |
|---|---|---:|---:|---|
| 1 | 1 s / 30 f | 0 | 29 | Paso de proyectil y esquiva |
| 2 | 1 s / 30 f | 30 | 59 | Confirmar impacto en pared |
| 3 | 2 s / 60 f | 60 | 119 | Mantener tension sin otro disparo |

**Escena 1.** Dispensador dispara hacia +X desde (156,82,0), jugador en carril seguro z=1.8 se aparta hasta z=2.8. Inicial flecha en salida, final pasa junto a lente rumbo a pared x=165, que queda detras de esta primera camara. Direcciones +X para flecha y +Z para jugador; velocidad real, paso rapido sin rampa falsa. Mobs ninguno, bloques no se destruyen, particulas naturales. Dia 6000 claro, set abierto, fondo pasillo. Profundidad proyectil/cuerpo/origen; foco pasada. Transicion: corte a segunda camara en Remotion en f30, no paneo de 180 grados. Aislada: amenaza legible; el resultado se confirma en plano siguiente.

**Escena 2.** Segunda camara muestra flecha ya clavada en pared tras pasada. Jugador a salvo gira cabeza si entra en periferia, sin exigir encuadrarlo junto al macro del impacto. Flecha quieta; movimientos de cabeza normales. Mobs ninguno; bloques estables, sin explosion ni particulas extras. Misma luz/hora/clima y entorno, nueva perspectiva de pared. Foco flecha clavada. Continuidad con escena 3 en esta camara. Aislada: confirmacion de impacto en pared, no cuerpo.

**Escena 3.** Sostener plano, cuerpo quieto. Sin traslacion/aceleracion ni otra flecha; mobs ninguno, bloques sin cambios, particulas ninguna. Luz y ambiente constantes, pared da fondo simple. Foco relacion cuerpo/impacto. Corte limpio; no disparo oculto durante salida. Aislada: fondo tenso breve, no loop.

#### Camara

Dos camaras libres estables, ambas tercera persona. A, pasada: lente (164,82.6,1.2), altura 1.6 sobre suelo, mira (156.5,82.3,0.5), orientacion -X; queda lateralmente apartada de linea de tiro z~0.5. Distancia al jugador ~3.5 bloques. B, resultado: lente (161.5,83,-6), altura 2, mira (165,82.2,0.5), orientacion +X/+Z, distancia ~7.4 al impacto. No unir A y B con spline: dos renders e insert en Remotion. Paneo, tilt variable, zoom, travelling, orbita y seguimiento: ninguno. Keyframes identicos por cada plano, velocidad cero, easing no aplica. FOV 65 -> 65 en A, 55 -> 55 en B. Sin shake. Primera persona es variante opcional ensayada, no base.

#### Composicion vertical

Plano A: cuerpo lateral y trayectoria hacia zona central, sin overlay sobre pasada. Plano B: flecha en pared grande y centrada x~540,y~1050; cuerpo opcional en borde si cabe, sin fingir que debe verse completo. Texto arriba en ambos. Ajustar pixeles en preview. Fondo no recomendado para lectura larga. Close-pass puede funcionar solo como transicion; no se le exige mostrar impacto que esta detras de su lente.

#### Shaders y estetica

Apagados. Contraste alto entre flecha y pared, saturacion nativa. Dia claro 6000 en llanura/set, sin niebla; luz artificial si interior demasiado oscuro. No motion blur horneado que borre proyectil ni shader con DOF.

#### HUD y elementos de interfaz

Ocultar HUD, hotbar, crosshair, chat, nombres, coordenadas, inventario y subtitulos. Particulas naturales; no trails artificiales. En primera persona, manos solo si replay las representa; no depender del HUD.

#### Audio

Foley de disparo/paso/impacto separado. Paso en f5-15, impacto objetivo f15-30 segun toma. Ambiente bajo. Mudo debe funcionar; no hitmarker sonoro ni daño inexistente. Dejar acento breve y espacio para voz.

#### Preparacion dentro de Minecraft

Set `SET-G05`, dispensador y pared, carril del jugador separado fisicamente de linea de tiro. Inventario del dispensador: flechas; jugador mano vacia. Sin mobs/IA; superflat, dia/clima fijos. Orden: probar linea sin jugador, marcar carril seguro, preparar pulso unico, ensayar apartarse, grabar. 5-10 intentos. Reset quitar flechas solo del set y recargar. No usar selector global que borre entidades ajenas.

#### Instrucciones de Replay Mod

Registrar trigger, trayectoria y pared final, jugador fuera de linea peligrosa. Render A: 0-29 f, posicion fija A; render B: 30-119 f del mismo intervalo real, posicion fija B. Keyframes temporales de B comienzan un segundo despues de los de A; no repetir disparo ni fingir dos eventos. Confirmar que pasada esta en A y flecha clavada en B; si no, mover limites y documentar nuevos frames manteniendo total de montaje. Exportar dos fuentes limpias y ensamblar solo en Remotion. Repetir si proyectil invisible o contacto con jugador. La camara libre no controla entidades.

#### Variantes

Tercera persona base; primera persona de espectador si se lee esquiva; corta; close-pass para transicion. No distintos proyectiles por cada episodio: flecha de utileria fija. Excluir cuando muestre el target exacto o contradiga la pista.

#### Diseno para Remotion

Dos fuentes verticales a 30 fps: A de 30 f y B de 90 f; montaje de 120 f, `impact`/`transition`, no loop. Usar A en f0-29 y B en f30-119 mediante secuencias, sin archivo con corte horneado. `cover` solo con accion visible, `contain` si se perderia. Sin blur; mascara solo para montaje. Texto superior, oscurecimiento local minimo. Mudo; master 4K opcional. Alinear acento con pasada/impacto real; no etiquetar como evidencia de todas las armas.

### G06: El mundo era mucho mas grande

#### Identificacion

- ID: `G06`. Nombre corto: Escala.
- Archivo: `mc_scale_structure_reveal_thirdfree_vanilla_scene_t01.mp4`.
- Categorias: escala, descubrimiento, poder, espacio; soporte narrativo amplio.
- Principal: construccion abstracta de gran altura. Secundarios: jugador pequeño, borde cercano, suelo.
- Emocion: asombro por tamaño. Intensidad 3/5.
- Uso: `scene`, `reveal`, `background` abierto. Duracion 6 s / 180 f. Corta 3 s / 90 f; larga principal. No loop.

#### Idea central

La camara sale de detras de un borde cercano y revela una estructura enorme junto a un jugador pequeño.

#### Hook

F0: textura de pared cercana y una franja del fondo. F0-15: travelling lateral descubre la base; antes de f30 aparece escala completa. Pregunta: "que tan alto es?". Evitar cinco segundos de dron lento o construir la silueta de un item especifico.

#### Guion por escena

| Escena | Duracion | Inicial | Final | Objetivo narrativo |
|---|---|---:|---:|---|
| 1 | 1 s / 30 f | 0 | 29 | Abrir escala por oclusion |
| 2 | 3 s / 90 f | 30 | 119 | Comparar humano y construccion |
| 3 | 2 s / 60 f | 120 | 179 | Sostener espacio para reveal |

**Escena 1.** Camara se desplaza 2 bloques lateralmente desde pared cercana; jugador fijo en (199,81,7), delante y a izquierda de base, fuera de bloques solidos. Estructura llega hasta y=103. Sujeto inicial parcialmente oculto, final visible entero. Movimiento +X de lente a ~2 b/s, desacelerar al final; jugador quieto. Mobs ninguno; bloques fijos, particulas ninguna. Dia 6000 despejado, llanura, fondo cielo y pared lejana. Profundidad borde/columna/cielo, foco relacion figura/altura. Continuidad. Aislada: reveal de escala, no estatua de respuesta.

**Escena 2.** Camara casi quieta, pequeño tilt hacia coronacion sin perder base. Inicio/final jugador fijo; lente puede subir 0.5 bloques en 3 s, 0.17 b/s. Mobs ninguno; bloques/particulas sin cambios. Luz/hora/clima constantes, fondo simple, profundidad conservada. Foco construccion completa, no una textura. Transicion frenada. Aislada: tamaño comprensible por figura humana visible.

**Escena 3.** Sostener cuadro; jugador gira levemente cabeza hacia arriba. Movimiento minimo y luego reposo; sin mobs, cambios de bloques ni particulas. Mismo ambiente, luz y hora, profundidad constante. Foco silueta total. Salida corte limpio, sin gran flare. Aislada: fondo amplio para nombre o categoria, no prueba de tamaño del target.

#### Camara

Tercera persona libre, lente inicial (197,89,-14), altura 8 sobre suelo; final lateral (199,89,-14), mirada (200.5,91,8.5). Distancia ~23 al centro. Travelling lateral primer segundo, tilt maximo 6 grados despues; sin zoom, orbita ni seguimiento. Ruta lineal y puntos mas cercanos al frenar, evitar spline atravesando pared. FOV 65 -> 65. Camara estable, sin shake. Margen superior para titulo fuera de coronacion; alternativa texto lateral.

#### Composicion vertical

Construccion x=430-720,y=420-1430; jugador cerca de x=460,y=1380. Texto a izquierda arriba, no sobre referencia humana. Fondo: abrir encuadre y desplazar columna a derecha, sin cortarla por UI. Escena principal tiene mayor escala aparente. Segunda variante baja solo si conserva coronacion y base.

#### Shaders y estetica

Dos versiones: vanilla y shaders suaves opcionales. Candidato: Complementary Reimagined con Iris compatible, perfil bajo, DOF/motion blur apagados, compatibilidad exacta pendiente. Sombras suaves, contraste medio, saturacion vanilla. Dia 6000 claro; niebla leve solo si no elimina coronacion; sin luz artificial. No convertir contraste en silueta negra. Variante cinematico-nocturna no necesaria para biblioteca basica.

#### HUD y elementos de interfaz

Ocultar HUD, hotbar, crosshair, chat, nombres, coordenadas, inventario y subtitulos. Sin particulas extras. Jugador sin equipo distintivo ni nombre visible; funciona con cualquier skin sencilla.

#### Audio

Ambiente de viento separado bajo; acento corto al descubrir estructura objetivo f20-30. No rugido de jefe ni explosion inexistente. Video funciona mudo y deja gran espacio para voz/musica. No musica de trailer incorporada.

#### Preparacion dentro de Minecraft

Set `SET-G06`, columna/torre abstracta, borde cercano separado de camara y suelo seguro. Superflat recomendado, sin mobs/IA, dia/clima fijos. Inventario no necesario. Orden: construir estructura y borde, cargar todos los chunks, poner jugador de escala, ensayar ruta. 2-4 intentos. Reset posicion del jugador; mundo estatico. La estructura puede acompañar muchos items sin representarlos literalmente.

#### Instrucciones de Replay Mod

Registrar jugador quieto y mirada breve, escenario completo cargado. P0 detras de borde, P1 desplazada, P4 levemente alta, P6 igual. Tiempo real; el hook depende de ruta, no de accionar un objeto. Foco medio de estructura, ajustar pitch manualmente para conservar base y cima. Repetir ruta si hay clipping. Render vanilla scene y fondo abierto; shader opcional del mismo replay tras comparar legibilidad.

#### Variantes

Protagonista, fondo lateral, corta de apertura y shader suave opcional. No orbita completa ni primera persona imprescindible. No escalas falsas por zoom animado no soportado. No construir otra torre por target.

#### Diseno para Remotion

180 f/30 fps/vertical, `scene`/`reveal`, no loop. `contain` preferible si panel cortaria escala, `cover` solo en 9:16 aprobado. Sin blur; oscurecer zona de texto, no figura humana. Sin mascara en fuente. Mudo, 4K util si se preve crop leve. Sincronizar descubrimiento visual con cambio de escena o categoria, nunca con dato de tamaño de un item no mostrado.

### G07: Se abre un espacio para la respuesta

#### Identificacion

- ID: `G07`. Nombre corto: Acceso revelado.
- Archivo: `mc_reveal_passage_open_thirdfront_vanilla_scene_t01.mp4`.
- Categorias: reveal, redstone de utileria, misterio, recompensa; cualquier respuesta como overlay separado.
- Principal: panel movil que descubre nicho. Secundarios: piston pegajoso, palanca, pedestal vacio.
- Emocion: resolucion visual. Intensidad 3/5.
- Uso: `reveal`, `scene`. Duracion 6 s / 180 f. Corta 3 s / 90 f; larga principal. No loop en base.

#### Idea central

Una pared se retira y deja un espacio vacio que Remotion puede acompañar con cualquier respuesta sin grabarla en Minecraft.

#### Hook

F0: panel cierra un nicho, borde de mecanismo visible. La palanca esta fuera del encuadre principal: no se exige verla ni se atribuye la accion al target. F0-15: operador quita energia y comienza retirada; antes de f30 hueco abierto. Pregunta: "que habia detras?". Evitar item/texto en pedestal, falso glow o afirmar una causa mecanica que el plano no demuestra.

#### Guion por escena

| Escena | Duracion | Inicial | Final | Objetivo narrativo |
|---|---|---:|---:|---|
| 1 | 1 s / 30 f | 0 | 29 | Abrir panel |
| 2 | 3 s / 90 f | 30 | 119 | Mantener nicho abierto con camara fija |
| 3 | 2 s / 60 f | 120 | 179 | Sostener espacio de respuesta |

**Escena 1.** Operador fuera de cuadro quita energia con palanca junto a set x=240. Panel se retira un bloque por piston; inicial hueco tapado, final apertura visible. Direccion -X, velocidad redstone real; operador permanece fuera del foco. Mobs ninguno; bloques movil/piston cambian estado, sin particulas extra. Set techado, luz neutra auxiliar, exterior 6000/despejado. Fondo nicho vacio mate, profundidad panel/nicho/pared. Foco borde que descubre. Continuidad. Aislada: se abre espacio, no se crea objeto; no pretende explicar circuito completo.

**Escena 2.** Camara permanece fija y operador no entra en cuadro. Apertura y nicho no cambian de tamano; velocidad cero. Mobs ninguno; mecanismo abierto, sin nuevos cambios ni particulas. Luz/hora/clima constantes; profundidad simple para alojar overlay sin tracking 3D. Foco vacio central. Continuidad a reposo. Aislada: espacio para respuesta editorial; este hold es deliberado, no un segundo hook.

**Escena 3.** Camara quieta, nicho vacio sostenido. Inicio/final iguales, velocidad cero; bloques estables, mobs/particulas ninguno. Misma luz y entorno, fondo limpio. Foco centro del nicho. Corte de salida limpio, no cierre automatico ni fundido horneado. Aislada: fondo de reveal para cualquier categoria compatible.

#### Camara

Tercera persona frontal libre fija. Lente (241.5,82.8,-6), altura 1.8 sobre suelo, mirada (241.5,82,1.5), orientacion +Z, distancia ~7.5. Sin travelling, paneo, tilt variable, orbita, seguimiento ni zoom; FOV 50 -> 50. P0/P6 iguales, velocidad cero, easing no aplica. Estable, sin shake. Palanca en x=238 y operador x=237.5 fuera de cuadro por diseño; el panel es el foco. Texto arriba e icono independiente despues de apertura. A diferencia de G01, no hay acercamiento lento ni cierre: es un fondo estable para reveal.

#### Composicion vertical

Apertura/pedestal x=330-730,y=700-1300. Texto y=200-460; nombre de respuesta en zona inferior segura si plantilla lo permite. Fondo: encuadre fijo abierto con nicho mas bajo; escena principal para apertura. No requiere segunda variante por item. No hacer parecer que el overlay es un objeto fisico perfectamente trackeado si no lo es.

#### Shaders y estetica

Apagados. Contraste medio, saturacion vanilla, sombras suaves. Set Overworld techado, exterior dia 6000 claro, sin niebla. Luz artificial oculta ilumina nicho, no halo coloreado. Shaders pueden crear pulsos de exposicion al abrir: evitar en base.

#### HUD y elementos de interfaz

Ocultar HUD, hotbar, crosshair, chat, nombres, coordenadas, inventario y subtitulos. Sin particulas añadidas ni item frames con contenido. Jugador fuera del centro, mano sin target.

#### Audio

Palanca/piston naturales en pista separada, golpe objetivo f15-24 ajustado al evento real. Ambiente interior bajo. Video mudo y comprensible. Campana de reveal pertenece a Remotion; no musica ni sonido especifico del target en captura.

#### Preparacion dentro de Minecraft

Set `SET-G07`, piston pegajoso y panel de un bloque, nicho/pedestal vacios. Superflat, dia/clima bloqueados, sin mobs/IA. Inventario mano vacia. Orden: montar circuito simple y comprobar extension/retraccion, construir marco sin bloquear piston, iniciar cerrado, grabar apertura. 3-6 intentos. Reset con palanca fuera de toma, no `/setblock` frente a camara. No inventar una puerta compleja si un panel simple cumple el objetivo.

#### Instrucciones de Replay Mod

Registrar mecanismo cerrado, accion y al menos 5 s abierto. P0/P6 identicos, sin desplazamiento. T0 antes del trigger; T6 seis segundos despues, apertura temprana. Foco nicho. Repetir si operador aparece o piston no retrae panel. Exportar limpio, sin target. Remotion coloca respuesta como capa separada. La corta de 90 f se usa cuando el hold de 6 s no aporta al montaje.

#### Variantes

Principal apertura, fondo abierto fijo, corta de 90 f. Cierre como otro intervalo solo si sirve para transicion, no invertido. No shaders ni particulas innecesarias; no primera persona que oculte mecanismo.

#### Diseno para Remotion

180 f/30 fps/9:16; `reveal`/`scene`, no loop. `cover` con nicho entero, `contain` para panel distinto. Sin blur, mascara opcional para layout, no embebida. Oscurecimiento local de texto; mudo. Master 4K util para reencuadre, no obligatorio. Sincronizar icono/nombre despues de apertura real; no antes ni como falso loot del target.

### G08: Buscar con intencion

#### Identificacion

- ID: `G08`. Nombre corto: Busqueda.
- Archivo: `mc_search_room_scan_thirdtop_vanilla_scene_t01.mp4`.
- Categorias: curiosidad, busqueda, ritmo de pistas; utilidad narrativa transversal.
- Principal: jugador. Secundarios: tres estantes/vacios y un nicho lateral, sin items de respuesta.
- Emocion: "esta cerca, pero todavia no". Intensidad 2/5.
- Uso: `background`, `scene`. Duracion 6 s / 180 f. Corta 3 s / 90 f; larga principal. No loop.

#### Idea central

El jugador inspecciona dos lugares y detecta un tercer espacio oculto, sin resolverlo con un objeto particular.

#### Hook

F0: cenital oblicua con jugador ya girando junto a primer estante. F0-15: giro decidido y paso al segundo; antes de f30 la geometria revela que hay otro nicho. Pregunta: "donde esta?". Evitar caminar sin proposito, hacer diez giros nerviosos o llenar paredes de objetos identificables.

#### Guion por escena

| Escena | Duracion | Inicial | Final | Objetivo narrativo |
|---|---|---:|---:|---|
| 1 | 1 s / 30 f | 0 | 29 | Primera inspeccion y cambio |
| 2 | 3 s / 90 f | 30 | 119 | Segunda inspeccion y descubrimiento del nicho |
| 3 | 2 s / 60 f | 120 | 179 | Detenerse ante nueva posibilidad |

**Escena 1.** Jugador en (280.5,81,0.5) mira estante vacio izquierdo y gira hacia segundo. Inicial cuerpo al lado izquierdo, final centro del set; direccion +X corta, velocidad caminar, aceleracion normal. Mobs ninguno; bloques fijos, particulas ninguna. Dia 6000 claro, sala abierta por arriba, fondo estantes de piedra sin texto. Profundidad cenital por alturas de estantes y suelo. Foco cuerpo y punto de inspeccion. Continuidad. Aislada: busqueda intencional, no paseo.

**Escena 2.** Dar dos pasos hacia segundo estante y girar al nicho compacto al verlo junto al divisor. Inicial centro, final (282.5,81,3.5); direccion +Z/+X, pausa corta y giro ~60 grados, sin sprint. Mobs ninguno; bloques/particulas sin cambios. Misma luz/clima/hora; fondo geometrico, profundidad por divisor. Foco orientacion hacia nicho en (283.5,81.5,5.5). Transicion continua. Aislada: otra opcion, no target.

**Escena 3.** Desde (282.5,81,3.5), desplazarse primero +X a x=283.5 y luego +Z hasta z=4.5, rodeando divisor sin atravesarlo. Detenerse antes del pedestal z=5, sin GUI ni recogida. Velocidad caminar y desaceleracion natural. No mobs, cambios de bloques ni particulas. Luz/entorno constantes, nicho legible. Foco espacio vacio. Corte antes de resolver. Aislada: suspenso ligero, no item especifico.

#### Camara

Tercera persona cenital oblicua libre; lente (282,91,-4), altura 10 sobre suelo, mirada (282,81.5,3.5). Set compactado a x=279-285: nicho en x=283, no en x=286 fuera de encuadre. Orientacion +Z, tilt descendente, no cenital perfecta. Sin paneo, zoom, travelling, orbita ni seguimiento; P0/P6 iguales, velocidad cero, easing no aplica. FOV 65 -> 65. Estable, sin shake. Esta ruta es `scene`. Candidata fondo: lente (282,95,-18), mirada (282,89,3), FOV 60 fijo, para desplazar accion a franja baja; someter a prueba con tarjeta y descartar si cuerpo/nicho quedan pequenos u ocultos.

#### Composicion vertical

Escena: tres puntos dentro de x=220-780,y=750-1350 como objetivo ajustable; jugador suficientemente grande para leer giro. Este encuadre queda parcialmente tapado por tarjeta central y NO es fondo aprobado. La candidata fondo debe reunir toda informacion relevante en y=1140-1480 sin compartir CTA. Si no se lee, usar como `scene` y dejar para fondo una accion mas simple, no achicarla indefinidamente. No informacion esencial fuera de UI; variante lateral si cenital pierde postura.

#### Shaders y estetica

Apagados. Sombras suaves que expliquen paredes, contraste medio, saturacion vanilla. Llanura/set abierto, 6000, despejado, sin niebla; luces artificiales solo para nicho si negro. Evitar DOF que borre estantes secundarios necesarios para la busqueda.

#### HUD y elementos de interfaz

Ocultar HUD, hotbar, crosshair, chat, nombres, coordenadas, inventario, subtitulos. Sin particulas extras. Estantes sin carteles, marcos con objetos ni etiquetas; utileria neutra.

#### Audio

Pasos separados y ambiente de sala bajo. Acento de descubrimiento opcional en giro al nicho cerca de f90-110, no al azar. Video mudo funcional. No sonidos de loot, magia o llave inexistentes; espacio continuo para narracion.

#### Preparacion dentro de Minecraft

Set `SET-G08`, dos estantes vacios y nicho detras de divisor, sin techo que tape cenital. Superflat recomendado, sin mobs/IA, dia/clima fijos, inventario mano vacia. Orden: construir geometria simple, ensayar ruta corta, revisar orientacion de cabeza desde arriba, grabar. 3-5 intentos. Reset jugador al primer estante, escenario estatico. No fabricar receta visual ni coleccion del target.

#### Instrucciones de Replay Mod

Registrar inspeccion continua de 6 s con margenes. T0 al primer giro, no antes de entrar a sala. P0/P6 fijos; foco centro de las tres posiciones. Tiempo real, no aceleracion 3x para ocultar caminata lenta. Repetir si no se lee la pausa o divisor tapa cuerpo. Render fondo y protagonista, mismas acciones sin cambiar props por episodio.

#### Variantes

Cenital oblicua base, lateral abierta si mejora postura y corta con dos inspecciones. No shaders necesarios, no mas particulas, no loop de caminar al reves. Variante sujeto derecho para texto izquierdo si el set cabe entero.

#### Diseno para Remotion

180 f/30 fps/vertical; `background`/`scene`, no loop. `cover` si tres posiciones sobreviven crop, `contain` si no. Blur nunca sobre lugares de inspeccion; oscurecimiento solo zona de texto, mascara opcional del panel. Mudo, 4K opcional. Sincronizar cambio de pista con giro de busqueda, no con una falsa propiedad del item.

### G09: La esquina no estaba vacia

#### Identificacion

- ID: `G09`. Nombre corto: Aparicion.
- Archivo: `mc_mystery_corner_appear_thirdfree_vanilla_scene_t01.mp4`.
- Categorias: misterio, peligro, mob de utileria, suspenso.
- Principal: aparicion por oclusion. Secundarios: zombie fijo de utileria, esquina, luz lateral.
- Emocion: sorpresa y amenaza. Intensidad 4/5.
- Uso: `scene`, `impact`. Duracion 5 s / 150 f. Corta 2 s / 60 f; larga principal. No loop.

#### Idea central

Una camara cruza una esquina y descubre una presencia que ya estaba alli, sin necesitar una persecucion impredecible.

#### Hook

F0: esquina ocupa parte de cuadro y deja ver pasillo aparentemente vacio. F0-15: camara se desplaza; antes de f30 aparece rostro/cuerpo del mob. Pregunta: "que hay ahi?". Evitar empezar con el mob ya totalmente visible o mantener un segundo negro para crear un susto.

#### Guion por escena

| Escena | Duracion | Inicial | Final | Objetivo narrativo |
|---|---|---:|---:|---|
| 1 | 1 s / 30 f | 0 | 29 | Descubrir presencia |
| 2 | 2 s / 60 f | 30 | 89 | Sostener amenaza legible |
| 3 | 2 s / 60 f | 90 | 149 | Retirada leve, sin persecucion |

**Escena 1.** Zombie en (321.5,81,2.5), IA bloqueada, oculto por divisor desde P0. Inicial no visible, final cuerpo descubierto por camara que recorre 3.5 bloques +X, de x=318.5 a x=322, manteniendo z=-2. Velocidad media 3.5 b/s con frenado final; mob sin traslacion. Bloques inmoviles, particulas ninguna. Interior techado, luz lateral neutra, exterior 6000/despejado. Fondo pasillo, profundidad esquina/mob/pared. Foco rostro. Continuidad. Aislada: sorpresa visual sin contexto.

**Escena 2.** Camara quieta frente al mob, que no ataca ni se mueve hacia lente; IA bloqueada. Inicio/final posiciones iguales, velocidad cero. Bloques estables, sin particulas. Misma hora/clima, techo evita quemadura solar; luz mantiene cuerpo legible. Profundidad por pasillo. Foco presencia, no item en mano. Transicion por comienzo de retirada de camara. Aislada: tension, no demostracion de conducta natural del zombie.

**Escena 3.** Camara retrocede 0.5 bloques y mantiene presencia dentro de cuadro. Mob fijo; direccion lente -Z aproximadamente segun ruta, velocidad 0.25 b/s, frenado suave. Sin otras entidades, cambios de bloques ni particulas. Iluminacion/clima/hora estables, fondo y profundidad constantes. Foco mob aun visible. Corte limpio, no oscuridad completa al final. Aislada: respiro tenso util antes de una respuesta.

#### Camara

Tercera persona libre sin jugador visible. Lente inicial (318.5,82.6,-2), altura 1.6 sobre suelo; final de reveal (322,82.6,-2), mirada (321.5,82,2.5). Distancia ~4.5 al mob. Travelling lateral 3.5 bloques en primer segundo y retirada a z=-2.5 al final. Paneo correctivo hacia rostro, tilt casi constante, sin zoom/orbita/seguimiento de IA. Ruta lineal fuera del divisor: P1 debe quedar en x=322, no x=319.5 que aun oculta al mob. FOV 55 -> 55. Estable, sin shake. Probar inicio oculto y final visible antes de ajustar velocidad.

#### Composicion vertical

Mob x=600,y=1000, cuerpo entero entre y=580-1430; esquina a izquierda. Titulo arriba izquierda, no sobre rostro. Escena completa recomendada. Fondo variante fija con mob lateral solo si no distrae de lectura; excluir si el mob es target o pista anticipada. No ocultar cuerpo en negro para fingir seguridad de spoilers.

#### Shaders y estetica

Dos versiones: vanilla primero y shader suave opcional, Complementary Reimagined con perfil bajo compatible pendiente. Sombras medias, contraste moderado, saturacion nativa, sin DOF ni motion blur. Interior oscuro pero legible, exterior fijo; niebla adicional ninguna. Luz artificial lateral fuera de cuadro. Si shader borra ojos/cuerpo o mete bloom, descartarlo.

#### HUD y elementos de interfaz

Ocultar HUD, hotbar, crosshair, chat, nombres, coordenadas, inventario y subtitulos. Particulas excesivas ninguna. Mob sin nombre visible ni equipo que añada otra pista; no GUI ni item frames.

#### Audio

Ambiente bajo y sonido natural de mob opcional separado. Acento de aparicion objetivo f20-30, no pico excesivo ni susto dependiente de volumen. Mudo debe funcionar. Si sonido identifica demasiado al target, no usarlo. Espacio para voz y musica posterior.

#### Preparacion dentro de Minecraft

Set `SET-G09`, pasillo techado y esquina, zombie con etiqueta de set, sin IA y persistente. No requiere combate ni invulnerabilidad del jugador. Dificultad no pacifica para conservarlo. Superflat con construccion temporal, dia/clima fijos. Orden: sala/techo, luz, summon fuera de toma, ajustar oclusion, registrar. 2-5 intentos. Reset posicion o eliminar solo mob etiquetado de ese set. Es puesta en escena, no prueba de comportamiento natural.

#### Instrucciones de Replay Mod

Registrar escenario con mob ya colocado; aparicion depende de camara, no summon dentro del clip. P0 oculta, P1 descubre, P3 igual, P5 retrocede 0.5. Tiempo real; foco rostro, no recorrer pasillo entero. Repetir ruta si clipping o mala luz, no cambiar mob por cada target. Render vanilla scene; shader opcional y corta desde mismo replay.

#### Variantes

Base aparicion, corta y fondo lateral condicionado. Variante sin mob con sombra geometrica puede ampliar usos, pero no venderla como la misma accion ni añadir ojos falsos. No mas particulas, no ataque simulado, no loop salvo otro diseño.

#### Diseno para Remotion

150 f/30 fps/vertical, `scene`/`impact`, no loop. `cover` conserva rostro/cuerpo, `contain` si panel lo corta. Sin blur en sujeto, oscurecimiento solo texto; mascara ninguna en fuente. Audio mudo. 4K opcional. Alinear aparicion con acento de tension; no usar junto a pista de origen incompatible ni asumir neutralidad por ser una escena general.

### G10: Reaccion de acierto sin mostrar la respuesta

#### Identificacion

- ID: `G10`. Nombre corto: Lo logre.
- Archivo: `mc_reaction_player_celebrate_thirdfront_vanilla_scene_t01.mp4`. Variante `loop` solo despues de aprobar continuidad.
- Categorias: recompensa, cierre, satisfaccion, loop condicionado; cualquier categoria de respuesta.
- Principal: jugador con manos vacias. Secundarios: plataforma neutra, pared mate.
- Emocion: satisfaccion humana simple. Intensidad 2/5.
- Uso: `background`, `loop` tras validar, `scene`. Duracion 4 s / 120 f. Corta 2 s / 60 f; larga principal. No inventar animacion de victoria inexistente.

#### Idea central

Un salto corto y una agachada comunican celebracion con movimientos reales de Minecraft, sin levantar trofeos ni usar el target.

#### Hook

F0: jugador comenzando salto, cuerpo entero visible. F0-15: ascenso y gesto claro. Pregunta implicita: "acertaste tambien?". Evitar postura inmovil, emotes de mods o animacion de brazos que Minecraft no permite reproducir.

#### Guion por escena

| Escena | Duracion | Inicial | Final | Objetivo narrativo |
|---|---|---:|---:|---|
| 1 | 1 s / 30 f | 0 | 29 | Salto corto de celebracion |
| 2 | 1 s / 30 f | 30 | 59 | Agachada y vuelta a postura |
| 3 | 2 s / 60 f | 60 | 119 | Reposo y cierre compatible con loop |

**Escena 1.** Jugador en (360.5,81,0.5), salta vertical sin avanzar ni sostener salto para repetir. Inicio despegue, final aterrizando segun fisica. Direccion +Y/-Y, aceleracion real, sin efectos de salto. Mobs ninguno; bloques fijos; particulas vanilla solo si aparecen. Dia 6000 claro, llanura/set, pared mate a distancia. Profundidad jugador/plataforma/pared, foco cuerpo. Continuidad. Aislada: celebracion simple, no poder de item.

**Escena 2.** Tras aterrizar, una agachada breve y volver a erguirse. Inicio/final misma posicion de pies, movimiento vertical corto de postura, velocidad manual normal sin rampa. Mobs ninguno, bloques sin cambios, particulas ninguna añadida. Misma luz/clima/hora y entorno; fondo quieto. Foco postura. Transicion continua. Aislada: gesto humano reconocible sin texto.

**Escena 3.** Quedarse quieto y con orientacion inicial; no levantar mano con emote. Velocidad cero, misma posicion final; bloques/mobs/particulas sin eventos. Luz fija y fondo simple, profundidad constante. Foco cuerpo y espacio de texto. Salida corte; loop solo si ultimo estado coincide con comienzo antes del despegue sin salto perceptible. Aislada: fondo de CTA. Si no cierra, usar archivo no loopable.

#### Camara

Tercera persona frontal fija; lente (360.5,82.6,-5.5), altura 1.6 sobre suelo, mirada (360.5,82,0.5), orientacion +Z; distancia 6 bloques. Sin paneo, tilt variable, zoom, travelling, orbita ni seguimiento. P0/P4 iguales, velocidad cero, easing no aplica. FOV 50 -> 50 constante. Estable, shake ninguno. Espacio superior amplio, pies y apice dentro.

#### Composicion vertical

Jugador x=560,y=1090, cuerpo entre y=700-1450 incluyendo salto. Texto y=200-460 y lado izquierdo si se requiere. Fondo: jugador a x=700 y tamaño moderado, zona de CTA no debe cubrir pies. Escena: centrado. Segunda variante izquierda aporta reuso; no cambiar skin/item por episodio.

#### Shaders y estetica

Apagados, ninguno recomendado. Sombras suaves, contraste medio, saturacion nativa. Dia 6000 claro, llanura/set, sin niebla, luz artificial no necesaria. Fondo sin agua, fuego o follaje moviendose para facilitar loop. Shader no aporta valor basico.

#### HUD y elementos de interfaz

Ocultar HUD, hotbar, crosshair, chat, nombres, coordenadas, inventario y subtitulos. Sin particulas de victoria añadidas. Mano vacia, skin sencilla cualquiera. No logo ni numero grabado.

#### Audio

Paso/aterrizaje como Foley separado opcional; golpe suave en contacto real antes de f35. Ambiente bajo. Mudo completamente funcional, sin fanfarria ni musica incrustada. El CTA hablado y campana de acierto se mezclan despues.

#### Preparacion dentro de Minecraft

Set `SET-G10`, plataforma plana y fondo estatico. Sin mobs/IA, efectos ni equipo; superflat, dia/clima bloqueados. Inventario mano vacia. Orden: colocar marca mental, ensayar salto/agachada sin desplazamiento, grabar. 3-6 intentos. Reset posicion/orientacion. No requiere comandos de animacion ni mods de emotes. El clip expresa reaccion, no certifica exito de una accion anterior inexistente.

#### Instrucciones de Replay Mod

Registrar varios ciclos con 2 s de reposo entre ellos. Elegir uno y conservar estado inicial/final. P0/P4 fijos, tiempo real; foco torso y pies. T0 justo antes de salto; si union no coincide, reencuadrar o marcar no loop, no invertir. Revisar idle de brazos, sombra y particulas en la costura. Exportar primero `scene`; usar nombre `loop` solo para variante con continuidad aprobada.

#### Variantes

Frontal protagonista, sujeto derecho/izquierdo para texto, corta. Loop solo aprobado tras ver varias repeticiones; alternativa no ciclica siempre disponible. No shader, emote, mas particulas ni primera persona que oculte reaccion.

#### Diseno para Remotion

120 f/30 fps/9:16; `background`, `loop` condicional. `cover` conserva pies/apice; `contain` para panel. Sin blur ni mascara en fuente, oscurecimiento localizado para texto. Mudo; 4K opcional. CTA/reaccion tras revelar respuesta independiente; no superponer item en mano como si se hubiese grabado. Reutilizable con todas las categorias tras comprobar spoilers de utileria.

## 6. Variantes recomendadas

### Reencuadrar no es volver a grabar

Grabar una accion y obtener otra camara desde Replay Mod es la principal economia del sistema. Un cambio de encuadre no necesita nuevo episodio, nueva skin ni nuevo item. Una segunda accion solo se justifica cuando cambia realmente la utilidad: por ejemplo, ruta izquierda/derecha, o comer/beber.

| Escena | Entrega imprescindible | Segunda entrega util | No producir por defecto |
|---|---|---|---|
| G01 | Apertura protagonista | Cofre bajo para texto | Cofre con cada respuesta dentro |
| G02 | Decision con dos rutas visibles | Eleccion contraria o cenital | Pasillos con iconos de cada item |
| G03 | Firme, hueco y jugador juntos | Cenital o corta | Muertes, explosion o item salvador |
| G04 | Salto lateral claro | Corta o primera persona | Otra herramienta/armadura por episodio |
| G05 | Proyectil y pared | Close-pass o primera persona | Un proyectil por cada arma del catalogo |
| G06 | Escala completa vanilla | Fondo abierto; shader suave si mejora | Esculturas de todos los targets |
| G07 | Apertura/nicho vacio | Nicho abierto fijo para reveal | Objetos de respuesta sobre pedestal |
| G08 | Busqueda cenital legible | Lateral baja para texto | Estantes con recetas por item |
| G09 | Aparicion vanilla | Corta o shader suave legible | Sustituir mob por cada target |
| G10 | Reaccion frontal | Sujeto a derecha/izquierda | Trofeos y emotes no reproducibles |

### Cortas, largas y lentas

- Cortas: extraer evento y resultado del master, ajustar `eventFrame` y duracion; no dejar un clip de 60 f con 45 f de espera.
- Largas: conservar tiempo de lectura real del resultado. No rellenar con camara sin proposito ni congelar una flecha en vuelo como gameplay normal.
- Lentas: renderizar de nuevo desde replay con mapeo temporal definido; documentar velocidad. No suponer que un MP4 a 30 fps contiene suficientes imagenes para slow motion suave.
- Rapidas: como regla editorial inicial, probar 1.1-1.25x para desplazamientos, pero conservar mecanicas/impactos legibles. No hay velocidad universal aprobada.
- Primera persona: conservar solo si ayuda a entender una accion directa; no por tener una casilla que completar.
- Mas particulas: no se ofrece como variante basica. Las particulas de una mecanica deben permanecer naturales.
- Loop: validar continuidad de sombras, idle, botones, entidades y estado del mundo. G10 puede necesitar quedar no ciclico; C16 es candidato mas controlable.

### Metadatos de variantes

Todas las variantes del mismo replay comparten `sourceReplayId`, pero tienen archivos, duraciones, hashes y crops propios. Evitar dos usos consecutivos de la misma fuente como si fueran tomas distintas. No espejar automaticamente escenas: puede falsear direcciones de mecanismos, manos o referencias del mundo.

## 7. Mundos, construcciones y preparaciones

### Mundo A: laboratorio de escenas generales

Un unico mundo creativo superflat de Java 1.21.11 basta para preparar G01-G10. El terreno por defecto del superflat puede estar a otra altura: los sets de esta guia construyen su propia plataforma y=80; no presuponen que el suelo natural este alli.

Separacion horizontal por zonas de 40 bloques. La region de cada set debe reservarse vacia antes de usar `/fill`. Nada de comandos de preparacion en mundos valiosos. Guardar una copia manual del mundo de rodaje antes de construir o resetear sets.

| Set | Centro aproximado X | Construccion | Props/entidades | Reinicio |
|---|---:|---|---|---|
| G01 | 0 | Plataforma, pared, cofre | Cofre vacio | Cerrar tapa |
| G02 | 40 | Dos accesos, divisor, suelo uniforme | Ninguno especial | Posicion/orientacion jugador |
| G03 | 80 | Foso, borde firme, soporte y arena | Arena, trigger opcional | Restaurar soporte y arena |
| G04 | 120 | Dos plataformas, gap y suelo inferior | Ninguno especial | Teleport al inicio |
| G05 | 160 | Dispensador, pared receptora y carril lateral | Flechas | Limpiar solo flechas del set y recargar |
| G06 | 200 | Columna abstracta, borde de oclusion | Jugador para escala | Posicion jugador |
| G07 | 240 | Nicho de un bloque, piston lateral, palanca | Panel, pedestal vacio | Volver a cerrar con palanca |
| G08 | 280 | Estantes vacios, divisor y nicho sin techo | Ninguno especial | Posicion jugador |
| G09 | 320 | Pasillo techado, esquina, luz | Zombie etiquetado sin IA | Reposicionar o reemplazar solo ese zombie |
| G10 | 360 | Plataforma/pared estatica | Jugador sin equipo | Posicion/orientacion |

El panel de G07 es una **ventana/nicho de un bloque**, no una puerta de dos bloques de altura para atravesar. La funcion es revelar un espacio, no permitir que el jugador pase. Esto evita un circuito complicado innecesario.

### Mundo B: entornos contextuales

Mundo normal separado, misma version. Marcar lugares para: bosque/cultivo, cueva iluminada, oceano con suelo legible, aldea, estructura descubierta. No hacen falta todos los biomas para cubrir narrativamente todas las plantas o bloques: el contexto es opcional.

Para C12/C15 preparar una ruta que conserve cargados todos los chunks visibles. Replay Mod no inventa terreno que nunca quedo registrado. Esperar a que el entorno y entidades terminen de cargar antes de iniciar accion.

### Nether y End

Son dimensiones reales del mundo de rodaje, no decorados teñidos. Preparar plataformas seguras y rutas cortas antes de capturar. No hacer una spline que atraviese un portal como si el render cambiara de dimension automaticamente. Grabar ambos lados y dejar el corte a Remotion.

No se requiere combatir un jefe para la base de treinta escenas. Escala, vacio y estructuras cubren el tono de progresion sin introducir un rodaje dificil por cada objeto raro.

### Orden de preparacion comun

1. Crear copia de trabajo del mundo y confirmar que no contiene construcciones ajenas.
2. Confirmar Java 1.21.11, perfil de mods y ejecutable FFmpeg accesible a Replay Mod; hacer replay/render MP4 de prueba de 2 s.
3. Construir solo el set que se va a usar, comprobar dimensiones y luz.
4. Preparar objetos, IA y estado inicial fuera de toma.
5. Ensayar la accion en partida sin camara compleja; asegurar resultado real y posibilidad de reset.
6. Grabar varias tomas con pausas de separacion, sin menus ni comandos dentro del intervalo util.
7. Crear ruta de camara y seleccionar tiempo real del evento; renderizar preview vertical.
8. Aprobar protagonista antes de extraer fondos, cortas o shaders.

## 8. Lista de comandos de Minecraft

### Alcance y estado de validacion

**No se ejecutaron estos comandos dentro de Minecraft.** Son preparaciones propuestas para Java 1.21.11; la sintaxis de bloque/entidad y el funcionamiento del montaje deben ensayarse en un mundo descartable. Si el juego rechaza una propiedad, detenerse y verificar autocompletado de 1.21.11; no corregirla copiando NBT de otra version al azar.

Los comandos `/fill`, `/setblock`, `/kill` y `/tp` pueden modificar o borrar elementos. Aqui solo deben utilizarse en las regiones reservadas del mundo de rodaje. No ejecutar `kill @e`, no limpiar inventarios globalmente ni modificar un servidor publico. Los resets son comandos manuales entre tomas, nunca parte del clip final.

Ejecutar los bloques SET en Overworld; el bloque base cambia explicitamente a esa dimension. No ejecutarlos despues de visitar Nether/End sin repetir ese cambio. Las coordenadas son absolutas. Dentro de un command block, quitar la barra inicial de `/fill`.

### BASE: antes de construir

```mcfunction
/gamemode creative @s
/execute in minecraft:overworld run tp @s 0 90 -8
/gamerule minecraft:advance_time false
/gamerule minecraft:advance_weather false
/gamerule minecraft:spawn_mobs false
/time set 6000
/weather clear
```

Las tres gamerules usan los IDs documentados para 1.21.11. No usar `doDaylightCycle`, `doWeatherCycle` o `doMobSpawning` de guias anteriores. `spawn_mobs=false` evita aparicion natural; no elimina mobs existentes ni impide necesariamente invocaciones explicitas. No desactivar daño para una toma que pretenda demostrar seguridad fisica.

### SET-G01: cofre sin respuesta

```mcfunction
/fill -6 80 -6 6 80 8 minecraft:stone_bricks
/fill -5 81 6 5 86 6 minecraft:gray_concrete
/setblock 0 81 0 minecraft:chest[facing=north]
/tp @s 0.5 81 -0.5 0 15
```

Usar mano vacia, abrir y cerrar normalmente. No hace falta `/give` de la respuesta. Reset manual: cerrar interfaz y comprobar tapa cerrada. La camara libre evita depender de la reproduccion del inventario.

### SET-G02: decision entre rutas

```mcfunction
/fill 34 80 -6 46 80 8 minecraft:stone_bricks
/fill 34 81 0 34 84 7 minecraft:gray_concrete
/fill 46 81 0 46 84 7 minecraft:gray_concrete
/fill 40 81 1 40 84 6 minecraft:gray_concrete
/fill 34 81 7 46 84 7 minecraft:gray_concrete
/tp @s 40.5 81 -1.5 0 0
```

El divisor no debe impedir entrar por izquierda/derecha. Usar paredes y luz equivalentes. Reset: repetir solo `/tp`, no reconstruir toda sala.

### SET-G03: desprendimiento escenografico

```mcfunction
/fill 74 80 -5 79 80 6 minecraft:stone_bricks
/fill 80 75 0 82 75 2 minecraft:stone_bricks
/fill 80 76 0 82 78 2 minecraft:air
/fill 80 79 0 82 79 2 minecraft:stone
/fill 80 80 0 82 80 2 minecraft:sand
/tp @s 79 81 1.5 -90 25
```

Trigger de una sola caida, desde chat o command block de impulso con boton fuera de cuadro:

```mcfunction
/fill 80 79 0 82 79 2 minecraft:air
```

Reset fuera de toma, solo despues de que termine toda caida:

```mcfunction
/fill 80 76 0 82 80 2 minecraft:air
/fill 80 79 0 82 79 2 minecraft:stone
/fill 80 80 0 82 80 2 minecraft:sand
/tp @s 79 81 1.5 -90 25
```

El jugador permanece sobre x<=79, nunca sobre arena. La retirada del soporte es escenografia por comando, no propiedad de un item ni detonacion real. Si se requiere demostrar solo supervivencia natural, usar G04 en lugar de presentar este trigger como accion del target.

### SET-G04: salto basico

```mcfunction
/fill 116 77 -2 128 77 5 minecraft:stone_bricks
/fill 116 80 0 120 80 3 minecraft:stone_bricks
/fill 123 80 0 128 80 3 minecraft:stone_bricks
/fill 122 79 0 122 79 3 minecraft:stone_bricks
/tp @s 118.5 81 1.5 -90 0
/gamemode survival @s
```

Ensayar salto corto hasta cornisa x=122, superficie y=80; segundo salto sube un bloque a plataforma x=123, superficie y=81. No es record ni animacion de agarrarse al borde. Suelo inferior limita caida si falla; comprobar salud antes de repetir. Reset `/tp` al inicio. Para construir otro set, volver a creativo. Sin efectos de salto ni vuelo.

### SET-G05: linea de proyectil controlada

```mcfunction
/gamemode creative @s
/fill 154 80 -3 167 80 5 minecraft:stone_bricks
/fill 165 81 -2 165 85 4 minecraft:gray_concrete
/setblock 156 81 0 minecraft:stone_bricks
/setblock 156 82 0 minecraft:dispenser[facing=east]
/give @s minecraft:arrow 64
/give @s minecraft:stone_button 1
/tp @s 160.5 81 1.8 90 0
```

Llenar dispensador manualmente con flechas. El boton es opcional para probar sin jugador en el carril; para un operador solo en su marca usar el pulso de abajo. El tiempo de vuelo y apartarse se ensaya, no se garantiza por frames. Carril del jugador z>=1.8 separado del eje z~0.5. No confiar en creativo como prueba de esquiva: confirmar en replay que no hay contacto.

Pulso individual desde el chat, con jugador ya en marca. Primero retirar energia durante preparacion; despues esperar 3 s de margen y colocar bloque de redstone para disparar una vez. Al enviar el comando, cerrar chat y apartarse. No son dos comandos que deban ejecutarse a la vez:

```mcfunction
/setblock 156 82 -1 minecraft:air
```

```mcfunction
/setblock 156 82 -1 minecraft:redstone_block
```

El bloque de redstone alimenta el dispensador por su lateral; solo hay un disparo al recibir energia. Es trigger escenografico, no habilidad del target. Dejar fuente de trigger fuera del encuadre util o elegir inicio despues de su colocacion manteniendo la pasada temprana. Si no se logra una reaccion visible a tiempo, repetir ensayo; no fingirla mediante un corte que cambie el hecho.

Reset de proyectiles SOLO en esta caja del set:

```mcfunction
/setblock 156 82 -1 minecraft:air
/kill @e[type=minecraft:arrow,x=154,y=80,z=-3,dx=13,dy=6,dz=8]
/tp @s 160.5 81 1.8 90 0
```

### SET-G06: construccion abstracta de escala

```mcfunction
/fill 192 80 -18 210 80 14 minecraft:stone_bricks
/fill 200 81 8 202 103 10 minecraft:stone_bricks
/fill 197 81 8 205 81 10 minecraft:stone_bricks
/fill 195 81 -10 197 94 -10 minecraft:gray_concrete
/tp @s 199 81 7 0 -25
```

La pared cercana es oclusion de camara, no la estructura protagonista. Posicion exacta de lente debe ajustarse en preview para que la salida lateral descubra base y cima. No agregar forma de espada, diamante ni item. Reset solo jugador.

### SET-G07: nicho movil sencillo

Montaje de una ventana de un bloque: piston en x=239 empuja panel de x=240 a x=241; al retraerlo, x=241 queda libre. Esto NO construye una puerta de altura de jugador.

```mcfunction
/fill 235 80 -6 246 80 7 minecraft:stone_bricks
/fill 240 81 1 240 84 1 minecraft:gray_concrete
/fill 242 81 1 243 84 1 minecraft:gray_concrete
/setblock 241 81 1 minecraft:gray_concrete
/fill 240 83 1 243 84 1 minecraft:gray_concrete
/fill 240 81 5 243 84 5 minecraft:gray_concrete
/setblock 241 81 3 minecraft:stone_bricks
/setblock 242 83 4 minecraft:sea_lantern
/setblock 239 82 1 minecraft:sticky_piston[facing=east]
/setblock 240 82 1 minecraft:stone_bricks
/setblock 238 82 1 minecraft:lever[face=wall,facing=west]
/tp @s 237.5 81 0.5 -90 0
```

Accionar palanca manualmente para **extender y cerrar** antes de grabar. El panel debe ocupar (241,82,1). En toma, quitar energia para **retraer y abrir**. Verificar que la palanca adherida alimenta piston y que ninguna decoracion bloquea desplazamiento. Si el montaje no funciona en 1.21.11, revisar estados/conexion antes de rodar; no animar panel por `/setblock` para fingir piston funcional. Reset con palanca, fuera de toma.

### SET-G08: sala de busqueda sin target

```mcfunction
/fill 276 80 -4 288 80 9 minecraft:stone_bricks
/fill 279 81 1 280 82 1 minecraft:gray_concrete
/fill 283 81 1 284 82 1 minecraft:gray_concrete
/fill 282 81 4 282 83 5 minecraft:gray_concrete
/fill 283 81 6 285 83 6 minecraft:gray_concrete
/setblock 283 81 5 minecraft:stone_bricks
/tp @s 280.5 81 0.5 90 10
```

Sin techo sobre trayectoria cenital. Estantes son volumenes simples vacios, no bibliotecas que sugieran encantamiento. Nicho compactado a x=283 para quedar dentro del plano. El jugador rodea divisor por z=3.5 y luego x=283.5, sin atravesar paredes. Reset jugador, no contenidos por episodio.

### SET-G09: aparicion por oclusion

```mcfunction
/fill 314 80 -5 328 80 8 minecraft:stone_bricks
/fill 324 81 0 324 85 7 minecraft:gray_concrete
/fill 318 81 0 320 85 0 minecraft:gray_concrete
/fill 318 81 7 324 85 7 minecraft:gray_concrete
/fill 318 85 0 324 85 7 minecraft:stone_bricks
/setblock 323 83 5 minecraft:sea_lantern
/difficulty normal
/summon minecraft:zombie 321.5 81 2.5 {NoAI:1b,PersistenceRequired:1b,Rotation:[180.0f,0.0f],Tags:["clip_g09"]}
```

NBT mostrado como propuesta que requiere prueba en 1.21.11; confirmar entidad inmovil, sin equipo aleatorio relevante y rostro hacia -Z, donde esta la camara. `Rotation` fija esa orientacion inicial para que `NoAI` no deje al mob de espaldas. Si aparece armadura/item, descartar esa toma o retirar equipo manualmente fuera del clip con sintaxis verificada; no asumir que todo summon sale identico. No usar dificultad pacifica: puede eliminar al mob. El techo evita sol directo.

Limpieza antes de un nuevo summon, SOLO entidad etiquetada de esta caja:

```mcfunction
/kill @e[type=minecraft:zombie,tag=clip_g09,x=314,y=80,z=-5,dx=14,dy=8,dz=13]
```

La camara libre revela por movimiento; el mob no se invoca en toma ni necesita atacar. `NoAI` es puesta en escena: no presentar el clip como comportamiento natural de persecucion.

### SET-G10: reaccion neutra

```mcfunction
/fill 355 80 -4 365 80 8 minecraft:stone_bricks
/fill 355 81 6 365 86 6 minecraft:gray_concrete
/tp @s 360.5 81 0.5 180 0
/gamemode survival @s
```

Quitar equipo/objetos visibles manualmente en el mundo de rodaje. Salto unico sin avance, agachada y reposo. No `/effect`, emotes ni animaciones externas. Reset con `/tp`. Si un loop no cierra por idle, usar no loopable o grabar otro ciclo.

### Kits opcionales para contextuales

Estos `/give` son inventario de rodaje fijo, no instrucciones de cambiar el prop por cada respuesta. No ejecutar todos si no se va a grabar esa familia.

```mcfunction
/give @s minecraft:iron_pickaxe 1
/give @s minecraft:iron_axe 1
/give @s minecraft:stone_bricks 64
/give @s minecraft:furnace 1
/give @s minecraft:coal 16
/give @s minecraft:raw_iron 16
/give @s minecraft:enchanting_table 1
/give @s minecraft:bookshelf 16
/give @s minecraft:anvil 1
/give @s minecraft:bread 16
/give @s minecraft:potion 1
/give @s minecraft:iron_chestplate 1
/give @s minecraft:oak_boat 1
/give @s minecraft:minecart 1
/give @s minecraft:rail 64
/give @s minecraft:powered_rail 16
/give @s minecraft:bow 1
/give @s minecraft:snowball 16
```

`/give ... potion` sin componentes no garantiza el efecto que se quiera mostrar. Definir y verificar una pocion concreta en inventario creativo antes de C07/C08; este documento no inventa sintaxis de componentes ni asocia color con efecto. Una pocion sin efecto sirve para beber como gesto, pero no para demostrar un estado.

Tormenta opcional de contexto C08:

```mcfunction
/weather thunder
```

No garantiza un rayo inmediato ni que ocurra en cuadro. Ensayar una toma real o usar solo lluvia como estado atmosferico. No escribir "evento natural" sobre un rayo invocado. Restablecer con `/weather clear` fuera de toma.

### Mecanicas que no deben copiarse de guias viejas

- Gamerules 1.21.11 usan IDs nuevos; consultar nota oficial [F01].
- Camara de Replay Mod no atrae mobs ni simula un segundo jugador [F02].
- GUI/inventarios no son base fiable de un replay; no diseñar reparacion/crafting dependiente de su reproduccion [F02].
- No incluir mecanicas exclusivas de items como nuevas tareas de esta biblioteca. Si una preparacion introduce una mecanica no verificada, investigar solo esa dependencia para 1.21.11 y marcar el ensayo pendiente.

### Fuentes y trazabilidad

| ID | Fuente | Uso y limite |
|---|---|---|
| F01 | https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-11 | Version objetivo, cambios de gamerules; no prueba de los sets |
| F02 | https://www.replaymod.com/docs/ y https://www.replaymod.com/download/ | Keyframes, espectador, render y disponibilidad 1.21.11; probar combinacion de mods |
| F08 | https://minecraft.wiki/w/Falling_Block y https://minecraft.wiki/w/Sand | Fisica de suelo del set; el trigger sigue siendo escenografia |
| F09 | https://minecraft.wiki/w/Piston y https://minecraft.wiki/w/Lever | Mecanismo de nicho; no certificacion de montaje por coordenadas |
| F10 | https://minecraft.wiki/w/Dispenser y https://minecraft.wiki/w/Arrow | Proyectil y activacion; trayectoria necesita ensayo |
| F11 | https://github.com/ReplayMod/ReplayMod/issues/53 y https://github.com/ReplayMod/ReplayMod/issues/952 | No asumir keyframes nativos de FOV |
| F12 | https://github.com/ReplayMod/ReplayMod/issues/903 y https://github.com/ReplayMod/ReplayMod/issues/815 | Limites de audio y GUI; no depender de addons no permitidos |
| Local | `public/mc-assets/README.md`, `public/mc-assets/item-assets/`, `public/mc-assets/entity-assets/` | Referencias visuales, no certificacion mecanica de 1.21.11 |

Las paginas actuales de Wiki pueden incorporar versiones posteriores. Registrar durante ensayo la version exacta y condiciones; si una fuente contradice 1.21.11, la nota de version y la prueba local prevalecen. No marcar como `probado` algo que solo se leyo.

## 9. Convencion de nombres de archivos

Patron:

```text
mc_<categoria>_<elemento-o-familia>_<accion>_<camara>_<variante>.mp4
```

`elemento-o-familia` describe utileria o funcion general, NO el target de cada episodio. `variante` puede contener tokens de estetica, encuadre y toma. Todo minuscula ASCII, sin espacios, acentos ni nombres comerciales.

| Campo | Vocabulario recomendado |
|---|---|
| categoria | discovery, decision, danger, motion, scale, reveal, search, mystery, reaction, workshop, redstone, environment |
| elemento-o-familia | container, routes, floor, gap, projectile, structure, passage, room, corner, player, equipment |
| accion | open, choose, collapse, jump, dodge, reveal, scan, appear, celebrate, prepare, cycle |
| camara | firstperson, thirdfront, thirdrear, thirdside, thirdtop, thirdoblique, thirdfree |
| variante | vanilla_scene_t01, vanilla_bgleft_t01, vanilla_bgright_t01, vanilla_short_t01, soft_scene_t01, vanilla_loop_t01 |

Ejemplos:

```text
mc_decision_routes_choose_thirdrear_vanilla_scene_t01.mp4
mc_reveal_passage_open_thirdfront_vanilla_scene_t01.mp4
mc_reaction_player_celebrate_thirdfront_vanilla_bgright_t01.mp4
mc_danger_projectile_dodge_thirdoblique_vanilla_short_t01.mp4
```

Guardar la version en metadata y carpeta de perfil, no cambiar todos los nombres por episodio. Estructura propuesta para biblioteca externa al Git de codigo:

```text
gameplay-library/
  java-1.21.11/
    replays/G01/session-t01.mcpr
    camera-paths/G01/
    masters/G01/
    approved/G01/mc_discovery_container_open_thirdoblique_vanilla_scene_t01.mp4
    audio/G01/
    reports/G01/
```

El nombre `approved` se usa solo despues de QA; no mover alli clips automaticamente por tener buen nombre o puntaje. La ubicacion definitiva y montaje de volumen se implementaran aparte. No guardar grandes MP4 dentro de Git ni presumir que el Docker productivo ya monta esa biblioteca.

## 10. Checklist de grabacion

- [ ] Perfil Java 1.21.11 confirmado; lista/version exacta de mods registrada.
- [ ] Replay corto de prueba exportado correctamente con resolucion vertical y 30 fps.
- [ ] FFmpeg localizado y configurado para Replay Mod en la maquina de captura, no solo en Remotion.
- [ ] Mundo de rodaje separado, copia disponible y region del set reservada.
- [ ] Mecanica/accion ensayada sin camara compleja y sin depender de un item del episodio.
- [ ] Inventario de utileria fijo; respuesta exacta ausente del set.
- [ ] Set inicial, hora y clima restaurados antes de cada toma.
- [ ] Chunks cargados, entidades correctas, ningun mob accidental ni sombra extraña.
- [ ] Jugador sin nombres visibles, logos de skin o equipo innecesario.
- [ ] HUD, hotbar, crosshair, chat, coordenadas, inventario y subtitulos fuera de entrega.
- [ ] Sonido separado o video mudo; musica del juego desactivada.
- [ ] Tres segundos de margen en replay, pero accion inmediata en archivo de uso.
- [ ] Evento fuerte antes de 1.5 s al seleccionar intervalo final.
- [ ] Un solo foco; causa y resultado no tapados por cuerpo, pared, blur o particulas.
- [ ] Prueba de encuadre protagonista antes de hacer variante fondo.
- [ ] Ruta de Replay Mod guardada; keyframes de tiempo y posicion separados y documentados.
- [ ] FOV constante anotado, sin dependencia de un zoom nativo no disponible.
- [ ] Al menos una toma con resultado limpio y 2 s finales reutilizables cuando el guion los pide.
- [ ] Reset y comandos fuera del intervalo util; limpieza limitada al set.
- [ ] Metadatos de elementos visibles, mecanicas implicitas y restricciones completados.
- [ ] No se genero una nueva toma solo porque cambio el target del quiz.

## 11. Checklist de control de calidad

### Tecnico

- [ ] Archivo decodifica completo, sin frames corruptos ni cortes truncados.
- [ ] 1080x1920, 9:16, 30 fps constantes; duracion coincide con `durationInFrames`.
- [ ] Sin duplicar un frame final por error de exportacion; sonido no alarga duracion accidentalmente.
- [ ] Sin musica, textos, subtitulos, logos, nombres o transiciones horneadas.
- [ ] Color SDR consistente entre vanilla/shader; nada de negros empastados ni reflejos que borren sujeto.
- [ ] No chunks vacios, clipping de camara ni entidades que aparecen por carga tardia.
- [ ] `cover` no elimina causa/contacto/resultado; `contain` usado cuando corresponde.
- [ ] Si es loop, revisar al menos tres ciclos con movimiento e iluminacion, no solo comparar primer/ultimo JPG.
- [ ] Audio separado con timestamp de evento; el video es comprensible silenciado.

### Editorial y generalidad

- [ ] Puede acompañar por lo menos tres categorias diferentes sin cambiar props, si esta marcado general.
- [ ] No exige volver a grabar cuando cambia el item de respuesta.
- [ ] Se puede explicar su accion con un verbo general: elegir, buscar, esquivar, abrir, saltar, revelar, reaccionar.
- [ ] Si la idea central exige una mecanica exclusiva, rechazarla para esta biblioteca; no reciclarla como contextual.
- [ ] Hook antes de 1.5 s y accion entendible sin voz.
- [ ] Un solo foco principal y motivo para seguir mirando hasta la resolucion.
- [ ] Inicio no incluye la caminata de preparacion ni una placa vacia.
- [ ] Final no requiere cortar una accion esencial ni invertir fisica.
- [ ] Estilo reconocible de Minecraft; no toda toma depende de shader, explosion o orbita.
- [ ] Version fondo probada con overlays reales del formato, no solo area segura teorica.
- [ ] La accion sigue siendo visible a tamaño de telefono, no un personaje de 30 px.
- [ ] El contexto no implica una receta, drop, origen, encantabilidad o propiedad falsa del target.
- [ ] No se adelantan pistas mediante utileria, bioma, mob, sonido distintivo o silueta.
- [ ] Cada uso registra `narrative`, `context` o `evidence`; `evidence` necesita hecho y version verificados.
- [ ] Si no existe combinacion segura, elegir otra general o conservar visual actual; nunca forzar un clip por llenar pantalla.

### Evaluacion automatizable, sin falsas promesas

Un futuro analizador puede separar tres resultados:

| Capa | Herramienta posible | Resultado fiable/limite |
|---|---|---|
| Tecnica | ffprobe/ffmpeg | Resolucion, fps, decodificacion, negros, congelaciones candidatas; no "viralidad" |
| Editorial | Revision humana o modelo de video/vision | Claridad, accion, zonas de texto y etiquetas, con incertidumbre y timestamps |
| Rendimiento | Analitica de publicaciones comparables | Retencion y finalizacion reales, no garantias por puntaje |

Una hoja de contacto ayuda a composicion y contenido, pero no permite juzgar por si sola timing, fluidez, audio ni un loop. Revisar tambien el video a velocidad real. Una cueva oscura, plano fijo o clip de 2 s no se rechaza automaticamente: puede cumplir su funcion. Las reglas tecnicas detectan candidatos a problema, no sustituyen criterio editorial.

Rubrica inicial por funcion, no ranking universal de todos los clips:

| Criterio editorial | Peso orientativo | Evidencia exigida |
|---|---:|---|
| Claridad sin audio | 25 | Causa y resultado identificables |
| Hook temprano | 20 | Timestamp del primer evento significativo |
| Reutilizacion real | 20 | Tres usos/categorias posibles sin nueva captura |
| Encuadre e integracion | 20 | Preview con overlays y crop de destino |
| Resolucion y ritmo | 15 | Final util, sin espera ni movimiento gratuito |

La puntuacion es una ayuda de orden, no un umbral cientifico. Rechazo o revision obligatoria ante falso gameplay, spoiler contextual, incompatibilidad de version, archivo roto o accion oculta. Incluso un clip de 95/100 no puede saltarse esas comprobaciones. Registrar por que y en que frames falla, no solo un numero.

### Flujo propuesto de aprobacion

```text
Replay y toma
  -> validacion tecnica
  -> preview protagonista sin audio
  -> revision de generalidad y elementos visibles
  -> preview con overlays de Remotion
  -> aprobacion humana inicial
  -> biblioteca reutilizable
  -> seleccion contextual por episodio
  -> analitica de publicaciones y rotacion
```

No se ha implementado este flujo ni un selector automatico en esta tarea. La aprobacion del clip no equivale a aprobacion para todos los episodios. Conservar revision contextual final, especialmente si el target coincide con un elemento visible.

## 12. Que diez clips grabar primero

### Orden por mejora visual y esfuerzo

| Orden | Escena | Por que conviene primero | Entrega inicial |
|---:|---|---|---|
| 1 | G02 Decision | Sin mobs/mecanismos, util para preguntas y countdown | Scene 6 s; fondo solo tras validar variante baja |
| 2 | G10 Reaccion | Cierre humano reutilizable para casi cualquier categoria | Scene 4 s; loop si pasa QA |
| 3 | G01 Descubrimiento | Accion familiar, sencilla y clara sin GUI en salida | Scene 6 s |
| 4 | G08 Busqueda | Da movimiento entre pistas sin demostrar una propiedad falsa | Scene 6 s; fondo bajo sujeto a preview |
| 5 | G04 Salto | Fallo aparente y recuperacion sin item especial | Scene 5 s |
| 6 | G06 Escala | Cambia ritmo visual con un set estatico y otra camara | Scene 6 s |
| 7 | G07 Acceso revelado | Fondo de respuesta independiente del item | Reveal 6 s |
| 8 | G03 Suelo inestable | Peligro generico potente, reset limitado y controlable | Impact/scene 5 s |
| 9 | G05 Esquiva | Proyectil hacia lente, contraste con planos tranquilos | Impact 4 s |
| 10 | G09 Aparicion | Misterio sin persecucion; requiere mas cuidado semantico | Scene 5 s |

El orden prioriza esfuerzo y reuso, no se confunde con el orden de escenas dentro de un episodio. No insertar los diez en cada reel.

### Ejemplos de montaje sin grabar por item

Los siguientes son esquemas narrativos, no afirmaciones mecanicas de las respuestas:

| Tipo de episodio | Hook | Fondo de pistas | Decision | Reveal/cierre |
|---|---|---|---|---|
| Item cualquiera | G04 salto | G08 busqueda + G02 decision | Otro tramo/fuente elegible sin repeticion inmediata | G07 nicho + icono exacto; G10 reaccion |
| Bloque/material | G06 escala | C02 taller si compatible, si no G08 | G02 | G07 + asset exacto |
| Comida/pocion | G01 descubrimiento | C07 solo si ilustracion compatible; general si no | G02 | G10 + respuesta separada |
| Arma/herramienta | G05 esquiva si no spoilea | C01/C18 solo con contexto validado; si no G08 | G02 | G07 + icono, sin cambiar equipo del jugador |
| Mob/estructura/bioma | G06 escala | G08 o contexto de lugar validado | G03 solo como tension narrativa compatible | Respuesta exacta en overlay y G10 |

No repetir necesariamente una toma por cada pista. Para evitar monotonía, seleccionar tramos/fuentes distintos con intensidad apropiada y no saturar el episodio con peligro continuo. Ajustar ventanas a los props reales de la plantilla: no asumir que todos los episodios duran 28.5 s.

### Criterio de expansion

Agregar una nueva escena solamente si falta una funcion narrativa, una familia contextual importante o variedad suficiente tras medir uso. No agregarla porque aparecio un nuevo item en el banco. Las demostraciones exclusivas quedan fuera de esta biblioteca: **no convertir el rodaje en una lista de mecanicas por item, ni siquiera como extras no solicitados**.

El resultado buscado es una biblioteca pequeña de acciones claras, combinable y revisable: diez generales para arrancar, veinte familias para ampliar, cero grabaciones obligatorias por respuesta.
