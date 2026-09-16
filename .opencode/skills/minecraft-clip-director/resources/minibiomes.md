# Escenas y minibiomas con propósito

Un minibioma es un entorno compuesto para una toma, no una plataforma decorada. El propósito decide terreno, volumen, luz, vegetación y assets. Esta guía produce un plan Markdown y criterios de prueba; no agrega campos al JSON de familias.

## 1. Promesa visual

Declara antes de diseñar:

- **Uso:** prueba visible, clip sin spoiler o plano ambiental.
- **Propósito:** qué debe entender el espectador.
- **Emoción:** hostil, acogedora, misteriosa, monumental, frágil u otra intención concreta.
- **Acción:** verbo observable del jugador y consecuencia real.
- **Elemento héroe:** un foco principal; el resto lo enmarca.
- **Prohibidos:** elementos fuera de contexto, spoilers, peligros no pedidos y decoración que compita.

No uses `épico`, `orgánico`, `cinemático` o `dopamina` como especificación. Tradúcelos a contraste, escala, revelación, movimiento, sonido y consecuencia visibles.

## 2. Ritmo audiovisual

Diseña por eventos, no por duración universal:

1. **Anticipación:** silueta, acceso o problema visible que crea una pregunta.
2. **Acción:** un gesto legible sin cortar a otro objeto para fingir causalidad.
3. **Consecuencia:** cambio visual o sonoro claro que recompensa la acción.

Usa un cambio dominante por beat. Reserva el mayor contraste para la acción o consecuencia. Más partículas, árboles o colores reducen el foco si todos compiten a la vez.

## 3. Puerta de relevancia

Para cada categoría propuesta, responde al menos una:

- ¿Apoya directamente la acción?
- ¿Es necesaria para que el entorno pertenezca al arquetipo?
- ¿Construye primer plano, profundidad o silueta?
- ¿Guía al actor o la mirada?

Si ninguna aplica, elimina la categoría. Vegetación, agua, ruinas y assets externos empiezan en `ninguno`, no en `por defecto`.

## 4. Cámara y planos

- Fija posición, punto de interés, FOV, orientación y recorrido del actor. Un teleport no es una cámara de Replay Mod.
- En vertical, comprueba 9:16 con overlays reales y tamaño de teléfono.
- Compón primer plano lateral, zona media de acción y fondo reconocible. No tapes manos, objeto, HUD ni consecuencia.
- Mantén un solo foco y evita que una arista del fondo atraviese la silueta del sujeto.
- Construye solo lo visible más el margen de recorrido. Oculta la unión con superflat y otros sets.

## 5. Blockout obligatorio

Implementa y revisa en este orden:

1. Masas grandes y perfil del horizonte con bloques simples.
2. Cámara, punto de interés y recorrido.
3. Volumen funcional: suelo, techo, agua, acceso o arena.
4. Estructuras y assets grandes.
5. Materiales, vegetación, acentos y sonido.

No detalles una silueta fallida. Si el usuario pide `blockout`, detente tras el paso 3 y no añadas decoración.

## 6. Contratos por arquetipo

| Arquetipo | Debe tener | Rechazar |
| --- | --- | --- |
| Cueva | volumen conectado, techo variable, entrada ocluida, recorrido de dos bloques de altura, paredes y planta irregulares | sala rectangular enterrada, techo plano visible, árboles interiores, fuga vertical de cielo, poza cuadrada decorativa |
| Campo de batalla | corredor seguro, diagonales, daños periféricos, horizonte agresivo y foco central libre | lava/fuego/TNT no pedidos, obstáculos en la acción, ruinas simétricas, decoración pacífica dominante |
| Granja | cultivos legibles, hidratación y soporte válidos, agrupaciones productivas, recorrido claro y color por parcelas | confeti de flores, cultivos inválidos, agua escapada, vegetación que tapa la demostración |
| Santuario o taller | acceso legible, cámara de acción, superficies funcionales y jerarquía arquitectónica | habitación vacía con pedestales, simetría sin foco, luz decorativa que falsea una prueba |
| Ribera | orilla curva, fondo sólido, transición seca/húmeda y agua contenida | piscina rectangular, lámina suspendida, agua invadiendo cámara o acción |
| Plano abierto | horizonte deliberado, agrupaciones laterales y una silueta dominante | plancha vacía, borde visible, objetos equidistantes, cambio de paleta sin cambio de composición |

Estos contratos son mínimos, no plantillas. Una escena híbrida debe cumplir los arquetipos que realmente usa.

## 7. Relieve y materiales

