#!/usr/bin/env python3
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
from copy import deepcopy
from pathlib import Path

from production_common import load_env_local, production_lock, speech_with_timestamps, write_json
from produce_quiz_copy import normalize_audio, public_path
from template_artifacts import render_props_path


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "data/mystery-v2-episodes.json"
GENERATED_PATH = ROOT / "src/generated/mystery-v2-episode.json"
FPS = 30
VARIANTS = ("fast", "balanced", "comment_bait")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require_text(value, label: str, maximum: int = 160) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{label} debe ser texto no vacío")
    if len(value) > maximum:
        raise RuntimeError(f"{label} supera {maximum} caracteres")


def project_asset(src: str, label: str) -> None:
    require_text(src, label)
    if not public_path(src).is_file():
        raise RuntimeError(f"Falta asset {label}: public/{src}")


def validate_episode(episode: dict) -> None:
    if episode.get("format") != "mystery-v2":
        raise RuntimeError("format debe ser mystery-v2")
    require_text(episode.get("id"), "id")
    answer = episode.get("answer", {})
    for key in ("id", "text", "category"):
        require_text(answer.get(key), f"answer.{key}", 32)
    for key in ("image", "silhouette"):
        require_text(answer.get(key), f"answer.{key}", 200)
    project_asset(answer["image"], "answer.image")
    project_asset(answer["silhouette"], "answer.silhouette")
    if answer["image"] != answer["silhouette"]:
        raise RuntimeError("answer.silhouette debe usar la forma exacta de answer.image")
    project_asset(episode.get("background"), "background")
    hooks = episode.get("hookOptions", {})
    if len(hooks) < 5:
        raise RuntimeError("hookOptions requiere al menos 5 hooks configurables")
    for hook_id, hook in hooks.items():
        require_text(hook.get("displayText"), f"hookOptions.{hook_id}.displayText", 40)
        require_text(hook.get("voiceText"), f"hookOptions.{hook_id}.voiceText", 80)
    hints = episode.get("hints", [])
    if len(hints) != 3:
        raise RuntimeError("La plantilla requiere exactamente 3 pistas")
    for index, hint in enumerate(hints):
        require_text(hint.get("voiceText"), f"hints[{index}].voiceText", 90)
        require_text(hint.get("displayText"), f"hints[{index}].displayText", 54)
        if not 2 <= len(hint.get("fragments", [])) <= 3:
            raise RuntimeError(f"hints[{index}].fragments requiere 2 o 3 fragmentos")
        if hint.get("visualType") not in {"durability", "combat", "mob", "recipe", "generic"}:
            raise RuntimeError(f"hints[{index}].visualType desconocido")
        if hint.get("visualAsset"):
            project_asset(hint["visualAsset"], f"hints[{index}].visualAsset")
    if episode.get("reveal", {}).get("answerText", "").strip().lower() != answer["text"].strip().lower():
        raise RuntimeError("reveal.answerText debe coincidir con answer.text")
    for variant_name in VARIANTS:
        variant = episode.get("variants", {}).get(variant_name)
        if not variant:
            raise RuntimeError(f"Falta variante {variant_name}")
        if variant["hookVariant"] not in hooks:
            raise RuntimeError(f"{variant_name}.hookVariant no existe")
        if variant["ctaVariant"] not in episode.get("ctaOptions", {}):
            raise RuntimeError(f"{variant_name}.ctaVariant no existe")
        timeline = variant["timeline"]
        if timeline["hook"] > 45:
            raise RuntimeError(f"{variant_name}: la primera pista debe comenzar antes del frame 46")
        duration = timeline["hook"] + sum(timeline["hints"]) + timeline["countdown"] + timeline["reveal"] + timeline["cta"] + timeline["loop"]
        seconds = duration / FPS
        limits = {"fast": (14, 16), "balanced": (18, 21), "comment_bait": (17, 20)}[variant_name]
        if not limits[0] <= seconds <= limits[1]:
            raise RuntimeError(f"{variant_name}: duración {seconds:.1f}s fuera de {limits[0]}–{limits[1]}s")


def build_timeline(raw: dict) -> dict:
    cursor = 0
    hook = {"from": cursor, "durationInFrames": raw["hook"]}
    cursor += raw["hook"]
    hints = []
    for duration in raw["hints"]:
        hints.append({"from": cursor, "durationInFrames": duration})
        cursor += duration
    countdown = {"from": cursor, "durationInFrames": raw["countdown"]}
    cursor += raw["countdown"]
    reveal = {"from": cursor, "durationInFrames": raw["reveal"]}
    cursor += raw["reveal"]
    cta = {"from": cursor, "durationInFrames": raw["cta"]}
    cursor += raw["cta"]
    loop = {"from": cursor, "durationInFrames": raw["loop"]}
    cursor += raw["loop"]
    return {"durationInFrames": cursor, "hook": hook, "hints": hints, "countdown": countdown, "reveal": reveal, "cta": cta, "loop": loop}


