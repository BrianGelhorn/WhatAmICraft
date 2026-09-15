# Minibiomas con profundidad

Un minibioma es un entorno compuesto para una toma, no un cuadrado gigante de cesped. El decorado sostiene la accion; no demuestra por si mismo la propiedad de una familia. Esta guia produce un plan de construccion, no campos nuevos para `scene.example.json`.

## Disenar desde la camara

1. Declara uso: ensayo de objetos visibles, clip de pista sin spoiler o plano ambiental. Define una accion observable y su consecuencia real; si solo se prueba paisaje, dilo. No rellenes con busqueda o celebracion desconectada.
2. Fija encuadre y posicion de camara, punto de interes, FOV y recorrido del actor. Usa el formato real del proyecto; para vertical, comprueba 9:16 con los overlays reales y tamaño de telefono. No confundas el teleport del jugador con una camara de Replay Mod.
3. Traza tres planos: primer plano lateral que enmarca sin tapar, zona media despejada para actuar y fondo con una silueta reconocible. Deja aire alrededor de manos/objetos y espacio para UI. Un solo foco; evita una arista del fondo atravesando la silueta del sujeto.
4. Elige un gesto del terreno (loma diagonal, vaguada curva, talud rocoso), una paleta coherente y un hito secundario. Explica que cambia entre escenas: relieve, perfil del horizonte y distribucion. Cambiar roble por abeto sobre la misma plataforma no cuenta.

## Generador disponible en este proyecto

Al implementar, reutiliza primero `Server/landscape.py` y `Server/scene_controller.py`: ya compilan terreno macizo, montañas, estructuras y vegetacion determinista. La IA elige la composicion, origen y semilla; no inventa coordenadas de cada arbol. Presets actuales: f02 claro de robles con arco, f03 santuario en montaña de abetos, f04 ribera de abedules y cultivos. No intercambies estos IDs con familias historicas de otro contenido.

Lee `Server/README.md` para `build --origin X Z --pitch N --seed N`, version y comandos reales. El manifest generado contiene limites, altura maxima, cantidades y checkpoints; revisalo antes de cargar. Cambiar semilla mantiene la funcion de la prueba. Para otro concepto ajusta la composicion en el generador y sus tests, no copies miles de comandos a mano ni agregues una IA de terreno.

El compilador actual prueba Java 1.21.11 sobre superflat Y72: no afirmes compatibilidad 26.1 ni adaptes otro mundo silenciosamente. Las cajas 192x192 son destructivas dentro de su volumen reservado; respalda y aplica `server.md`. El montaje del pack no construye nada hasta ejecutar setup.

## Relieve antes que detalle

- Empieza por la huella visible: orientativamente 32x48 o 48x64 bloques para una toma cercana; ampliala solo por recorrido o fondo visible. No impongas estas medidas a un plano abierto. Nunca 1024x1024 por defecto para ocultar bordes.
- Conserva plana solo la zona funcional necesaria, por ejemplo un claro de 7x9. Fuera, usa formas anchas y asimetricas, no anillos concentricos ni terrazas rectangulares repetidas. Un desnivel orientativo de 3-7 bloques debe leerse desde la camara, no solo existir fuera de cuadro.
- Disena primero masas grandes, luego transiciones y finalmente microdetalle. Una loma suavizada con huellas irregulares y desplazadas es preferible a ruido independiente por bloque. No agregues un sistema procedural si unas formas deterministas resuelven la toma; si usas azar, fija y registra la semilla.
- Cada columna necesita volumen debajo de su superficie: base solida, subsuelo y cubierta. Nada de una lamina de hierba suspendida ni plantas enterradas. Usa la altura final local `h(x,z)` para colocar decoracion en `h(x,z)+1`, con soporte y espacio validos.
- Adapta al bioma: orillas curvas con taludes y profundidad, piedra expuesta en pendientes, suelo organico bajo copas. No añadas agua o acantilados a todas las escenas. Si una llanura es deliberada, justifica el relieve bajo y obtiene profundidad con agrupaciones, oclusiones laterales y horizonte, no con una plancha vacia.
- Construye lo que ve la camara y un margen para su recorrido. Oculta la union con superflat fuera del encuadre o tras relieve y vegetacion; el borde del set y otras escenas no deben asomar.

## Vegetacion, materiales y luz

