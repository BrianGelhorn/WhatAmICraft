#!/usr/bin/env python3
"""Generate audio and render one registered hook experiment without changing production config."""

import argparse
import json
import math
import os
import subprocess
from copy import deepcopy
from pathlib import Path

from production_common import load_env_local, speech_with_timestamps
from produce_quiz_copy import normalize_audio, public_path
from render_hook_experiment_preview import preview_config


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "src/generated/quiz-copy-episode.json"
MANIFEST_PATH = ROOT / "data/quiz-copy-hook-experiments.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def generate_experiment_voice(text: str, public_src: str, config: dict) -> tuple[str, int]:
    destination = public_path(public_src)
    if destination.exists():
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(destination)],
            check=True,
            capture_output=True,
            text=True,
        )
        return public_src, math.ceil(float(probe.stdout.strip()) * 30)
    os.environ["ELEVENLABS_VOICE_ID"] = config["voiceGeneration"]["voiceId"]
    alignment = speech_with_timestamps(
        text,
        destination,
        config["voiceGeneration"]["model"],
        1,
    )
    duration_ms = alignment["character_end_times_seconds"][-1] * 1000
    return public_src, math.ceil(duration_ms * 30 / 1000)


def build_config(config: dict, variant: dict) -> dict:
    result = preview_config(config, variant)
    base = config["audio"]["normalization"]
    voice_settings = {
        "targetLufs": base["voiceTargetLufs"],
        "truePeakDb": base["voiceTruePeakDb"],
        "loudnessRange": base["voiceLoudnessRange"],
    }
    experiment_dir = f"audio/quiz-copy/experiments/{config['id']}/{variant['id']}"
    voice_specs = {
        "hook": (variant["audio"]["hookText"], f"{experiment_dir}/hook.mp3", variant["timing"]["hookTitleFromFrame"]),
        "handoff": (variant["audio"]["handoffText"], f"{experiment_dir}/handoff.mp3", variant["timing"]["handoffFromFrame"]),
    }
    generated = {}
    for voice_id, (text, public_src, from_frame) in voice_specs.items():
        raw_src, duration = generate_experiment_voice(text, public_src, config)
        normalized_src = normalize_audio(public_path(raw_src), "audio/quiz-copy/normalized", voice_settings, False)
        generated[voice_id] = {
            "publicSrc": normalized_src,
            "from": from_frame,
            "durationInFrames": duration,
        }
    for voice in result["audio"]["voices"]:
        if voice["id"] in generated:
            voice.update(generated[voice["id"]])
            voice.pop("playbackRate", None)
            voice.pop("fadeOutFrames", None)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Renderiza un experimento completo de hook")
    parser.add_argument("--variant", default="challenge-v1")
    args = parser.parse_args()
    load_env_local()

    config = read_json(CONFIG_PATH)
    variants = {variant["id"]: variant for variant in read_json(MANIFEST_PATH)["variants"]}
    variant = variants.get(args.variant)
    if variant is None:
        raise SystemExit(f"Variante inexistente: {args.variant}")

    config = build_config(config, variant)
    stem = f"{config['id']}-{args.variant}-full"
    props = ROOT / "out/render-jobs" / stem / "video-props.json"
    output = ROOT / "out/previews" / f"{stem}.mp4"
    write_json(props, {"config": config})
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "node",
            "node_modules/@remotion/cli/remotion-cli.js",
            "render",
            "QuizCapasCopy",
            str(output),
            f"--props={props.relative_to(ROOT).as_posix()}",
            f"--frames=0-{config['durationInFrames'] - 1}",
            "--concurrency=1",
        ],
        cwd=ROOT,
        check=True,
        timeout=1800,
    )
    print(f"full experiment: {output.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
