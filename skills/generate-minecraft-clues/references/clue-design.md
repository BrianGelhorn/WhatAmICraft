# Diseño y desambiguación de pistas

## Usar exactamente 3 pistas

Generar siempre 3 pistas, incluso para variantes, estados y objetivos difíciles. Si tres hechos confiables no producen una intersección única, reemplazar hechos poco discriminantes o devolver `needs_review: true`; nunca agregar una cuarta pista.

## Construir candidatos

Incluir:

1. Variantes de la misma familia.
2. Objetos con receta, drop, apariencia, generación o uso similar.
3. Todas las opciones dadas por el usuario.
4. El objetivo exacto.

No auditar “lana roja” solamente contra objetos aleatorios. Compararla al menos con las demás lanas coloreadas y con variantes coloreadas que compartan obtención si una pista menciona tintes.

## Progresión

- Pista 1: categoría, dimensión, función amplia o comportamiento compartido.
- Pista 2: obtención, herramienta, receta o generación que reduzca candidatos.
- Pista 3: discriminador fuerte que solo sea definitivo al combinarse con las anteriores.

La última pista debe dejar solo el objetivo al intersectarse con las anteriores. Antes de ella deben quedar al menos dos candidatos y cada pista aislada, incluida la final, debe ser compatible con al menos dos candidatos razonables. La pista final no puede ser una definición independiente.

Buscar una curva de duda controlada: amplia → reductora → decisiva. Cada pista posterior a la primera debe reducir la intersección acumulada; si no lo hace, reemplazarla.

## Patrón dinámico para la plantilla

Seleccionar hechos que además formen una curva visual coherente:

1. `property-state`: una propiedad amplia y visible del objetivo, como durabilidad, stack, estado o familia.
2. `action-interaction`: una acción verificable, como atacar, usar, colocar, consumir, transformar o activar.
3. `origin-context`: una fuente o contexto reconocible, como entidad, receta, estructura, bioma o dimensión.

Cada pista debe tener una o dos unidades visuales. Por cada unidad declarar un fragmento corto y un paso del prefab en el mismo orden; el primer paso empieza en `0` y el segundo, si existe, normalmente en `0.58`. Vincular cada paso con un `fact_id` de la propia pista.

Elegir únicamente prefabs presentes en el contrato activo de la plantilla. Si un hecho no tiene una representación honesta, cambiar el hecho o declarar `needs_template_prefab`; no simularlo con barras, flechas, scans o flashes decorativos. La silueta previa al reveal representa la categoría, nunca la forma exacta del objetivo.

## Sin comparaciones ni candidatos nombrados

Describir únicamente propiedades del objetivo. No mencionar por nombre otro candidato, objeto rival u opción descartada, aunque la comparación sea verdadera. Rechazar estructuras como “igual que X”, “a diferencia de X”, “ambos X e Y”, `like X`, `unlike X`, `similar to X` o `compared with X`.

Transformar la comparación en un predicado autónomo. “A diferencia de un arco, puedo permanecer cargada” sigue siendo demasiado reveladora; buscar en su lugar otro hecho independiente sobre obtención, durabilidad, categoría, condición o interacción secundaria. No usar al rival como pista negativa ni como atajo para explicar la familia.

## Novedad semántica entre pistas

Cada pista debe aportar un hecho independiente, no revelar progresivamente las palabras omitidas de otra. Rechazar las **pistas telescópicas**: dos frases con la misma relación donde la segunda solo sustituye una categoría general por un miembro específico.

Ejemplo inválido:

- Pista 2: “Me pueden obtener de un animal”.
- Pista 3: “Me obtienen de las ovejas”.

Ambas expresan el mismo hecho base: `objetivo → se obtiene de → fuente animal`. La tercera no agrega una propiedad; solo resuelve qué animal ocultaba la segunda. Deben fusionarse en una sola pista o reemplazarse una con un hecho distinto, como uso, receta, comportamiento, generación o interacción.

Antes de aceptar el conjunto, comparar cada par de pistas:

1. Reducir cada frase a `objetivo + relación + valor`.
2. Si dos frases conservan la misma relación y una solo especializa el valor de la otra, tratarlas como un único hecho aunque tengan distintos `fact_ids`.
3. Preguntar qué propiedad nueva y verificable introduce la pista posterior. Si la respuesta es solamente “aclara de qué animal, material, estructura, bioma, herramienta o ingrediente hablaba antes”, rechazarla.
4. Exigir que los `fact_ids` de las pistas sean distintos y representen afirmaciones realmente independientes; cambiar el identificador no convierte una especificación jerárquica en un hecho nuevo.

La reducción de candidatos sigue siendo necesaria, pero no demuestra por sí sola novedad semántica. Una pista puede reducir candidatos y continuar siendo redundante si únicamente completa una pista anterior.

## Dificultad de la pista final

