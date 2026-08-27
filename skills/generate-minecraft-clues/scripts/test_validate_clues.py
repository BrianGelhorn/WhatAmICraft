#!/usr/bin/env python3

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def presentation(role: str, display_text: str, prefab: str, step_type: str, fact_id: str) -> dict:
    return {
        "role": role,
        "display_text": display_text,
        "fragments": [display_text],
        "emphasis_words": [],
        "visual": {"prefab": prefab, "steps": [{"type": step_type, "fact_id": fact_id, "from": 0}]},
    }


VALID_EPISODE = {
    "episode": {
        "target": {
            "id": "red_wool",
            "display_name": "Red Wool",
            "edition": "java",
            "version": "1.21.5",
            "kind": "block",
            "family": "wool",
            "variant": "red",
            "aliases": [],
            "forbidden_terms": ["red", "roja"],
            "forbidden_clue_terms": ["explode"],
        },
        "mode": "open_answer",
        "difficulty": "specific",
        "clue_count": 3,
        "clue_count_reason": "Three independent clues",
        "candidates": ["red_wool", "pink_wool", "blue_wool"],
        "facts": [
            {"id": "f1", "scope": "family", "source_type": "minecraft-data", "source": "minecraft-data 1.21.5", "verified": True, "relation": "family", "semantic_key": "wool-family", "matches_candidates": ["red_wool", "pink_wool", "blue_wool"]},
            {"id": "f2", "scope": "target", "source_type": "wiki", "source": "Minecraft Wiki", "verified": True, "relation": "use", "semantic_key": "bed-material", "matches_candidates": ["red_wool", "pink_wool"]},
            {"id": "f3", "scope": "variant", "source_type": "wiki", "source": "Minecraft Wiki", "verified": True, "relation": "dye", "semantic_key": "flower-dye", "matches_candidates": ["red_wool", "blue_wool"]},
        ],
        "clues": [
            {"text": "I belong to a soft building family.", "referent": "target", "fact_ids": ["f1"], "matches_candidates": ["red_wool", "pink_wool", "blue_wool"], "presentation": presentation("property-state", "SOFT BUILDING FAMILY", "material-property", "soft-material", "f1")},
            {"text": "I can become part of a place where players sleep.", "referent": "target", "fact_ids": ["f2"], "matches_candidates": ["red_wool", "pink_wool"], "presentation": presentation("action-interaction", "CRAFTS INTO A BED", "crafting-use", "craft-bed", "f2")},
            {"text": "My shade is produced with a flower dye.", "referent": "target", "fact_ids": ["f3"], "matches_candidates": ["red_wool", "blue_wool"], "presentation": presentation("origin-context", "MADE WITH FLOWER DYE", "recipe-source", "flower-dye", "f3")},
        ],
        "remaining_after_each_clue": [3, 2, 1],
        "unique_answer": True,
        "needs_review": False,
        "human_validation": {
            "stable_referent": True,
            "progressive_reduction": True,
            "no_named_comparisons": True,
            "exact_answer_recoverable": True,
            "final_clue_rationale": "The final variant fact isolates the answer after the family and use clues.",
        },
        "sources": [{"title": "Minecraft Wiki", "url": "https://minecraft.wiki/"}],
    }
}


def run_validator(episode: dict, require_presentation: bool = True) -> tuple[int, dict]:
    validator = Path(__file__).with_name("validate_clues.py")
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        json.dump(episode, handle)
        path = handle.name
    try:
        command = [sys.executable, str(validator), path]
        if require_presentation:
            command.append("--require-presentation")
        result = subprocess.run(command, capture_output=True, text=True)
        return result.returncode, json.loads(result.stdout)
    finally:
        Path(path).unlink(missing_ok=True)


