#!/usr/bin/env python3
"""Render a short, non-production visual preview for a registered hook variant."""

import argparse
import json
import subprocess
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "src/generated/quiz-copy-episode.json"
MANIFEST_PATH = ROOT / "data/quiz-copy-hook-experiments.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def preview_config(config: dict, variant: dict) -> dict:
    result = deepcopy(config)
    result["hook"]["title"] = variant["copy"]["title"]
    result["hook"]["handoff"] = variant["copy"]["handoff"]
    result["reveal"]["cta"] = variant["copy"]["revealCta"]
    shift = result["timeline"]["contentStartFrame"] - variant["timing"]["contentStartFrame"]
    result["timeline"].update(variant["timing"])
    result["durationInFrames"] -= shift
    for voice in result["audio"]["voices"]:
        if voice["id"].startswith("clue-") or voice["id"] == "reveal":
            voice["from"] -= shift
    for effect in result["audio"]["effects"]:
        if effect["from"] >= config["timeline"]["contentStartFrame"]:
            effect["from"] -= shift
    result["audio"]["music"]["durationInFrames"] = result["durationInFrames"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Renderiza un preview visual corto del hook")
    parser.add_argument("--variant", default="challenge-v1")
    parser.add_argument("--frames", default="0-180")
    args = parser.parse_args()

    config = read_json(CONFIG_PATH)
    variants = {variant["id"]: variant for variant in read_json(MANIFEST_PATH)["variants"]}
    variant = variants.get(args.variant)
    if variant is None:
        raise SystemExit(f"Variante inexistente: {args.variant}")
    if variant["audio"]["requiresRegeneration"]:
        print("preview: visual-only; requiere voces nuevas antes de producción")

    config = preview_config(config, variant)
    stem = f"{config['id']}-{args.variant}-preview"
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
            f"--frames={args.frames}",
            "--concurrency=1",
        ],
        cwd=ROOT,
        check=True,
        timeout=900,
    )
    print(f"preview: {output.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
