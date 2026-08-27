#!/usr/bin/env python3
"""Small self-check for the optional retention contract."""

from __future__ import annotations

from validate_template_contract import validate_retention


def manifest() -> dict:
    return {
        "compositionId": "Mystery",
        "fps": 30,
        "durationInFrames": 555,
        "automation": {
            "format": "mystery",
            "inputPath": "data.json",
            "schemaPath": "schema.json",
            "producer": "producer.py",
            "generatedConfigPath": "generated.json",
            "editableFields": ["answer"],
            "generatedFields": [],
        },
        "intro": {
            "hookDurationFrames": 21,
            "handoffDurationFrames": 21,
            "contentStartFrame": 42,
            "maxContentStartFrame": 45,
            "visualBeats": [{"from": frame} for frame in (0, 60, 120, 180, 240, 300, 360, 420, 480, 540)],
        },
        "retention": {
            "variant": "balanced",
            "durationRangeInFrames": [540, 660],
            "questionMaxStartFrame": 24,
            "maxVisualGapFrames": 75,
            "answerAsset": "assets/answer.png",
            "silhouetteAsset": "assets/silhouette.png",
            "variants": ["fast", "balanced", "hard_mode", "comment_bait"],
            "cta": {"from": 459, "durationInFrames": 96, "quantified": True},
        },
        "audio": {
            "status": "complete",
            "allowedSources": ["audio/voice.mp3"],
            "cues": [{
                "id": "question",
                "role": "voice",
                "src": "audio/voice.mp3",
                "from": 12,
                "durationInFrames": 12,
                "volume": 1,
                "visualEvent": "question-visible",
                "maxOffsetFrames": 0,
            }],
        },
        "scenes": [{"id": "all", "from": 0, "durationInFrames": 555}],
        "animationPolicy": {"allowCssTransitions": False, "allowRandomness": False},
    }


def main() -> None:
    valid = manifest()
    errors: list[str] = []
    validate_retention(valid["retention"], valid, valid["intro"], valid["audio"], errors)
    assert not errors
    invalid = manifest()
    invalid["retention"]["cta"]["quantified"] = False
    errors = []
    validate_retention(invalid["retention"], invalid, invalid["intro"], invalid["audio"], errors)
    assert any("retention.cta" in error for error in errors)
    print("ok: retention contract self-check")


if __name__ == "__main__":
    main()
