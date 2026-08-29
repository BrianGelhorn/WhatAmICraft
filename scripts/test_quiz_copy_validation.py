#!/usr/bin/env python3
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import produce_quiz_copy as quiz
from produce_quiz_copy import BANK_PATH, read_json, validate_episode


def rejected(episode: dict, expected: str) -> None:
    try:
        validate_episode(episode)
    except RuntimeError as error:
        assert expected in str(error), error
    else:
        raise AssertionError(f"Expected validation error containing: {expected}")


episode = read_json(BANK_PATH)["episodes"][0]
validate_episode(episode)

bad_voice = deepcopy(episode)
bad_voice["clues"][0]["voice"]["text"] = "Different clue"
rejected(bad_voice, "coincidir exactamente")

bad_icon = deepcopy(episode)
bad_icon["thumbnail"]["icon"] = bad_icon["hook"]["rouletteIcons"][0]
rejected(bad_icon, "mismo asset")

long_clue = deepcopy(episode)
long_clue["clues"][0]["text"] = long_clue["clues"][0]["voice"]["text"] = "x" * 91
rejected(long_clue, "supera 90")

with TemporaryDirectory() as directory:
    corrupt = Path(directory) / "manifest.json"
    corrupt.write_text("", encoding="utf-8")
    original_path = quiz.manifest_path
    original_generate = quiz.generate_audio
    try:
        quiz.manifest_path = lambda _episode: corrupt
        quiz.generate_audio = lambda _episode: {"signature": "regenerated", "voices": {}}
        assert quiz.prepare_audio(episode, generate=True, seed=False, force=False)["signature"] == "regenerated"
    finally:
        quiz.manifest_path = original_path
        quiz.generate_audio = original_generate

print("ok: quiz-copy validation guards")