La pista final debe confirmar mediante una propiedad exclusiva pero indirecta. No debe describir la habilidad emblemática que funciona como definición popular del objetivo.

Rechazar, por ejemplo:

- élitros: "me despliego para planear";
- creeper: "me acerco y exploto";
- perla de ender: "teletransporto al lanzador".

Preferir una relación lateral que siga siendo verificable y exclusiva. Para élitros, "las membranas de una criatura que aparece tras varias noches sin dormir restauran mi durabilidad" identifica el objeto sin decir alas, vuelo ni planeo.

Antes de aceptar la secuencia:

1. Registrar en `target.forbidden_clue_terms` la habilidad icónica, sus verbos, sustantivos y sinónimos en el idioma de salida.
2. Rechazar cualquier pista que contenga esos términos o una paráfrasis funcional equivalente.
3. Comprobar que la última pista deja un candidato por obtención, reparación, receta, condición, limitación, interacción secundaria o cifra, no por la función más conocida.
4. Hacer una lectura ciega de la última pista aislada. Si basta por sí sola para responder de inmediato, volverla más indirecta y exigir que se combine con información anterior.

## Coherencia narrativa y adivinabilidad

Mantener el objetivo como sujeto lógico estable. Una pista puede mencionar ingredientes, estructuras, mobs o usos solo para afirmar algo sobre el objetivo: “aparezco en”, “me obtienen de”, “me fabrican con” o “sirvo para”. Rechazar secuencias que cambien el objeto implícito de la adivinanza entre el bloque, su material, su tinte, su fuente o un producto relacionado.

La categoría gramatical anunciada debe coincidir con la respuesta: si se dice “soy un bloque”, todas las pistas deben seguir describiendo ese bloque. No usar “también” para enlazar mecanismos distintos si puede producir una contradicción aparente.

Antes de entregar, hacer una lectura ciega y responder:

1. ¿Qué entidad describe cada “soy”, “me”, “mi” y “puedo”?
2. ¿Cada pista nueva descarta al menos un superviviente real?
3. ¿Cada pista introduce una relación o propiedad independiente, en vez de completar un término genérico anterior?
4. ¿La última pista permite nombrar la respuesta visible exacta, incluida su variante?
5. ¿Puede explicarse la unicidad sin recurrir a información que no aparece en las pistas?

Si alguna respuesta falla, reescribir y volver a validar. Guardar el resultado en `human_validation`, incluyendo una justificación breve de la pista final.

## Evaluar una pista

Para cada candidato responder: “¿Esta afirmación también es verdadera para este candidato en esta versión?”. Guardar todos los compatibles en `matches_candidates`. Calcular la intersección acumulada, no la aparente intención de la frase.

Si la intersección final contiene más de una opción, reconsiderar las pistas generadas. Ordenarlas por cuánto reducen el conjunto, sustituir primero las redundantes o menos discriminantes y recalcular desde el universo original. Repetir hasta que quede exactamente el objetivo. No eliminar candidatos que cumplan literalmente las pistas ni reinterpretar una pista de forma favorable a la respuesta prevista.

Si la intersección queda vacía, alguna pista es falsa para el objetivo o los hechos son incompatibles: descartar el conjunto y volver a las fuentes.

Rechazar:

- pistas posteriores a la primera aplicables por igual a todos los candidatos que aún sobreviven;
- pistas telescópicas donde una frase posterior solo especifica el animal, material, estructura, bioma, herramienta o ingrediente mencionado genéricamente antes;
- sinónimos, traducciones o partes obvias del nombre;
- comparaciones subjetivas de aspecto sin criterio;
- rareza sin cifra o categoría respaldada;
- hechos históricos que ya no aplican a la versión;
- combinaciones cuyo resultado final tenga más de un candidato.
- conjuntos que lleguen a una única respuesta antes de la última pista;
- pistas no finales que, por sí solas, solo puedan describir al objetivo dentro del universo razonable.
- cualquier pista aislada, incluida la final, que deje un solo candidato;
- pistas que nombren otro candidato auditado o se apoyen en una comparación directa.

## Caso guía: lana roja

“Soy un bloque de lana”, “puedo obtenerme de una oveja teñida” y “sirvo para una cama” describen muchas lanas. El conjunto es ambiguo.

Agregar un hecho específico verificable que siga describiendo la lana objetivo, por ejemplo “me tiñen con un colorante fabricado a partir de…”. Evaluarlo contra todas las lanas y terminar con un discriminador que permita nombrar el color exacto. Si otra opción también cumple el hecho final, conservarla y buscar otro discriminador.

## Fuentes

Priorizar `minecraft-data` para IDs, materiales, dureza, drops, herramientas y recetas. Usar Minecraft Wiki para contexto no estructurado. Conservar URL y paráfrasis atómica. Si las fuentes difieren, preferir la fuente/versionado aplicable y marcar la discrepancia; no combinar datos silenciosamente.

