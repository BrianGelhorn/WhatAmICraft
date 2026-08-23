#!/usr/bin/env python3
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

from production_common import load_env_local, production_lock, speech_with_timestamps, write_json
from produce_quiz_copy import normalize_audio, public_path
from mystery_prefabs import load_prefab_catalog
from template_artifacts import render_props_path


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "data/mystery-v2-episodes.json"
GENERATED_PATH = ROOT / "src/generated/mystery-v2-episode.json"
FPS = 30
VARIANTS = ("fast", "balanced", "comment_bait")
VISUAL_PREFAB_STEPS = {
    "durability-loss": {"durability"},
    "inventory-properties": {"durability", "stack-limit"},
    "item-entity-interaction": {"melee", "ranged"},
    "entity-equipment": {"holds-answer"},
}
VISUAL_PREFABS_REQUIRING_ASSET = {"item-entity-interaction", "entity-equipment"}


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
    expected_silhouette = f"images/guess-types/hidden/{answer['category'].title()}.png"
    if answer["silhouette"] != expected_silhouette:
        raise RuntimeError(f"answer.silhouette debe usar la silueta genérica de la categoría: {expected_silhouette}")
    if answer["image"] == answer["silhouette"]:
        raise RuntimeError("answer.silhouette no puede revelar la forma exacta de answer.image")
    project_asset(episode.get("background"), "background")
    hooks = episode.get("hookOptions", {})
    if len(hooks) < 5:
        raise RuntimeError("hookOptions requiere al menos 5 hooks configurables")
    for hook_id, hook in hooks.items():
        require_text(hook.get("displayText"), f"hookOptions.{hook_id}.displayText", 40)
        require_text(hook.get("emphasisText"), f"hookOptions.{hook_id}.emphasisText", 28)
        require_text(hook.get("voiceText"), f"hookOptions.{hook_id}.voiceText", 80)
    hints = episode.get("hints", [])
    reviewed_prefabs = {prefab["id"]: prefab for prefab in load_prefab_catalog()["prefabs"]}
    if len(hints) != 3:
        raise RuntimeError("La plantilla requiere exactamente 3 pistas")
    for index, hint in enumerate(hints):
        require_text(hint.get("voiceText"), f"hints[{index}].voiceText", 90)
        require_text(hint.get("displayText"), f"hints[{index}].displayText", 54)
        if not 1 <= len(hint.get("fragments", [])) <= 2:
            raise RuntimeError(f"hints[{index}].fragments requiere 1 o 2 fragmentos")
        visual = hint.get("visual", {})
        prefab = visual.get("prefab")
        if prefab not in VISUAL_PREFAB_STEPS:
            raise RuntimeError(f"hints[{index}].visual.prefab no tiene un prefabricado implementado")
        if prefab in reviewed_prefabs and reviewed_prefabs[prefab]["status"] != "approved":
            raise RuntimeError(f"hints[{index}].visual.prefab todavía no está aprobado")
        steps = visual.get("steps", [])
        if not 1 <= len(steps) <= 2:
            raise RuntimeError(f"hints[{index}].visual.steps requiere 1 o 2 pasos")
        if len(steps) != len(hint["fragments"]):
            raise RuntimeError(f"hints[{index}].visual.steps debe coincidir con la cantidad de fragments")
        starts = [step.get("from") for step in steps]
        if starts[0] != 0 or any(not isinstance(value, (int, float)) or not 0 <= value <= 0.9 for value in starts):
            raise RuntimeError(f"hints[{index}].visual.steps debe empezar en 0 y usar from entre 0 y 0.9")
        if starts != sorted(set(starts)):
            raise RuntimeError(f"hints[{index}].visual.steps debe tener from únicos y ascendentes")
        step_types = [step.get("type") for step in steps]
        if len(step_types) != len(set(step_types)) or any(step_type not in VISUAL_PREFAB_STEPS[prefab] for step_type in step_types):
            raise RuntimeError(f"hints[{index}].visual.steps no es compatible con {prefab}")
        for step_index, step in enumerate(steps):
            if step["type"] in {"durability", "stack-limit"}:
                require_text(step.get("label"), f"hints[{index}].visual.steps[{step_index}].label", 24)
            if step["type"] == "stack-limit":
                require_text(step.get("value"), f"hints[{index}].visual.steps[{step_index}].value", 4)
        supporting_asset = visual.get("supportingAsset")
        if prefab in VISUAL_PREFABS_REQUIRING_ASSET and not supporting_asset:
            raise RuntimeError(f"hints[{index}].visual.supportingAsset es obligatorio para {prefab}")
        if supporting_asset:
            project_asset(supporting_asset, f"hints[{index}].visual.supportingAsset")
        if visual.get("environment", "default") not in {"default", "water"}:
            raise RuntimeError(f"hints[{index}].visual.environment desconocido")
    normalized_hints = [(hint["voiceText"].strip().lower(), hint["displayText"].strip().lower()) for hint in hints]
    for left, right in zip(normalized_hints, normalized_hints[1:]):
        if left[0] == right[0] or left[1] == right[1]:
            raise RuntimeError("No se permiten pistas repetidas en escenas consecutivas")
    countdown = episode.get("countdown", {})
    visible_numbers = countdown.get("values", [])
    number_aliases = {"1": "one", "2": "two", "3": "three", "one": "one", "two": "two", "three": "three"}
    spoken_numbers = [number_aliases[word] for word in re.findall(r"[a-z]+|[123]", countdown.get("voiceText", "").lower()) if word in number_aliases]
    expected_numbers = [{1: "one", 2: "two", 3: "three"}.get(value) for value in visible_numbers]
    if spoken_numbers != expected_numbers:
        raise RuntimeError("countdown.voiceText debe decir exactamente los números visibles y en el mismo orden")
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
        if timeline["hook"] > 35:
            raise RuntimeError(f"{variant_name}: la primera pista debe comenzar antes de 1.20s (frame 36)")
        minimum_cta = {"fast": 60, "balanced": 75, "comment_bait": 90}[variant_name]
        if timeline["cta"] < minimum_cta:
            raise RuntimeError(f"{variant_name}: CTA requiere al menos {minimum_cta / FPS:.1f}s")
        if timeline["reveal"] < 66:
            raise RuntimeError(f"{variant_name}: reveal requiere al menos 2.2s")
        cta = episode["ctaOptions"][variant["ctaVariant"]]
        require_text(cta.get("promptText"), f"{variant_name}: CTA prompt", 56)
        forbidden = ("YES", "NO", "DID YOU GET", "YOUR TURN", "TYPE ONE")
        if any(token in cta["displayText"].upper() for token in forbidden) or cta.get("options") != ["1", "2", "3"]:
            raise RuntimeError(f"{variant_name}: CTA contradictorio; usa una única respuesta numérica 1/2/3")
        if variant_name == "comment_bait" and cta["displayText"] != "COMMENT 1, 2, OR 3":
            raise RuntimeError("comment_bait debe usar exactamente 'COMMENT 1, 2, OR 3'")
        duration = timeline["hook"] + sum(timeline["hints"]) + timeline["countdown"] + timeline["reveal"] + timeline["cta"] + timeline["loop"]
        seconds = duration / FPS
        limits = {"fast": (15.5, 16), "balanced": (16, 17), "comment_bait": (16.5, 17)}[variant_name]
        if not limits[0] <= seconds <= limits[1]:
            raise RuntimeError(f"{variant_name}: duración {seconds:.1f}s fuera de {limits[0]}–{limits[1]}s")
    music = episode.get("audio", {}).get("music", {})
    if not 0 <= music.get("duckedVolume", 1) < music.get("volume", 0):
        raise RuntimeError("audio.music.duckedVolume debe ser menor que volume")


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