- Agrupa por condiciones: vegetacion densa en bordes, claros donde se actua, musgo en zonas humedas y piedras en taludes. Alterna grupos y vacios; evita cuadriculas, distancias uniformes y confeti aleatorio.
- Varia altura, anchura y perfil de copa, no solo madera/hojas: roble irregular y ancho; abeto escalonado y conico; abedul mas esbelto. Usa unas pocas variantes coherentes, sin invadir el corredor del actor ni la linea de vision.
- Paleta corta con funciones: material dominante, transicion y acento. Agrupa mezclas por pendiente/humedad/desgaste, no damero al azar. Flores y rocas pequeñas son acentos, no sustitutos del relieve.
- Elige hora y direccion de luz por legibilidad del objeto contra el fondo. Mediodia es valido para una prueba mecanica, no la unica opcion estetica. Evita sujetos negros a contraluz, sombras que ocultan la accion y faroles decorativos que roban el foco.
- Registra clima, hora, FOV, recursos graficos y shaders realmente usados. No dependas de shaders para que el set funcione en vanilla. No prometas controlar iluminacion cinematografica o camara desde un datapack.
- Sonido y movimiento ambiental deben acompañar, no falsear causalidad ni distraer. En un quiz, revisa spoilers de bioma, color, sonido y silueta tanto como los del objeto.

## Tres composiciones de referencia

Son propuestas de paisaje, no familias F02-F04 ni pruebas mecanicas. Alturas relativas a la superficie del claro (`y0`); comprobarlas en el encuadre elegido. No reutilizar los tres ejemplos literalmente en cada pedido.

| Composicion | Relieve y planos | Vegetacion y camara | Evitar |
| --- | --- | --- | --- |
| Claro de robles en ladera | Huella 40x48, claro 7x9 a y0; loma diagonal posterior a y0+5, depresion lateral a y0-2; roca baja lateral en primer plano | Robles de copas anchas a alturas distintas agrupados en la loma; vista oblicua desde el borde bajo hacia el claro | Arbol central tapando manos, escalones rectangulares y arboles equidistantes |
| Vaguada de coniferas | Huella 32x56; paso curvo a y0, talud izquierdo irregular a y0+6 y hombro derecho a y0+3; fondo desplazado, no simetrico | Abetos conicos de distintos tamaños en grupos, suelo de podzol por manchas; camara mirando a lo largo de la curva con salida visible | Pasillo recto entre paredes iguales, alfombra uniforme de podzol |
| Ribera de abedules | Huella 48x40; zona seca de accion a y0; orilla curva baja hacia agua a y0-1 con fondo solido a y0-3; loma de fondo a y0+4 | Abedules esbeltos agrupados lejos del agua; encuadre diagonal con franja de ribera lateral y fondo abierto | Piscina rectangular, agua invadiendo la prueba o bioma revelando un target |

## Plan minimo antes de construir

Escribe estos datos concretos en la entrega de diseño, no solo adjetivos como "organico" o "cinematico":

- **Intencion y accion:** que se ve, que se prueba, que no se demuestra y riesgos de spoiler.
- **Camara y planos:** posicion, direccion/punto de interes, FOV, encuadre, recorrido y espacio para overlays.
- **Geometria:** dimension y caja de escritura, claro funcional, alturas extrema y base, formas principales y transicion de bordes. Separa caja de construccion, recorrido del actor y zona de control.
- **Materiales y distribucion:** paleta, variantes de arbol, grupos, vacios y regla de colocacion sobre la superficie final.
- **Ejecucion:** version real, semilla si aplica, lotes/chunks, orden de construccion, limpieza acotada y restauracion de la prueba.
- **Diferencia y ensayo:** que distingue esta escena de las otras, vistas a capturar y condiciones de rechazo.

## Puerta de calidad

Primero compara siluetas y masas en bloques simples desde la camara prevista; corrige proporciones antes de decorar. Tras construir, captura inicio, punto clave y final si hay accion, o vista principal y laterales si es solo paisaje. Usa el cliente real; texto JSON y tests Python no sustituyen capturas.

Rechaza o corrige si ocurre cualquiera de estos casos:

- El relieve no se lee, el horizonte es una recta por accidente o se ve una plataforma flotante/cuadrada.
- No se distinguen primer plano, accion y fondo; la vegetacion tapa el foco o el objeto resulta ilegible en movil.
- Las escenas comparten la misma silueta con distinta paleta, o el detalle consiste en arboles clonados y flores uniformes.
- Las plantas desaparecen por soporte invalido, hay hojas no persistentes donde se requieren, agua escapada, colisiones o elementos suspendidos.
- El decorado revela un candidato, distrae de la relacion ilustrada o el montaje sustituye una accion real.
- Setup o reset repetidos dejan restos, comandos fallidos o chunks sin construir. Sigue `server.md` para comprobarlo.

Entrega observaciones por captura y correcciones, no una puntuacion estetica inventada. Sin cliente/capturas: `visual_pending`, con comprobaciones tecnicas y ensayo visual pendiente claramente separados.