def selected_config(episode: dict, variant_name: str) -> dict:
    variant = episode["variants"][variant_name]
    hook = episode["hookOptions"][variant["hookVariant"]]
    cta = episode["ctaOptions"][variant["ctaVariant"]]
    return {
        "id": episode["id"],
        "format": "mystery-v2",
        "language": episode["language"],
        "variant": variant_name,
        "hookVariant": variant["hookVariant"],
        "ctaVariant": variant["ctaVariant"],
        "visualIntensity": variant["visualIntensity"],
        "hypothesis": variant["hypothesis"],
        "answer": deepcopy(episode["answer"]),
        "background": episode["background"],
        "hook": {"question": hook["displayText"], "ruleText": episode["ruleText"], "showBrandMark": True},
        "hints": deepcopy(episode["hints"]),
        "countdown": {"displayText": episode["countdown"]["displayText"], "values": episode["countdown"]["values"]},
        "reveal": {"preRevealText": episode["reveal"]["preRevealText"], "answerText": episode["reveal"]["answerText"]},
        "cta": {"text": cta["displayText"], "options": cta["options"]},
        "timeline": build_timeline(variant["timeline"]),
        "theme": deepcopy(episode["theme"]),
        "voice": {"status": "pending", "segments": []},
        "audio": {"status": "pending", "effects": []},
        "debug": deepcopy(episode["debug"]),
    }


def voice_specs(episode: dict, config: dict) -> list[dict]:
    variant = episode["variants"][config["variant"]]
    hook = episode["hookOptions"][variant["hookVariant"]]
    cta = episode["ctaOptions"][variant["ctaVariant"]]
    timeline = config["timeline"]
    return [
        {"id": "hook", "text": hook["voiceText"], "from": 0, "sceneEnd": timeline["hook"]["from"] + timeline["hook"]["durationInFrames"], "emphasisWords": []},
        *[
            {"id": f"hint-{index + 1}", "text": hint["voiceText"], "from": timeline["hints"][index]["from"] + 2, "sceneEnd": timeline["hints"][index]["from"] + timeline["hints"][index]["durationInFrames"], "emphasisWords": hint["emphasisWords"]}
            for index, hint in enumerate(episode["hints"])
        ],
        {"id": "countdown", "text": episode["countdown"]["voiceText"], "from": timeline["countdown"]["from"] + 2, "sceneEnd": timeline["countdown"]["from"] + timeline["countdown"]["durationInFrames"], "emphasisWords": []},
        {"id": "reveal", "text": episode["reveal"]["voiceText"], "from": timeline["reveal"]["from"] + 5, "sceneEnd": timeline["reveal"]["from"] + timeline["reveal"]["durationInFrames"], "emphasisWords": [episode["answer"]["text"]]},
        {"id": "cta", "text": cta["voiceText"], "from": timeline["cta"]["from"] + 4, "sceneEnd": timeline["cta"]["from"] + timeline["cta"]["durationInFrames"], "emphasisWords": cta["options"]},
    ]


def audio_signature(episode: dict, config: dict, spec: dict) -> str:
    payload = {"text": spec["text"], "voice": episode["voiceGeneration"], "variant": config["variant"], "version": 1}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def word_timings(alignment: dict, absolute_from: int) -> list[dict]:
    characters = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]
    words = []
    for match in re.finditer(r"\S+", "".join(characters)):
        start, end = match.span()
        words.append({
            "word": "".join(characters[start:end]),
            "startFrame": absolute_from + math.floor(starts[start] * FPS),
            "endFrame": absolute_from + math.ceil(ends[end - 1] * FPS),
        })
    return words


