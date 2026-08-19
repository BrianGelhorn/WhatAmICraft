---
name: remotion-template-builder
description: Create or modify Remotion video templates with a fast stop-scrolling intro, visual-first construction, correct audio reuse or generation, exact frame synchronization, restrained animation, and Studio verification. Use for any template that needs music, voice, SFX, repeated scenes, or format variants.
---

# Remotion template builder

Build predictable templates in two passes: finish the complete video silently first, then add and tune audio. Do not use audio to hide a weak visual timeline.

## Required video structure

Unless the user requests another structure:

1. **Stop-scrolling hook**: one aggressive, clear visual action in 12-30 frames. Use one focus: a stop-scroller, short impact, cut, contrast change, partial reveal, or directed movement.
2. **Fast handoff**: in 6-15 frames, state what the video is about or what the viewer must answer.
3. **Content**: begin by frame 45 at 30 fps. The viewer must see the useful mechanic, first element, or first shot within 1.5 seconds.
4. **Development and close**: keep the pace of the content; do not extend the intro to fill duration.

The intro should feel like an impact, not a logo animation. Avoid long title cards, decorative particles, context-free logos, and several competing effects.

## Workflow

1. Inspect the project before creating components, assets, or sounds. Reuse existing compositions, fonts, helpers, and media where appropriate.
2. Read `references/template-contract.md` and create or update a `template.contract.json` beside the template.
3. Define the visual timeline first: fps, duration, hook, handoff, content start, text, cards, reveal, and close.
4. Build the entire template with **no audio mounted**. The `visual-only` stage must work as a complete video by itself.
5. Run the validator in the visual stage and inspect Remotion Studio. Fix layout, timing, text, and animation before adding audio.
6. Inventory the real files in `public/audio/`. Reuse an existing file only when its role and character match the visual event.
7. Remove incorrect audio from JSX and the manifest, even if the file exists. Do not keep it just because it is available.
8. If a required voice, music bed, or SFX does not exist, generate it with the project's available audio pipeline and save it under `public/audio/` before mounting it.
9. Add audio in a second pass. Synchronize by adjusting `from`, `durationInFrames`, `trimBefore`, `trimAfter`, and volume. A desynchronized cue must be repaired, not merely reported.
10. Run the validator in `audio-complete`, inspect Studio with sound, render stills for key states, and render a short clip to check the mix.

## Local build, then mini PC handoff

- Treat the local machine as the development and render machine. Run Remotion stills, clips, and final exports locally.
- Treat the mini PC as the deployment and automation machine. Do not use it for normal renders or visual QA.
- After the local template passes visual, audio, JSON, and render checks, stop and wait for explicit user authorization before syncing anything to the mini PC.
- Never infer authorization from a finished render, a Studio preview, a dry run, or a previous SSH session. Transfer only after the user clearly approves this specific template.
- On the mini PC, run only safe handoff checks by default: file presence, JSON dry run, service health, and Studio hosting. Do not start a full render there unless the user explicitly asks.
- Keep the local source and mini PC copy aligned before rebuilding the producer, dashboard, bot, or publisher worker.

## Editable JSON for the mini PC

Every generated template must be editable through JSON, not by changing React code.

- Keep the source of truth in `data/<format>-episodes.json`, with a stable top-level `schema_version`, `format`, and `episodes` array.
- Keep the schema in `schemas/<format>-episode.schema.json`.
- Keep a producer at `scripts/produce_<format>.py` that selects an episode, writes `src/generated/<format>-episode.json`, and calls Remotion.
- Treat `src/generated/` as generated output. Never ask the mini PC or dashboard to edit it directly.
- Put every intended edit in the source episode JSON: text, options, answer, explanation, visual asset ids, background, intro timing, audio cues, and any template-specific knobs.
- Keep paths, field names, ids, and `format` stable so the dashboard, priority worker, and mini PC can select and render episodes without template-specific code changes.
- Add an `automation` block to `template.contract.json` with `inputPath`, `schemaPath`, `producer`, `generatedConfigPath`, `format`, and the editable/generated field lists.
- Validate the JSON before rendering. A bad episode should fail before an expensive render, while a missing audio should go through the reuse/generation pass described above.

Use this pipeline: `data JSON -> schema validation -> producer -> generated Remotion config -> composition -> render`. The composition reads only the generated config; it should not contain hardcoded episode content.

## Audio rules

- `audio.status: "pending"` means the visual-only pass: `allowedSources` and `cues` must be empty and no `<Audio>` should be mounted.
- `audio.status: "complete"` means the second pass: every mounted source is listed and every cue has a role, frame, duration, volume, `visualEvent`, and `maxOffsetFrames`.
- Reuse suitable files already in `public/audio/`. If none fits, generate the missing audio with the project pipeline; do not use a random substitute.
- If a file is wrong for the scene, remove it from the composition and manifest. If it is right but late or early, move or trim it until it matches.
- Keep roles separate: `music`, `voice`, `sfx`, and `ambience`. Do not stack multiple music tracks unless requested.
- The first strong sound must accompany the first strong visual. A loud SFX over a still screen is incorrect.
- A voice must start when its text or subject is visible. A reveal sound must start when the reveal state appears.
- Do not overlap voices. Duck music under speech and restore it after the phrase.
- Use `from`/`Sequence`, `durationInFrames`, `trimBefore`, and `trimAfter` explicitly. Use a frame-local volume callback for fades.

## Animation rules

- Use `useCurrentFrame()`, `interpolate()`, `Easing`, and intentional springs.
- Prohibit CSS `transition` and `animation`, `Math.random()`, wall-clock reads, timers, unbounded loops, and render-time state changes.
- Prefer short fade, translate, and restrained scale. Avoid gratuitous bounce, spin, zoom, or simultaneous motion.
- Keep text inside stable boxes. Do not change font size or position frame by frame to force a fit.
- Use blur, glow, and shadows sparingly and with bounded values.

## Verification

Review the silent version first at: frame 0, hook end, handoff, content start, waiting midpoint, two frames before reveal, reveal, and close. Then repeat with audio.

Correct and rerun validation when a cue is wrong, a cue is desynchronized, text is covered, content starts too late, the Studio state differs from the render, or animation has no clear visual purpose. The correct action is to remove, replace, generate, move, trim, or retune the asset until it fits.

Report the composition changed, files reused or generated, synchronization frames, frames reviewed, and validations run.
