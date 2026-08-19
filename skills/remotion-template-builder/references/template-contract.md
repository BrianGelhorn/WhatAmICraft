# Template contract

The production contract is `templates/quiz-copy/template.contract.json`.

It must declare:

- composition id, fps, and duration;
- source JSON, schema, producer, and generated config paths;
- editable and generated fields;
- hook, scene, audio, and animation policies;
- the vertical, square, and YouTube thumbnail compositions.

The only supported production path is:

`data/quiz-copy-episodes.json -> schemas/quiz-copy-episode.schema.json -> scripts/produce_quiz_copy.py -> src/generated/quiz-copy-episode.json -> QuizCapasCopy`
