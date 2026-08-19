# Review checklist

## Silent visual pass

- Frame 0 has a clear visual impact with no flash or clipping.
- Frames 12-30 contain one aggressive hook focus.
- The handoff states the question or promise quickly.
- Content starts by frame 45 at 30 fps.
- The first card or useful shot has no overlap or jump.
- The waiting state is stable.
- The answer is absent two frames before reveal.
- The reveal and explanation fit without being covered.

## Audio pass

- Review audio only after the silent visual pass is stable.
- Reuse an existing source only if its role and character match the scene.
- Remove incorrect cues from JSX and the manifest.
- Generate missing voice, music, or SFX with the project's audio pipeline.
- Every important cue has `visualEvent`, `from`, and `maxOffsetFrames`.
- The first strong sound begins with the first strong visual.
- Voice starts when its text or subject is visible.
- Reveal SFX starts with the reveal state.
- Correct desynchronization by moving or trimming; do not leave it as a warning.
- Check music ducking, fades, duration, and duplicate playback in the final clip.

## Animation pass

- Motion is deterministic and bounded.
- No CSS transitions, CSS animations, timers, randomness, or unexplained state changes.
- No gratuitous bounce, spin, zoom, or effects fighting for attention.