def build_retention_beats(timeline: dict) -> list[dict]:
    beats = [("hook-impact", 0), ("hook-rule", 12), ("hook-pulse", 24)]
    for index, scene in enumerate(timeline["hints"]):
        beats.extend([
            (f"hint-{index + 1}-entry", scene["from"]),
            (f"hint-{index + 1}-visual", scene["from"] + 18),
            (f"hint-{index + 1}-keyword", scene["from"] + scene["durationInFrames"] // 2),
            (f"hint-{index + 1}-exit", scene["from"] + scene["durationInFrames"] - 12),
        ])
    countdown = timeline["countdown"]
    beats.extend((f"countdown-{index}", countdown["from"] + index * countdown["durationInFrames"] // 3) for index in range(3))
    reveal = timeline["reveal"]
    beats.extend((name, reveal["from"] + offset) for name, offset in (("reveal-shake", 0), ("reveal-line", 10), ("reveal-light", 24), ("reveal-answer", 38), ("reveal-payoff", 56)))
    cta = timeline["cta"]
    beats.extend((name, cta["from"] + offset) for name, offset in (("cta-question", 0), ("cta-one", 12), ("cta-two", 24), ("cta-three", 36), ("cta-pulse", 54)))
    beats.extend([("loop-start", timeline["loop"]["from"]), ("loop-hook", timeline["durationInFrames"] - 1)])
    return [{"id": name, "frame": frame} for name, frame in sorted(beats, key=lambda item: item[1]) if frame < timeline["durationInFrames"]]


def selected_config(episode: dict, variant_name: str, render_mode: str = "final") -> dict:
    variant = episode["variants"][variant_name]
    hook = episode["hookOptions"][variant["hookVariant"]]
    cta = episode["ctaOptions"][variant["ctaVariant"]]
    timeline = build_timeline(variant["timeline"])
    return {
        "id": episode["id"],
        "format": "mystery-v2",
        "language": episode["language"],
        "variant": variant_name,
        "renderMode": render_mode,
        "hookVariant": variant["hookVariant"],
        "ctaVariant": variant["ctaVariant"],
        "visualIntensity": variant["visualIntensity"],
        "hypothesis": variant["hypothesis"],
        "answer": deepcopy(episode["answer"]),
        "background": episode["background"],
        "hook": {"question": hook["displayText"], "emphasis": hook["emphasisText"], "ruleText": episode["ruleText"], "showBrandMark": False},
        "hints": deepcopy(episode["hints"]),
        "countdown": {"displayText": episode["countdown"]["displayText"], "values": episode["countdown"]["values"]},
        "reveal": {"preRevealText": episode["reveal"]["preRevealText"], "answerText": episode["reveal"]["answerText"]},
        "cta": {"text": cta["displayText"], "prompt": cta["promptText"], "options": cta["options"]},
        "timeline": timeline,
        "retentionBeats": build_retention_beats(timeline),
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
        {"id": "countdown", "text": episode["countdown"]["voiceText"], "from": timeline["countdown"]["from"] + 2, "sceneEnd": timeline["countdown"]["from"] + timeline["countdown"]["durationInFrames"], "emphasisWords": [], "maxTempo": 1.6},
        {
            "id": "reveal", "text": episode["reveal"]["voiceText"],
            "from": timeline["reveal"]["from"] + 5,
            "sceneStart": timeline["reveal"]["from"],
            "sceneEnd": timeline["reveal"]["from"] + timeline["reveal"]["durationInFrames"],
            "alignWord": episode["answer"]["text"],
            "alignFrame": timeline["reveal"]["from"] + 24,
            "emphasisWords": [episode["answer"]["text"]],
        },
        {"id": "cta", "text": cta["voiceText"], "from": timeline["cta"]["from"] + 4, "sceneEnd": timeline["cta"]["from"] + timeline["cta"]["durationInFrames"], "emphasisWords": cta["options"]},
    ]


def audio_signature(episode: dict, spec: dict) -> str:
    payload = {
        "text": spec["text"],
        "voice": episode["voiceGeneration"],
        "version": 4,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def pacing_signature(signature: str, spec: dict) -> str:
    payload = {
        "voiceSignature": signature,
        "sceneFrames": spec["sceneEnd"] - spec["from"],
        "maxTempo": spec.get("maxTempo", 1),
    }
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


def first_normalized_word(value: str) -> str:
    words = re.findall(r"[a-z0-9]+", value.lower())
    return words[0] if words else ""


def paced_audio(source: Path, signature: str, tempo: float) -> Path:
    destination = source.with_name(f"{source.stem}-{signature[:12]}-paced.m4a")
    if destination.is_file():
        return destination
    temporary = destination.with_name(f"{destination.stem}.tmp.m4a")
    temporary.unlink(missing_ok=True)
    try:
        subprocess.run([
            "node", "node_modules/@remotion/cli/remotion-cli.js", "ffmpeg", "-y", "-i", str(source),
            "-af", f"atempo={tempo:.6f}", "-vn", "-c:a", "aac", "-b:a", "192k", "-f", "mp4", str(temporary),
        ], cwd=ROOT, check=True)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def generate_voice(episode: dict, spec: dict, force: bool) -> dict:
    signature = audio_signature(episode, spec)
    raw_src = f"audio/mystery-v2/voice-cache/{signature}.mp3"
    manifest_path = public_path(f"audio/mystery-v2/voice-cache/{signature}.json")
    raw_path = public_path(raw_src)
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
    alignment = deepcopy(alignment)
    duration_seconds = alignment["character_end_times_seconds"][-1]
    available_frames = spec["sceneEnd"] - spec["from"]
    tempo = duration_seconds * FPS / max(1, available_frames - 1)
    audio_source = raw_path
    if tempo > 1:
        if tempo > spec.get("maxTempo", 1):
            raise RuntimeError(f"Voz {spec['id']} dura {duration_seconds:.2f}s y su escena permite {available_frames / FPS:.2f}s; acorta el copy")
        audio_source = paced_audio(raw_path, pacing_signature(signature, spec), tempo)
        alignment["character_start_times_seconds"] = [value / tempo for value in alignment["character_start_times_seconds"]]
        alignment["character_end_times_seconds"] = [value / tempo for value in alignment["character_end_times_seconds"]]
    normalization = episode["audio"]["normalization"]
    normalized = normalize_audio(audio_source, "audio/mystery-v2/normalized", {
        "targetLufs": normalization["voiceTargetLufs"],
        "truePeakDb": normalization["voiceTruePeakDb"],
        "loudnessRange": normalization["voiceLoudnessRange"],
    }, False)
    segment_from = spec["from"]
    if spec.get("alignWord"):
        target = first_normalized_word(spec["alignWord"])
        aligned_word = next((word for word in word_timings(alignment, 0) if first_normalized_word(word["word"]) == target), None)
        if not aligned_word:
            raise RuntimeError(f"Voz {spec['id']} no contiene la palabra de alineación {spec['alignWord']}")
        segment_from = spec["alignFrame"] - aligned_word["startFrame"]
        if segment_from < spec["sceneStart"]:
            raise RuntimeError(f"Voz {spec['id']} necesita comenzar antes de su escena para alinear {spec['alignWord']}")
    duration = math.ceil(alignment["character_end_times_seconds"][-1] * FPS)
    end = segment_from + duration
    if end > spec["sceneEnd"]:
        available = (spec["sceneEnd"] - segment_from) / FPS
        actual = duration / FPS
        raise RuntimeError(f"Voz {spec['id']} dura {actual:.2f}s y su escena permite {available:.2f}s; acorta el copy")
    return {
        "id": spec["id"], "text": spec["text"], "audioSrc": normalized,
        "start": segment_from, "end": end, "emphasisWords": spec["emphasisWords"],
        "words": word_timings(alignment, segment_from),
    }


def complete_audio(episode: dict, config: dict, force: bool) -> None:
    segments = [generate_voice(episode, spec, force) for spec in voice_specs(episode, config)]
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
    countdown_words = next(segment for segment in segments if segment["id"] == "countdown")["words"]
    if len(countdown_words) != len(config["countdown"]["values"]):
        raise RuntimeError("La alineación del countdown no contiene exactamente tres números")
    effects = [{"id": "impact", **impact, "from": 0, "visualEvent": "hook-impact", "maxOffsetFrames": 0}]
    for index, scene in enumerate(config["timeline"]["hints"]):
        effects.append({"id": f"hint-{index + 1}-hit", **tick, "from": scene["from"], "visualEvent": f"hint-{index + 1}-entry", "maxOffsetFrames": 0})
        effects.append({"id": f"hint-{index + 1}-shift", **tick, "from": scene["from"] + scene["durationInFrames"] // 2, "visualEvent": f"hint-{index + 1}-keyword", "maxOffsetFrames": 1})
    effects.extend({"id": f"countdown-{value}", **tick, "from": countdown_words[index]["startFrame"], "visualEvent": f"countdown-{index}", "maxOffsetFrames": 0} for index, value in enumerate(config["countdown"]["values"]))
    reveal_segment = next(segment for segment in segments if segment["id"] == "reveal")
    answer_word = next(word for word in reveal_segment["words"] if first_normalized_word(word["word"]) == first_normalized_word(episode["answer"]["text"]))
    effects.append({"id": "answer-reveal", **reveal, "from": answer_word["startFrame"], "visualEvent": "reveal-light", "maxOffsetFrames": 0})
    config["voice"] = {"status": "complete", "segments": segments}
    config["audio"] = {"status": "complete", "music": music, "effects": effects}


def render_path(config: dict) -> Path:
    suffix = "-preview" if config["renderMode"] == "preview" else ""
    return ROOT / f"out/previews/{config['id']}-{config['variant']}{suffix}.mp4"


def render(config: dict) -> Path:
    output = render_path(config)
    stem = output.stem
    props = render_props_path(stem, "video")
    write_json(props, {"config": config})
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "node", "node_modules/@remotion/cli/remotion-cli.js", "render", "MysteryVideo", str(output),
        f"--props={props.relative_to(ROOT).as_posix()}",
        f"--frames=0-{config['timeline']['durationInFrames'] - 1}", "--concurrency=1",
    ]
    if config["renderMode"] == "preview":
        command.append("--scale=0.5")
    subprocess.run(command, cwd=ROOT, check=True, timeout=1800)
    return output


def contact_sheet(video: Path) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("Contact sheet requiere ffmpeg en PATH")
    output = video.with_name(f"{video.stem}-contact.png")
    subprocess.run([
        ffmpeg, "-y", "-loglevel", "error", "-i", str(video),
        "-vf", "fps=0.5,scale=270:480,tile=3x3:padding=8:margin=8",
        "-frames:v", "1", str(output),
    ], cwd=ROOT, check=True, timeout=180)
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
    parser.add_argument("--preview", action="store_true", help="Render silencioso 540x960 con efectos reducidos")
    parser.add_argument("--contact-sheet", action="store_true", help="Crear mosaico QA desde el render")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    load_env_local()
    bank = read_json(BANK_PATH)
    if bank.get("schema_version") != 2 or bank.get("format") != "mystery-v2":
        raise RuntimeError("Banco Mystery V2 inválido")
    episode = next((item for item in bank["episodes"] if item["id"] == args.episode), None)
    if episode is None:
        raise RuntimeError(f"Episodio inexistente: {args.episode}")
    validate_episode(episode)
    variants = VARIANTS if args.all_variants else (args.variant,)
    render_requested = args.render or args.preview
    with production_lock():
        for variant in variants:
            config = selected_config(episode, variant, "preview" if args.preview else "final")
            if args.generate_audio:
                complete_audio(episode, config, args.force_audio)
            elif render_requested and not (args.visual_only or args.preview):
                raise RuntimeError("Usa --generate-audio para un render final o --visual-only para revisar diseño")
            if args.dry_run:
                print(f"ok: {episode['id']} {variant} {config['timeline']['durationInFrames'] / FPS:.1f}s")
                continue
            write_json(GENERATED_PATH, config)
            print(f"config: {GENERATED_PATH.relative_to(ROOT)} ({variant})")
            output = render_path(config)
            if render_requested:
                output = render(config)
                print(f"render: {output.relative_to(ROOT)}")
            if args.contact_sheet:
                if not output.is_file():
                    raise RuntimeError(f"No existe {output.relative_to(ROOT)}; usa --render o --preview primero")
                sheet = contact_sheet(output)
                print(f"contact-sheet: {sheet.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
