#!/usr/bin/env python3
from copy import deepcopy

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

print("ok: quiz-copy validation guards")
