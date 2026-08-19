# Clue rules

Source of truth: `generate-minecraft-clues` skill.

## Target kind

Use the visible quiz category, not Minecraft's broad internal class. Example: crossbow is `weapon`, not generic `item`.

For block targets, the candidate universe is every block in the selected edition and version from `minecraft-data`. Do not replace that universe with a hand-picked sample. The episode may keep a compact audit hint, but the clue writer and validator must evaluate the clue against all blocks.

Before choosing a new target, read `data/used-targets.json` and reject every ID already listed there. Refresh it with `python3 scripts/target_inventory.py` after changing episode data.

## Difficulty curve

- Use 3 clues for canonical easy targets.
- Use 4 clues for variants or hard targets.
- Order: broad → narrowing → strong → variant discriminator.
- Before the final clue, at least two reasonable candidates should remain.
- After all clues, exactly one answer should remain.
- The last clue should be the target's characteristic behavioral or relational signature, stated naturally. It may be unique against the full universe; avoid unnecessary numeric or implementation detail.

## What to avoid

- Do not name rival candidates.
- Do not compare directly: no "like a bow", "unlike a sword", "similar to X", "compared with X".
- Do not reveal iconic mechanics directly: elytra/glide, ender pearl/teleport, creeper/explode, etc.
- Do not use telescopic clues where one clue says the general source and the next reveals the same source specifically.
- Early clues should not identify the answer by themselves; the final signature may be unique if it does not reveal the name or a trivial synonym.
- Do not use synonyms, translations, or obvious chunks of the item name.

## What to prefer

- Verified facts from `minecraft-data` and Minecraft Wiki.
- Indirect but true discriminators: recipe, repair, condition, generation, limitation, secondary interaction, numeric property.
- Prefer a final signature such as “I can turn a weather event into a redstone signal” or “the strength of my signal depends on how close an impact is to my center.”
- Each clue must add a new semantic fact.
- The target remains the logical subject of every clue.

## Final check

Read the clues blind:

1. Does each clue describe the same target?
2. Does each new clue reduce the candidate set?
3. Is the final clue indirect, not a definition?
4. Can the exact visible answer be explained from the full intersection?

If not, regenerate or mark `needs_review: true`.