def main() -> int:
    code, result = run_validator(VALID_EPISODE)
    assert code == 0 and result["valid"]

    two_beat = copy.deepcopy(VALID_EPISODE)
    two_beat["episode"]["clues"][0]["presentation"]["fragments"].append("BUILDING BLOCK")
    two_beat["episode"]["clues"][0]["presentation"]["visual"]["steps"].append({"type": "building-family", "fact_id": "f1", "from": 0.58})
    code, result = run_validator(two_beat)
    assert code == 0 and result["valid"]

    legacy = copy.deepcopy(VALID_EPISODE)
    for clue in legacy["episode"]["clues"]:
        del clue["presentation"]
    code, result = run_validator(legacy, require_presentation=False)
    assert code == 0 and result["valid"]
    code, result = run_validator(legacy)
    assert code != 0
    assert any("presentation is required" in error for error in result["errors"])

    invalid = copy.deepcopy(VALID_EPISODE)
    invalid["episode"]["clues"][0]["presentation"]["fragments"].append("SECOND BEAT")
    code, result = run_validator(invalid)
    assert code != 0
    assert any("equal length" in error for error in result["errors"])

    invalid = copy.deepcopy(VALID_EPISODE)
    invalid["episode"]["clues"][1]["presentation"]["role"] = "property-state"
    code, result = run_validator(invalid)
    assert code != 0
    assert any("role must be action-interaction" in error for error in result["errors"])

    invalid = copy.deepcopy(VALID_EPISODE)
    invalid["episode"]["clues"][2]["presentation"]["visual"]["steps"][0]["fact_id"] = "f1"
    code, result = run_validator(invalid)
    assert code != 0
    assert any("fact_id must belong" in error for error in result["errors"])

    invalid = copy.deepcopy(two_beat)
    invalid["episode"]["clues"][0]["presentation"]["visual"]["steps"][0]["from"] = 0.2
    code, result = run_validator(invalid)
    assert code != 0
    assert any("must start at 0" in error for error in result["errors"])

    invalid = copy.deepcopy(VALID_EPISODE)
    invalid["episode"]["target"]["aliases"] = "red wool"
    code, result = run_validator(invalid)
    assert code != 0
    assert any("target.aliases must be a list of strings" in error for error in result["errors"])

    invalid = copy.deepcopy(VALID_EPISODE)
    invalid["episode"]["clue_count"] = 4
    invalid["episode"]["clues"].append(copy.deepcopy(invalid["episode"]["clues"][-1]))
    code, result = run_validator(invalid)
    assert code != 0
    assert any("clue_count must be exactly 3" in error for error in result["errors"])

    invalid = copy.deepcopy(VALID_EPISODE)
    invalid["episode"]["clues"][1]["matches_candidates"] = ["red_wool", "pink_wool", "blue_wool"]
    code, result = run_validator(invalid)
    assert code != 0
    assert any("must equal the fact intersection" in error for error in result["errors"])

    ambiguous = copy.deepcopy(VALID_EPISODE)
    ambiguous["episode"]["candidates"] = ["red_wool", "pink_wool"]
    ambiguous["episode"]["facts"][0]["matches_candidates"] = ["red_wool", "pink_wool"]
    ambiguous["episode"]["facts"][2]["matches_candidates"] = ["red_wool", "pink_wool"]
    ambiguous["episode"]["clues"][0]["matches_candidates"] = ["red_wool", "pink_wool"]
    ambiguous["episode"]["clues"][2]["matches_candidates"] = ["red_wool", "pink_wool"]
    ambiguous["episode"]["remaining_after_each_clue"] = [2, 2, 2]
    ambiguous["episode"]["unique_answer"] = False
    ambiguous["episode"]["needs_review"] = True
    code, result = run_validator(ambiguous)
    assert code != 0
    assert result["unique_answer"] is False
    assert result["remaining_candidates"] == ["pink_wool", "red_wool"]

    golden = copy.deepcopy(VALID_EPISODE)
    golden["episode"]["target"] = {
        "id": "golden_apple",
        "display_name": "Golden Apple",
        "edition": "java",
        "version": "1.21.5",
        "kind": "food",
        "family": "apple",
        "aliases": [],
        "forbidden_terms": ["golden", "apple", "enchanted"],
        "forbidden_clue_terms": ["regeneration"],
    }
    golden["episode"]["candidates"] = ["golden_apple", "enchanted_golden_apple"]
    golden["episode"]["facts"] = [
        {"id": "g1", "scope": "family", "source_type": "minecraft-data", "source": "minecraft-data 1.21.5", "verified": True, "relation": "food", "semantic_key": "stackable-food", "matches_candidates": ["golden_apple", "enchanted_golden_apple"]},
        {"id": "g2", "scope": "target", "source_type": "wiki", "source": "Minecraft Wiki", "verified": True, "relation": "use", "semantic_key": "full-hunger-use", "matches_candidates": ["golden_apple", "enchanted_golden_apple"]},
        {"id": "g3", "scope": "target", "source_type": "wiki", "source": "Minecraft Wiki", "verified": True, "relation": "effect", "semantic_key": "absorption-effect", "matches_candidates": ["golden_apple", "enchanted_golden_apple"]},
    ]
    golden["episode"]["clues"] = [
        {"text": "I am a stackable food.", "referent": "target", "fact_ids": ["g1"], "matches_candidates": ["golden_apple", "enchanted_golden_apple"]},
        {"text": "A player can consume me with a full hunger bar.", "referent": "target", "fact_ids": ["g2"], "matches_candidates": ["golden_apple", "enchanted_golden_apple"]},
        {"text": "Eating me grants temporary extra health.", "referent": "target", "fact_ids": ["g3"], "matches_candidates": ["golden_apple", "enchanted_golden_apple"]},
    ]
    golden["episode"]["remaining_after_each_clue"] = [2, 2, 2]
    golden["episode"]["unique_answer"] = False
    golden["episode"]["needs_review"] = True
    code, result = run_validator(golden)
    assert code != 0
    assert result["remaining_candidates"] == ["enchanted_golden_apple", "golden_apple"]

    print("validate_clues self-test: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

