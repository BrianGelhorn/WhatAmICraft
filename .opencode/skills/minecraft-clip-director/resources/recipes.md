# Recetas De Escenas

Este indice evita leer la biblioteca completa. Son puntos de partida, no clips visualmente aprobados. No crear una variante si el archivo existente ya resuelve la necesidad.

| Receta | Base existente | Evento -> consecuencia -> final | Duracion |
|---|---|---|---|
| discovery | G01 | Abrir cofre vacio -> sostener misterio -> cerrar | 180 f |
| decision | G02 | Mirar dos rutas -> amagar una, elegir otra -> detenerse | 180 f |
| danger | G03 / G05 | Suelo cede / proyectil pasa -> apartarse -> mostrar resultado | 150 / 120 f |
| recovery | G04 | Salto corto -> apoyo inferior y segundo salto -> alivio | 150 f |
| scale | G06 | Salir de oclusion -> revelar estructura y jugador -> sostener | 180 f |
| reveal | G07 | Retirar panel -> ver pedestal vacio -> dejar espacio limpio | 180 f |
| search | G08 | Mirar dos sitios -> rodear divisor -> inspeccionar nicho vacio | 180 f |
| presence | G09 | Camara cruza esquina -> descubre mob ya colocado -> sostener | 150 f |
| reaction | G10 | Un salto -> una agachada -> reposo | 120 f |

## Decisiones Por Defecto

- Construccion neutra de piedra/gris, sin props que representen la respuesta.
- Tres partes contiguas: para 180 f usar 0-29, 30-119, 120-179; para 150 f usar 0-29, 30-89, 90-149; para 120 f usar 0-29, 30-59, 60-119.
- Camara fija oblicua o frontal con actor, recorrido y consecuencia en el mismo cuadro. Si no cabe, simplificar set antes de agregar camaras.
- Posiciones con coordenadas absolutas solo si se conoce el set. En un concepto nuevo usar espacio local explicitamente, sin presentarlo como construccion instalada.
- Materiales indicados en `setup`. Actuacion y evento observables en `beats`. Reinicio separado en `reset`.

G05 es una excepcion existente de dos fuentes (30 + 90 f); leer su ficha especifica, no forzar este brief de una sola toma a fingir un paneo imposible. El formato compacto solo admite una toma; para un pedido multiplano adaptar el contrato primero o usar la ficha tecnica de la biblioteca.

## Buenos Y Malos Usos

**Bueno:** G08 en preguntas de herramientas, minerales y pociones. Se busca una respuesta; no se afirma que esos targets aparezcan fisicamente en un estante. Mismo archivo, estantes vacios.

**Malo:** cambiar el item oculto de un cofre por episodio. Ya obliga a nuevas capturas y puede adelantar la respuesta.

**Bueno:** peligro por suelo que cae delante del jugador; independiente del objeto preguntado.

**Malo:** esponja absorbiendo agua renombrada como "transformacion generica". La accion sigue siendo exclusiva.

**Bueno:** G07 deja un pedestal vacio y Remotion agrega un icono independiente.

**Malo:** asegurar que Remotion sustituye automaticamente un objeto que el jugador sostiene en el video.

## Revision Visual Humana

Para cada criterio escribir internamente SI o NO con una razon concreta: reuso sin cambios, evento temprano, consecuencia visible, foco legible, geometria posible, reset claro. Un NO bloquea la entrega como lista para ensayo. No poner puntajes inventados ni convertir el resultado del validador en "aprobado visual".
