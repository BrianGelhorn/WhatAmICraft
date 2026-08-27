# Prefabs visuales aprobados

Consultar `GET /api/clue-prefabs` antes de seleccionar escenas. Usar únicamente registros con `status: approved`; si una relación solo tiene prefabs `draft`, devolver `needs_template_prefab`.

## `durability-loss`

- Rol: `property-state`.
- Relaciones: `durability`, `wear`, `item_break`.
- Tipos compatibles: `weapon`, `tool`, `item`, `armor`.
- Usar cuando el hecho verificado afirma que el objetivo pierde durabilidad, se desgasta por uso o puede romperse.
- No usar para objetos sin durabilidad ni para representar reparación.
- Generar exactamente un fragmento y un paso:

```json
{
  "role": "property-state",
  "fragments": ["LOSES DURABILITY"],
  "visual": {
    "prefab": "durability-loss",
    "steps": [
      {"type": "durability", "label": "DURABILITY DROPS", "fact_id": "f_durability", "from": 0}
    ]
  }
}
```

La escena usa la silueta genérica de la categoría, comienza con la barra llena, acelera el desgaste y termina con una rotura.

## `stack-limit`

- Rol: `property-state`.
- Relaciones: `stack_limit`, `inventory`.
- Tipos compatibles: `item`, `food`, `weapon`, `tool`, `block`.
- Usar cuando el hecho verificado afirma que el objetivo se apila o tiene una cantidad máxima de inventario.
- El valor es editable por episodio y debe ser un texto corto, por ejemplo `16`, `64` o `1`.
- Generar exactamente un fragmento y un paso:

```json
{
  "role": "property-state",
  "fragments": ["STACK LIMIT: 16"],
  "visual": {
    "prefab": "stack-limit",
    "steps": [
      {"type": "stack-limit", "label": "STACK LIMIT", "value": "16", "fact_id": "f_stack", "from": 0}
    ]
  }
}
```

La escena usa la silueta genérica de la categoría y muestra el valor del episodio. No fijar `16` en la pista si la fuente verificada indica otro límite.

## `enchantment-glint`

- Rol: `property-state`.
- Relaciones: `enchantable`, `enchantment`.
- Tipos compatibles: `weapon`, `tool`, `item`, `armor`.
- Usar cuando el hecho verificado afirma que el objetivo puede recibir encantamientos.
- El ítem principal y el icono de apoyo son configurables desde el episodio.
- Generar exactamente un fragmento y un paso:

```json
{
  "role": "property-state",
  "fragments": ["ENCHANTABLE"],
  "visual": {
    "prefab": "enchantment-glint",
    "supportingAsset": "mc-assets/item-assets/ENCHANTED_BOOK.png",
    "steps": [
      {"type": "enchantment", "label": "ENCHANTABLE", "fact_id": "f_enchantable", "from": 0}
    ]
  }
}
```

La escena comienza con ambos iconos separados, hace impactar el libro contra el objeto, lo oculta y centra el objetivo con un aura violeta. No usar destellos aleatorios ni revelar la forma exacta antes del reveal.

