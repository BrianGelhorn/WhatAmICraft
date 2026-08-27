---
name: generate-minecraft-clues
description: Create or audit exactly three sourced, progressive, globally non-repeated Minecraft clues and package them as dynamic template-ready scenes with synchronized text and visual prefab beats. Use for WhatAmICraft clue banks, Clues API uploads, episode JSON, Remotion/TTS copy, batch generation, classification, ambiguity checks, visual planning, and used/unused deduplication.
---

# Generate Minecraft clues

Read [references/clue-design.md](references/clue-design.md) before generation/audit. Read [references/content-schema.md](references/content-schema.md) when producing JSON or integrating with Remotion/TTS. For a repository integration, inspect its current prefab catalog and schema before choosing visuals.
Read [references/visual-prefabs.md](references/visual-prefabs.md) before assigning a visual prefab. Treat the Clues API catalog as the runtime source of truth and use only records with `status: approved`.

## Version policy

The existing bank is historical and must remain unchanged, including its `1.21.5` metadata. From now on, every new target, clue upload, episode, and related generation input uses Minecraft Java `26.1`. Never mass-rewrite old episodes to update their version. If the installed data provider lacks `26.1` data, stop with `needs_review` and verify against the exact official source; never silently fall back to an older version.

## Deduplicate first

1. Load canonical targets and clue history from the Clues API/database plus every historical/current episode/video record. Prefer the API/client over direct JSON when available.
2. Normalize IDs and aliases. Exclude every used/reserved target and any semantically repeated clue set; changing template, version, wording, or language does not reset usage.
3. For a batch, reserve/select atomically and require exactly the requested count of distinct unused targets. If history cannot be read reliably, stop rather than risk repetition.
4. Mark usage only through the owning API with episode/video identity when consumed; do not falsify published history.

## Generate

1. Resolve edition, version, canonical/display name, family/variant, and visible `kind`. New targets must use edition `java` and version `26.1`; preserve each historical record's original version. Use the most specific quiz category: crossbow=`weapon`, lectern=`block`, edible target=`food`; `item` is fallback only.
2. Build a serious candidate universe: family variants, mechanically/visually similar targets, and all supplied choices.
3. Extract structured facts with `scripts/extract_minecraft_data.mjs`; use the exact Minecraft Wiki page for missing contextual facts. Paraphrase atomic facts and retain source URL/version. Never present inference as verified.
4. Write exactly three short target-referent clues: broad → reducing → cumulatively decisive. Prefer the visual arc `property-state` → `action-interaction` → `origin-context`; each clue must add an independent fact and reduce survivors after clue 1.
5. Require each isolated clue to fit at least two candidates, at least two survivors before clue 3, and exactly the target after cumulative clue 3. Avoid names/aliases, named comparisons, telescoping facts, and iconic-definition giveaways.
6. Add `presentation` to every clue: one or two short fragments, emphasis words, an implemented and approved visual prefab, and the same number of ordered visual steps. Tie every step to one of the clue's verified `fact_ids`; the first starts at `0`, an optional second defaults to `0.58`.
7. Keep every beat explanatory: show a property, interaction, source, environment, recipe, or transformation stated by the clue. Never use random bars, arrows, scans, incomplete flashes, or the exact answer silhouette before reveal.
8. Generate narration from the exact finalized clue and reveal strings; never use an older bank or alternate wording.
9. Run `scripts/validate_clues.py --require-presentation`; copy computed audit fields instead of inventing them. Then validate the resulting prefab payload with the active template producer/schema.
10. If uniqueness, evidence, or approved prefab coverage fails, replace weak facts and rerun. If still unresolved, return `needs_review: true` and `needs_template_prefab` where applicable; never select a draft prefab, invent a visual, add a fourth clue, or remove legitimate candidates.

## Output

Return the schema-valid `episode`, sources, validator `audit`, dedup evidence, `human_validation`, and render-ready `presentation` for all three clues. For batches, also return requested/generated/rejected counts and unique canonical target IDs.

Commands:

```bash
node scripts/extract_minecraft_data.mjs --version 26.1 --name red_wool --out facts.json
python3 scripts/validate_clues.py episode.json --require-presentation
```

