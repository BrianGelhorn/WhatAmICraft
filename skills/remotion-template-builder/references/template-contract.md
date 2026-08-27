# Template contract

The production contract is `templates/quiz-copy/template.contract.json`.

It must declare:

- composition id, fps, and duration;
- source JSON, schema, producer, and generated config paths;
- editable and generated fields;
- hook, scene, audio, and animation policies;
- optional retention policy for mystery templates: selected variant, duration range, question deadline, visual-beat ceiling, CTA timing, and answer/silhouette assets;
- the vertical, square, and YouTube thumbnail compositions.

The only supported production path is:

`data/quiz-copy-episodes.json -> schemas/quiz-copy-episode.schema.json -> scripts/produce_quiz_copy.py -> src/generated/quiz-copy-episode.json -> QuizCapasCopy`

For a retention-first mystery template, add this manifest block:

```json
{
  "retention": {
    "variant": "balanced",
    "durationRangeInFrames": [540, 660],
    "questionMaxStartFrame": 24,
    "maxVisualGapFrames": 75,
    "answerAsset": "assets/crossbow.png",
    "silhouetteAsset": "assets/crossbow-silhouette.png",
    "variants": ["fast", "balanced", "hard_mode", "comment_bait"],
    "cta": {"from": 459, "durationInFrames": 96, "quantified": true}
  }
}
```

`retention` is optional for other formats. When present, the validator checks the selected variant, duration range, first question cue, visual-beat spacing, local asset declarations, and quantified CTA. The producer remains responsible for resolving those asset ids to real files and for proving that the silhouette and answer are the same target.