- Huella orientativa para toma cercana: 32x48 o 48x64; amplía solo por recorrido o fondo visible.
- Deja plana únicamente la zona funcional. Fuera, usa masas anchas, asimétricas y desplazadas; evita anillos y terrazas rectangulares repetidas.
- Un desnivel de 3-7 bloques debe leerse desde cámara. En cuevas importa además la variación de techo y anchura.
- Cada columna necesita base, subsuelo y cubierta. Nada de superficies flotantes.
- Paleta corta: dominante, transición y acento. Distribuye por pendiente, humedad, desgaste o función, nunca como ruido independiente por bloque.
- Coloca decoración en la altura final local `h(x,z)+1` y verifica soporte, espacio, gravedad, agua y hojas persistentes.

## 8. Vegetación y luz

- Agrupa vegetación por condiciones; alterna grupos y vacíos. No uses cuadrículas ni distancias uniformes.
- Varía silueta, altura y anchura, no solo especie. Conserva cámara, recorrido y acción despejados.
- Una escena puede tener cero árboles. Cueva, taller o arena hostil deben justificar cada planta.
- Elige hora por legibilidad y emoción. No dependas de shaders para que la composición funcione.
- En pruebas de luz, ningún bloque decorativo puede emitir luz ni abrir una fuga al cielo.
- Registra clima, hora, FOV y recursos gráficos realmente usados.

## 9. Política de assets

Antes de diseñar, consulta `Server/generated/studio/asset_catalog.json` o `Server/catalogs/all_assets.json`. La política de cada escena declara:

- tags o IDs permitidos;
- tags o IDs excluidos;
- tamaño y cantidad máximos;
- función visual de cada slot;
- zonas permitidas y corredor prohibido;
- soporte, orientación y escala;
- comportamiento cuando no hay coincidencias: usar ninguno.

`archive` solo indica procedencia. No selecciones por orden alfabético, primeros elementos del ZIP ni coincidencias parciales de nombres. La implementación debe filtrar antes de colocar y el test debe fallar si el manifest contiene tags, IDs, tamaños o cantidades prohibidas.

## 10. Validación automática mínima

Cada implementación deja pruebas para lo aplicable:

- caja de escritura dentro de límites y sin solapamientos;
- recorrido desde entrada/cámara hasta la acción con suelo y dos bloques libres;
- línea visual cámara-foco despejada;
- zona de acción sin lava, fuego, cactus, caída u otro daño no pedido;
- agua contenida, plantas soportadas y bloques con gravedad estables;
- cuevas con techo sobre la zona de acción y sin fuga vertical de cielo;
- política de assets respetada por `manifest.json`;
- silueta/heightmap distinta de otras escenas, no solo otra paleta;
- setup, reset y setup repetido sin restos ni tareas tardías.

Los checkpoints prueban bloques concretos, no composición. Los tests Python no sustituyen capturas.

## 11. Plan mínimo

```markdown
## Intención y promesa
- Uso:
- Propósito:
- Emoción:
- Acción y consecuencia:
- Elemento héroe:
- Prohibidos:

## Cámara y planos
- Cámara/FOV/punto de interés:
- Primer plano / acción / fondo:
- Recorrido y overlays:

## Blockout y geometría
- Caja de escritura y huella visible:
- Masas, alturas y transición de bordes:
- Zona funcional:

## Ritmo audiovisual
- Anticipación:
- Acción:
- Consecuencia:

## Política de assets
- Permitidos/excluidos:
- Cantidad/tamaño/función/zona:

## Verificación
- Pruebas automáticas:
- Capturas requeridas:
- Condiciones de rechazo:
- Estado visual: visual_pending
```

## 12. Revisión visual

Captura como mínimo:

1. Entrada o anticipación.
2. Cámara principal antes de la acción.
3. Momento de acción y consecuencia.
4. Vista lateral para detectar cajas, bordes, fugas, colisiones o elementos suspendidos.
5. Composición 9:16 con overlays si el destino es móvil.

Rechaza si el arquetipo no se reconoce sin explicación, el foco no se entiende en móvil, la vegetación tapa la acción, el relieve no se lee, dos escenas comparten silueta, o el decorado falsea la mecánica. Entrega observaciones por captura y correcciones concretas, no una puntuación estética inventada.

## Fuentes del proyecto

Al implementar, lee `Server/scene_controller.py`, `Server/landscape.py`, el catálogo y el manifest actuales. No mantengas aquí una lista de presets: cambia con el proyecto. Lee `Server/README.md` para versión, comandos y límites reales. El montaje del datapack no construye nada hasta ejecutar setup.