def generate_voice(episode: dict, config: dict, spec: dict, force: bool) -> dict:
    base = f"audio/mystery-v2/{episode['id']}/{config['variant']}"
    raw_src = f"{base}/{spec['id']}.mp3"
    manifest_path = public_path(f"{base}/{spec['id']}.json")
    raw_path = public_path(raw_src)
    signature = audio_signature(episode, config, spec)
    cached = read_json(manifest_path) if manifest_path.exists() else None
    if not force and cached and cached.get("signature") == signature and raw_path.is_file():
        alignment = cached["alignment"]
    else:
        os.environ["ELEVENLABS_VOICE_ID"] = episode["voiceGeneration"]["voiceId"]
        alignment = speech_with_timestamps(
            spec["text"],
            raw_path,
            episode["voiceGeneration"]["model"],
            episode["voiceGeneration"].get("speed", 1),
        )
        write_json(manifest_path, {"signature": signature, "alignment": alignment})
    normalization = episode["audio"]["normalization"]
    normalized = normalize_audio(raw_path, "audio/mystery-v2/normalized", {
        "targetLufs": normalization["voiceTargetLufs"],
        "truePeakDb": normalization["voiceTruePeakDb"],
        "loudnessRange": normalization["voiceLoudnessRange"],
    }, False)
    duration = math.ceil(alignment["character_end_times_seconds"][-1] * FPS)
    end = spec["from"] + duration
    if end > spec["sceneEnd"]:
        available = (spec["sceneEnd"] - spec["from"]) / FPS
        actual = duration / FPS
        raise RuntimeError(f"Voz {spec['id']} dura {actual:.2f}s y su escena permite {available:.2f}s; acorta el copy")
    return {
        "id": spec["id"], "text": spec["text"], "audioSrc": normalized,
        "start": spec["from"], "end": end, "emphasisWords": spec["emphasisWords"],
        "words": word_timings(alignment, spec["from"]),
    }


def complete_audio(episode: dict, config: dict, force: bool) -> None:
    segments = [generate_voice(episode, config, spec, force) for spec in voice_specs(episode, config)]
    for left, right in zip(segments, segments[1:]):
        if left["end"] > right["start"]:
            raise RuntimeError(f"Voces solapadas: {left['id']} termina en {left['end']} y {right['id']} empieza en {right['start']}")
    music = deepcopy(episode["audio"]["music"])
    project_asset(music["publicSrc"], "audio.music.publicSrc")
    music.update({"from": 0, "durationInFrames": config["timeline"]["durationInFrames"]})
    impact = episode["audio"]["impact"]
    tick = episode["audio"]["tick"]
    reveal = episode["audio"]["reveal"]
    for name, effect in (("impact", impact), ("tick", tick), ("reveal", reveal)):
        project_asset(effect["publicSrc"], f"audio.{name}.publicSrc")
    countdown = config["timeline"]["countdown"]
    step = countdown["durationInFrames"] // len(config["countdown"]["values"])
    effects = [{"id": "impact", **impact, "from": 0}]
    effects.extend({"id": f"hint-{index + 1}-hit", **tick, "from": scene["from"]} for index, scene in enumerate(config["timeline"]["hints"]))
    effects.extend({"id": f"countdown-{value}", **tick, "from": countdown["from"] + index * step} for index, value in enumerate(config["countdown"]["values"]))
    effects.append({"id": "answer-reveal", **reveal, "from": config["timeline"]["reveal"]["from"] + 8})
    config["voice"] = {"status": "complete", "segments": segments}
    config["audio"] = {"status": "complete", "music": music, "effects": effects}


def render(config: dict) -> Path:
    stem = f"{config['id']}-{config['variant']}"
    output = ROOT / f"out/previews/{stem}.mp4"
    props = render_props_path(stem, "video")
    write_json(props, {"config": config})
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "node", "node_modules/@remotion/cli/remotion-cli.js", "render", "MysteryVideo", str(output),
        f"--props={props.relative_to(ROOT).as_posix()}",
        f"--frames=0-{config['timeline']['durationInFrames'] - 1}", "--concurrency=1",
    ], cwd=ROOT, check=True, timeout=1800)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Produce Mystery V2")
    parser.add_argument("--episode", default="mystery-trident-v2")
    parser.add_argument("--variant", choices=VARIANTS, default="balanced")
    parser.add_argument("--all-variants", action="store_true")
    parser.add_argument("--visual-only", action="store_true")
    parser.add_argument("--generate-audio", action="store_true")
    parser.add_argument("--force-audio", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    load_env_local()
    bank = read_json(BANK_PATH)
    if bank.get("format") != "mystery-v2":
        raise RuntimeError("Banco Mystery V2 inválido")
    episode = next((item for item in bank["episodes"] if item["id"] == args.episode), None)
    if episode is None:
        raise RuntimeError(f"Episodio inexistente: {args.episode}")
    validate_episode(episode)
    variants = VARIANTS if args.all_variants else (args.variant,)
    with production_lock():
        for variant in variants:
            config = selected_config(episode, variant)
            if args.generate_audio:
                complete_audio(episode, config, args.force_audio)
            elif args.render and not args.visual_only:
                raise RuntimeError("Usa --generate-audio para un render final o --visual-only para revisar diseño")
            if args.dry_run:
                print(f"ok: {episode['id']} {variant} {config['timeline']['durationInFrames'] / FPS:.1f}s")
                continue
            write_json(GENERATED_PATH, config)
            print(f"config: {GENERATED_PATH.relative_to(ROOT)} ({variant})")
            if args.render:
                output = render(config)
                print(f"render: {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
