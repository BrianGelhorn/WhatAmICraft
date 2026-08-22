#!/usr/bin/env python3
import json
from copy import deepcopy
from pathlib import Path

from thumbnails import FORMATS, category_icon_path, copy_thumbnail_config, type_names, type_thumbnail_path, validate_config

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    copy_bank = json.loads((ROOT / "data/quiz-copy-episodes.json").read_text(encoding="utf-8"))
    copied = copy_thumbnail_config(copy_bank["episodes"][0])
    validate_config(copied)
    assert set(copied["thumbnail"]["platforms"]) == {"vertical"} == set(FORMATS)
    assert copied["thumbnail"]["outputDir"] == "out/thumbnails"
    assert copied["hintCount"] == 3
    assert copied["answerType"] == "Item"
    assert copied["categoryIcon"] == category_icon_path("Item")
    assert copied["categoryIcon"] != copied["thumbnail"]["icon"]
    assert "Item" in type_names()
    assert type_thumbnail_path("Item", "vertical").as_posix().endswith("out/thumbnails/item/default/item.vertical.jpg")
    tool_episode = deepcopy(copy_bank["episodes"][0])
    tool_episode["answer"]["guessType"] = "Tool"
    assert copy_thumbnail_config(tool_episode)["categoryIcon"] == category_icon_path("Tool")
    print("ok: thumbnail config and platform routing")


if __name__ == "__main__":
    main()
