# Esquema de contenido

Usar este formato como contrato mínimo. Se permiten campos adicionales.

```json
{
  "episode": {
    "target": {
      "id": "red_wool",
      "display_name": "Red Wool",
      "edition": "java",
      "version": "1.21.5",
      "kind": "block",
      "family": "wool",
      "variant": "red",
      "forbidden_terms": ["red", "roja"],
      "forbidden_clue_terms": ["glide", "fly", "wing"]
    },
    "mode": "open_answer",
    "difficulty": "specific",
    "clue_count": 3,
    "clue_count_reason": "Three independent facts identify the exact color variant cumulatively",
    "candidates": ["red_wool", "pink_wool", "blue_wool"],
    "facts": [
      {"id": "f_family", "scope": "family", "type": "material", "value": "Belongs to the wool family", "source_type": "minecraft-data", "source": "minecraft-data 1.21.5", "verified": true, "relation": "family", "semantic_key": "wool-family", "matches_candidates": ["red_wool", "pink_wool", "blue_wool"]},
      {"id": "f_use", "scope": "target", "type": "use", "value": "Can be crafted into a bed", "source_type": "minecraft-data", "source": "minecraft-data 1.21.5", "verified": true, "relation": "use", "semantic_key": "bed-material", "matches_candidates": ["red_wool", "pink_wool"]},
      {"id": "f_recipe_dye", "scope": "variant", "type": "recipe", "value": "Crafted with wool and red dye", "source_type": "minecraft-data", "source": "minecraft-data 1.21.5", "verified": true, "relation": "dye", "semantic_key": "flower-dye", "matches_candidates": ["red_wool", "blue_wool"]}
    ],
    "clues": [
      {
        "order": 1,
        "text": "I belong to a family that softens footsteps.",
        "referent": "target",
        "fact_ids": ["f_family"],
        "matches_candidates": ["red_wool", "pink_wool", "blue_wool"]
      },
      {
        "order": 2,
        "text": "I can become part of a place where players sleep.",
        "referent": "target",
        "fact_ids": ["f_use"],
        "matches_candidates": ["red_wool", "pink_wool"]
      },
      {
        "order": 3,
        "text": "My shade is produced with a flower dye.",
        "referent": "target",
        "fact_ids": ["f_recipe_dye"],
        "matches_candidates": ["red_wool", "blue_wool"]
      }
    ],
    "remaining_after_each_clue": [3, 2, 1],
        "audit": {
      "candidate_universe": ["blue_wool", "pink_wool", "red_wool"],
      "fact_matches": {
        "f_family": ["blue_wool", "pink_wool", "red_wool"],
        "f_use": ["pink_wool", "red_wool"],
        "f_recipe_dye": ["blue_wool", "red_wool"]
      },
      "computed_clue_matches": [
        ["blue_wool", "pink_wool", "red_wool"],
        ["pink_wool", "red_wool"],
        ["red_wool"]
      ],
      "semantic_keys": ["bed-material", "flower-dye", "wool-family"]
    },
    "unique_answer": true,
    "needs_review": false,
    "human_validation": {
      "stable_referent": true,
      "progressive_reduction": true,
      "no_named_comparisons": true,
      "exact_answer_recoverable": true,
      "final_clue_rationale": "Explain why the final clue identifies the exact visible answer."
    },
    "warnings": [],
    "sources": [
      {
        "title": "Red Wool – Minecraft Wiki",
        "url": "https://minecraft.wiki/"
      }
    ],
    "narration": ""
  }
}
```

`facts[].matches_candidates` es la fuente de verdad para las coincidencias. El validador calcula las coincidencias de cada pista como la interseccion de sus hechos; `clues[].matches_candidates` y `audit.computed_clue_matches` deben coincidir con ese resultado.

## Presentación dinámica

Cada objeto de `clues` debe incluir una presentación renderizable. Ejemplo:

```json
"presentation": {
  "role": "property-state",
  "display_text": "DURABILITY GOES DOWN",
  "fragments": ["DURABILITY GOES DOWN"],
  "emphasis_words": ["DURABILITY"],
  "visual": {
    "prefab": "durability-loss",
    "steps": [
      {"type": "durability", "label": "DURABILITY DROPS", "fact_id": "f_durability", "from": 0}
    ]
  }
}
```

Usar los roles, en orden, `property-state`, `action-interaction`, `origin-context`. `clues[].text` es la voz final; no duplicarla en otro campo. `fragments` debe tener uno o dos textos y coincidir uno a uno con `visual.steps`. Cada `fact_id` visual debe pertenecer a la pista y cada `prefab` debe existir en el esquema activo de Remotion.

Cada hecho tambien declara `relation` y `semantic_key`. No reutilizar un `semantic_key` en dos pistas; si se repite una `relation`, justificar por que aporta una propiedad independiente.

Reglas:

- `clue_count` debe ser `3` y `clues` debe contener exactamente tres elementos.
- `target.kind` es el GuessType visible y debe ser la categoría más específica disponible: `block`, `enchantment`, `food`, `item`, `mineral`, `mob`, `plant`, `potion`, `structure`, `tool` o `weapon`. Reservar `item` para objetivos sin una categoría funcional más precisa.
- `facts[].value` debe ser una paráfrasis atómica.
- `scope` debe ser `family`, `target` o `variant`.
- `source_type` debe ser `minecraft-data`, `wiki` o `inference`.
- Una inferencia debe tener `verified: false` hasta comprobarla.
- `matches_candidates` debe incluir el objetivo en todas las pistas.
- `clues[].referent` debe ser `target`: los pronombres y verbos deben describir siempre la entidad que se adivina.
- Cada pista debe incluir `presentation`; usar `scripts/validate_clues.py --require-presentation` para exigir el patrón dinámico.
- `forbidden_terms` debe incluir el modificador de variante, traducciones y alias que regalarían la respuesta.
- `target.aliases` puede incluir nombres alternativos o traducciones del objetivo; `candidate_aliases` puede mapear candidatos rivales a sus nombres visibles para detectar filtraciones.
- `forbidden_clue_terms` debe incluir la habilidad icónica y sus sinónimos. Ninguna pista puede usarlos ni expresar una paráfrasis funcional equivalente.
- `remaining_after_each_clue` debe representar intersecciones acumuladas.
- `unique_answer` solo puede ser `true` si la intersección final contiene exactamente el objetivo.
- `needs_review` debe ser `true` cuando la intersección final no sea única; no debe marcarse junto con `unique_answer: true`.
- Cada `fact_id` de una pista debe existir en `facts`; los hechos deben declarar `scope`, `source_type`, `source` y `verified`.
- `human_validation` debe documentar la lectura ciega: referente estable, reducción progresiva, respuesta exacta recuperable y motivo concluyente de la última pista.
- `human_validation.no_named_comparisons` debe confirmar que ninguna pista nombra candidatos rivales ni usa comparaciones directas.

