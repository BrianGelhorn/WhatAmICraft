#!/usr/bin/env python3
import argparse
import hashlib
import json
import math
import os
import random
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from production_common import load_env_local, production_lock, speech_with_timestamps, write_json
from thumbnails import copy_thumbnail_config, render_thumbnails as render_official_thumbnails, write_config as write_thumbnail_config
from music_library import CLIP_DURATION_SECONDS, original_starts, ready_clips_for_template
from video_formats import with_target_kind

ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "data/quiz-copy-episodes.json"
GENERATED_PATH = ROOT / "src/generated/quiz-copy-episode.json"
CONTRACT_PATH = ROOT / "templates/quiz-copy/template.contract.json"
FPS = 30
VOICE_AUDIO_VERSION = "current-text-v2"
MUSIC_EXTENSIONS = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def public_path(public_src: str) -> Path:
    root = (ROOT / "public").resolve()
    path = (root / public_src).resolve()
    if path != root and root not in path.parents:
        raise RuntimeError(f"Ruta fuera de public/: {public_src}")
    return path


def project_path(relative_path: str) -> Path:
    path = (ROOT / relative_path).resolve()
    if path != ROOT and ROOT not in path.parents:
        raise RuntimeError(f"Ruta fuera del proyecto: {relative_path}")
    return path


def require_text(value, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"Falta texto valido en {label}")


def require_number(value, label: str, minimum: float = 0) -> None:
    if not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise RuntimeError(f"Valor invalido en {label}")


def normalized_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def generated_voices(episode: dict) -> list[tuple[str, dict, bool]]:
    voices = [
        (f"clue-{index + 1}", clue["voice"], False)
        for index, clue in enumerate(episode["clues"])
    ]
    voices.append(("reveal", episode["reveal"]["voice"], True))
    return voices


def validate_episode(episode: dict) -> None:
    require_text(episode.get("id"), "id")
    for key in ("id", "displayName", "guessType", "edition", "version"):
        require_text(episode.get("answer", {}).get(key), f"answer.{key}")
    if episode["answer"]["edition"] not in {"java", "bedrock"}:
        raise RuntimeError("answer.edition debe ser java o bedrock")
    require_text(episode.get("background"), "background")
    hook = episode.get("hook", {})
    for key in ("eyebrow", "title", "handoff", "categoryPrefix", "selectedIcon"):
        require_text(hook.get(key), f"hook.{key}")
    for key, maximum in {"eyebrow": 24, "title": 24, "handoff": 28, "categoryPrefix": 12}.items():
        if len(hook[key]) > maximum:
            raise RuntimeError(f"hook.{key} supera {maximum} caracteres y puede solaparse")
    if not isinstance(hook.get("rouletteIcons"), list) or len(hook["rouletteIcons"]) != 7:
        raise RuntimeError("hook.rouletteIcons requiere 7 iconos para conservar el audio sincronizado")
    if hook["selectedIcon"] in hook["rouletteIcons"]:
        raise RuntimeError("hook.selectedIcon no puede repetirse dentro de hook.rouletteIcons")
    if len(episode.get("clues", [])) != 3:
        raise RuntimeError("La copia del quiz requiere exactamente 3 pistas")
    require_text(episode.get("hintUi", {}).get("label"), "hintUi.label")
    require_text(episode.get("hintUi", {}).get("cta"), "hintUi.cta")
    if len(episode["hintUi"]["label"]) > 32 or len(episode["hintUi"]["cta"]) > 32:
        raise RuntimeError("hintUi supera el largo seguro de la composicion")
    if "{current}" not in episode["hintUi"]["label"] or "{total}" not in episode["hintUi"]["label"]:
        raise RuntimeError("hintUi.label debe incluir {current} y {total}")
    thumbnail = episode.get("thumbnail", {})
    for key in (
        "eyebrow",
        "headlineTop",
        "headlineBottom",
        "difficulty",
        "subline",
        "mysteryLabel",
        "hintLabel",
        "background",
        "icon",
        "accent",
        "secondaryAccent",
        "outputDir",
    ):
        require_text(thumbnail.get(key), f"thumbnail.{key}")
    for key, maximum in {
        "eyebrow": 24,
        "headlineTop": 12,
        "headlineBottom": 10,
        "difficulty": 8,
        "subline": 24,
        "mysteryLabel": 14,
        "hintLabel": 16,
    }.items():
        if len(thumbnail[key]) > maximum:
            raise RuntimeError(f"thumbnail.{key} supera {maximum} caracteres y puede solaparse")
    if "{number}" not in thumbnail["hintLabel"]:
        raise RuntimeError("thumbnail.hintLabel debe incluir {number}")
    for key in ("accent", "secondaryAccent"):
        try:
            if len(thumbnail[key]) != 7 or not thumbnail[key].startswith("#"):
                raise ValueError
            int(thumbnail[key][1:], 16)
        except ValueError as error:
            raise RuntimeError(f"Color hexadecimal invalido en thumbnail.{key}") from error
    require_number(thumbnail.get("iconScale"), "thumbnail.iconScale", 0.5)
    if thumbnail["iconScale"] > 1.5:
        raise RuntimeError("thumbnail.iconScale no puede superar 1.5")
    if not isinstance(thumbnail.get("iconOffsetY"), (int, float)) or not math.isfinite(thumbnail["iconOffsetY"]) or abs(thumbnail["iconOffsetY"]) > 300:
        raise RuntimeError("thumbnail.iconOffsetY debe estar entre -300 y 300")
    platforms = thumbnail.get("platforms")
    if not isinstance(platforms, dict) or "vertical" not in platforms:
        raise RuntimeError("thumbnail.platforms debe definir vertical")
    if not set(platforms.values()) <= {"silhouette", "pixelated", "roulette"}:
        raise RuntimeError("thumbnail.platforms contiene una variante desconocida")
    project_path(thumbnail["outputDir"])
    icons = {hook["selectedIcon"], thumbnail["icon"], episode.get("reveal", {}).get("icon")}
    if len(icons) != 1:
        raise RuntimeError("hook.selectedIcon, thumbnail.icon y reveal.icon deben ser el mismo asset")
    if normalized_label(Path(hook["selectedIcon"]).stem) != normalized_label(episode["answer"]["id"]):
        raise RuntimeError("answer.id debe coincidir con el nombre del icono seleccionado")
    for index, clue in enumerate(episode["clues"]):
        require_text(clue.get("text"), f"clues[{index}].text")
        require_text(clue.get("voice", {}).get("text"), f"clues[{index}].voice.text")
        require_text(clue.get("voice", {}).get("publicSrc"), f"clues[{index}].voice.publicSrc")
        if clue["text"].strip() != clue["voice"]["text"].strip():
            raise RuntimeError(f"clues[{index}].text debe coincidir exactamente con su voz")
        if len(clue["text"]) > 90:
            raise RuntimeError(f"clues[{index}].text supera 90 caracteres y puede desbordarse")
    reveal = episode.get("reveal", {})
    for key in ("prompt", "answerLabel", "answerText", "cta", "icon"):
        require_text(reveal.get(key), f"reveal.{key}")
    for key, maximum in {"prompt": 20, "answerLabel": 20, "answerText": 32, "cta": 40}.items():
        if len(reveal[key]) > maximum:
            raise RuntimeError(f"reveal.{key} supera {maximum} caracteres y puede solaparse")
    if normalized_label(reveal["answerText"]) != normalized_label(episode["answer"]["displayName"]):
        raise RuntimeError("reveal.answerText debe coincidir con answer.displayName")
    require_text(reveal.get("voice", {}).get("text"), "reveal.voice.text")
    if episode["answer"]["displayName"].lower() not in reveal["voice"]["text"].lower():
        raise RuntimeError("reveal.voice.text debe mencionar answer.displayName")

    timeline = episode.get("timeline", {})
    for key in (
        "contentStartFrame",
        "reelStopFrame",
        "hookTitleFromFrame",
        "handoffFromFrame",
        "categoryFromFrame",
        "hintDurationInFrames",
        "revealDurationInFrames",
        "answerStartFrame",
        "countdownStepInFrames",
    ):
        require_number(timeline.get(key), f"timeline.{key}")
    if timeline["reelStopFrame"] != 34:
        raise RuntimeError("timeline.reelStopFrame debe ser 34 para conservar la pista de ruleta sincronizada")
    if timeline["answerStartFrame"] >= timeline["revealDurationInFrames"]:
        raise RuntimeError("timeline.answerStartFrame debe caer dentro del reveal")
    if reveal["countdownFrom"] * timeline["countdownStepInFrames"] != timeline["answerStartFrame"]:
        raise RuntimeError("countdownFrom × countdownStepInFrames debe coincidir con answerStartFrame")

    voice_generation = episode.get("voiceGeneration", {})
    require_text(voice_generation.get("voiceId"), "voiceGeneration.voiceId")
    require_text(voice_generation.get("model"), "voiceGeneration.model")
    roulette = episode.get("audio", {}).get("roulette", {})
    music = episode.get("audio", {}).get("music", {})
    normalization = episode.get("audio", {}).get("normalization", {})
    for key, minimum in (
        ("voiceTargetLufs", -70),
        ("voiceTruePeakDb", -10),
        ("voiceLoudnessRange", 1),
    ):
        require_number(normalization.get(key), f"audio.normalization.{key}", minimum)
    if normalization["voiceTargetLufs"] > -5 or normalization["voiceTruePeakDb"] > 0:
        raise RuntimeError("Los objetivos de normalizacion de voz no son validos")
    require_text(music.get("folder"), "audio.music.folder")
    for key in (
        "targetLufs",
        "truePeakDb",
        "loudnessRange",
        "volume",
        "duckedVolume",
        "fadeInFrames",
        "fadeOutFrames",
        "duckFadeFrames",
    ):
        minimum = -70 if key == "targetLufs" else -10 if key == "truePeakDb" else 1 if key.endswith("Frames") else 0
        require_number(music.get(key), f"audio.music.{key}", minimum)
    if music["targetLufs"] > -5 or music["truePeakDb"] > 0:
        raise RuntimeError("Los objetivos de normalizacion de audio no pueden ser positivos")
    if music["volume"] > 1 or music["duckedVolume"] > 1:
        raise RuntimeError("Los volumenes de musica deben estar entre 0 y 1")
    if music["duckedVolume"] > music["volume"]:
        raise RuntimeError("audio.music.duckedVolume no puede superar audio.music.volume")
    for key in ("publicSrc", "from", "durationInFrames", "volume"):
        if key == "publicSrc":
            require_text(roulette.get(key), f"audio.roulette.{key}")
        else:
            require_number(roulette.get(key), f"audio.roulette.{key}")
    if roulette["durationInFrames"] != timeline["reelStopFrame"] + 2:
        raise RuntimeError("audio.roulette.durationInFrames debe terminar dos frames despues del reel")
    require_number(roulette.get("targetPeakDb"), "audio.roulette.targetPeakDb", -30)
    if roulette["targetPeakDb"] > 0:
        raise RuntimeError("audio.roulette.targetPeakDb no puede ser positivo")
    for effect_id in ("countdownClick", "revealBell"):
        effect = episode.get("audio", {}).get(effect_id, {})
        require_text(effect.get("publicSrc"), f"audio.{effect_id}.publicSrc")
        require_number(effect.get("durationInFrames"), f"audio.{effect_id}.durationInFrames", 1)
        require_number(effect.get("volume"), f"audio.{effect_id}.volume")
        require_number(effect.get("targetPeakDb"), f"audio.{effect_id}.targetPeakDb", -30)
        if effect["targetPeakDb"] > 0:
            raise RuntimeError(f"audio.{effect_id}.targetPeakDb no puede ser positivo")
    generic_voices = episode.get("audio", {}).get("genericVoices", [])
    if not isinstance(generic_voices, list):
        raise RuntimeError("audio.genericVoices debe ser una lista")
    for index, voice in enumerate(generic_voices):
        for key in ("id", "text", "publicSrc"):
            require_text(voice.get(key), f"audio.genericVoices[{index}].{key}")
        for key in ("from", "durationInFrames", "volume"):
            require_number(voice.get(key), f"audio.genericVoices[{index}].{key}")

    static_assets = [
        episode["background"],
        thumbnail["background"],
        f"images/guess-types/hidden/{episode['answer']['guessType']}.png",
        f"images/guess-types/visible/{episode['answer']['guessType']}.png",
        thumbnail["icon"],
        hook["selectedIcon"],
        *hook["rouletteIcons"],
        reveal["icon"],
        roulette["publicSrc"],
        episode["audio"]["countdownClick"]["publicSrc"],
        episode["audio"]["revealBell"]["publicSrc"],
        *[voice["publicSrc"] for voice in generic_voices],
    ]
    missing = [src for src in static_assets if not public_path(src).exists()]
    if missing:
        raise RuntimeError(f"Faltan assets: {', '.join(missing)}")

    expected_prefix = f"audio/quiz-copy/{episode['id']}/"
    for voice_id, voice, _ in generated_voices(episode):
        if not voice["publicSrc"].startswith(expected_prefix):
            raise RuntimeError(f"{voice_id}.publicSrc debe empezar con {expected_prefix}")


def audio_signature(episode: dict) -> str:
    payload = {
        "audioVersion": VOICE_AUDIO_VERSION,
        "voiceGeneration": episode["voiceGeneration"],
        "voices": [
            {
                "id": voice_id,
                "text": voice["text"],
                "publicSrc": voice["publicSrc"],
                "speed": voice.get("speed", 1),
            }
            for voice_id, voice, _ in generated_voices(episode)
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def manifest_path(episode: dict) -> Path:
    return ROOT / f"public/audio/quiz-copy/{episode['id']}/manifest.json"


def seed_audio(episode: dict) -> dict:
    raise RuntimeError("El audio heredado esta deshabilitado; genera voces desde el texto actual.")


def generate_audio(episode: dict) -> dict:
    os.environ["ELEVENLABS_VOICE_ID"] = episode["voiceGeneration"]["voiceId"]
    model = episode["voiceGeneration"]["model"]
    voices = {}
    for voice_id, voice, is_reveal in generated_voices(episode):
        destination = public_path(voice["publicSrc"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        alignment = speech_with_timestamps(
            voice["text"],
            destination,
            model,
            voice.get("speed", 1),
        )
        metadata = {
            "durationMs": int(alignment["character_end_times_seconds"][-1] * 1000 + 0.999),
        }
        if is_reveal:
            normalized = "".join(alignment["characters"])
            answer_index = normalized.lower().find(episode["answer"]["displayName"].lower())
            if answer_index < 0:
                raise RuntimeError("No se pudo sincronizar el nombre de la respuesta final")
            metadata["answerStartMs"] = round(
                alignment["character_start_times_seconds"][answer_index] * 1000,
            )
        voices[voice_id] = metadata
        print(f"  voz: {voice_id}", flush=True)
    manifest = {"signature": audio_signature(episode), "voices": voices}
    write_json(manifest_path(episode), manifest)
    return manifest


def prepare_audio(episode: dict, generate: bool, seed: bool, force: bool) -> dict:
    path = manifest_path(episode)
    manifest = read_json(path) if path.exists() else None
    files_exist = all(public_path(voice["publicSrc"]).exists() for _, voice, _ in generated_voices(episode))
    if not force and manifest and manifest.get("signature") == audio_signature(episode) and files_exist:
        return manifest
    if generate:
        return generate_audio(episode)
    if seed:
        return seed_audio(episode)
    raise RuntimeError(
        "Las voces especificas estan pendientes o desactualizadas. "
        "Usa --generate-audio para generarlas.",
    )


def frames(milliseconds: float) -> int:
    return math.ceil(milliseconds * FPS / 1000)


def normalize_audio(source: Path, cache_dir: str, settings: dict, dry_run: bool) -> str:
    digest = hashlib.sha256()
    digest.update(json.dumps(
        {"normalizationVersion": 2, **{key: value for key, value in settings.items() if key != "mode"}},
        sort_keys=True,
    ).encode())
    with source.open("rb") as audio_file:
        for chunk in iter(lambda: audio_file.read(1024 * 1024), b""):
            digest.update(chunk)
    public_src = f"{cache_dir}/{digest.hexdigest()[:20]}.m4a"
    destination = public_path(public_src)
    seek = ["-ss", str(settings["trimStartSeconds"])] if settings.get("trimStartSeconds") else []
    limit = ["-t", str(settings["trimDurationSeconds"])] if settings.get("trimDurationSeconds") else []

    if not dry_run and not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f"{destination.stem}.tmp.m4a")
        temporary.unlink(missing_ok=True)
        try:
            analysis = subprocess.run(
                [
                    "node",
                    "node_modules/@remotion/cli/remotion-cli.js",
                    "ffmpeg",
                    "-hide_banner",
                    *seek,
                    "-i",
                    str(source),
                    *limit,
                    "-af",
                    f"loudnorm=I={settings.get('targetLufs', -16)}:LRA={settings.get('loudnessRange', 11)}:TP={settings.get('truePeakDb', -1.5)}:print_format=json",
                    "-f",
                    "null",
                    "-",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            if analysis.returncode != 0:
                raise RuntimeError(f"No se pudo analizar {source.name}:\n{analysis.stderr[-2000:]}")
            measured = json.loads(analysis.stderr[analysis.stderr.rfind("{"):analysis.stderr.rfind("}") + 1])
            if settings.get("mode", "loudness") == "peak":
                input_peak = float(measured["input_tp"])
                if not math.isfinite(input_peak):
                    raise RuntimeError(f"No se pudo medir el pico de {source.name}")
                audio_filter = f"volume={settings['targetPeakDb'] - input_peak:.3f}dB"
            else:
                audio_filter = (
                    f"loudnorm=I={settings['targetLufs']}:LRA={settings['loudnessRange']}:TP={settings['truePeakDb']}"
                    f":measured_I={measured['input_i']}:measured_LRA={measured['input_lra']}"
                    f":measured_TP={measured['input_tp']}:measured_thresh={measured['input_thresh']}"
                    f":offset={measured['target_offset']}:linear=true"
                )
            subprocess.run(
                [
                    "node",
                    "node_modules/@remotion/cli/remotion-cli.js",
                    "ffmpeg",
                    "-y",
                    *seek,
                    "-i",
                    str(source),
                    *limit,
                    "-af",
                    audio_filter,
                    "-vn",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-ar",
                    "48000",
                    "-ac",
                    "2",
                    "-f",
                    "mp4",
                    str(temporary),
                ],
                cwd=ROOT,
                check=True,
            )
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)

    return public_src


def prepare_music(settings: dict, dry_run: bool, template_id: str = "clues") -> dict:
    clips = ready_clips_for_template(template_id)
    folder = Path(settings["folder"]).expanduser()
    if not folder.is_absolute():
        folder = ROOT / folder
    tracks = sorted(
        path for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in MUSIC_EXTENSIONS
    ) if folder.is_dir() else []
    options = [("fragment", clip) for clip in clips] + [
        ("original", {"path": track, "startSeconds": start})
        for track in tracks
        for start in original_starts(track.name)
    ]
    if not options:
        raise RuntimeError(f"No hay musica compatible para la plantilla {template_id}")

    kind, selected = random.SystemRandom().choice(options)
    if kind == "fragment":
        clip = selected
        public_src = normalize_audio(
            public_path(clip["publicSrc"]),
            "audio/quiz-copy/music-cache",
            {
                "targetLufs": settings["targetLufs"],
                "truePeakDb": settings["truePeakDb"],
                "loudnessRange": settings["loudnessRange"],
            },
            dry_run,
        )
        return {
            "publicSrc": public_src,
            "sourceName": f"{clip['title']} @ {clip['startSeconds']:g}s",
            "sourceUrl": clip["url"],
            "fragmentStartSeconds": clip["startSeconds"],
            "from": 0,
            **{key: settings[key] for key in (
                "volume",
                "duckedVolume",
                "fadeInFrames",
                "fadeOutFrames",
                "duckFadeFrames",
            )},
            "trackCount": len(options),
        }

    source = selected["path"]
    start = selected["startSeconds"]
    public_src = normalize_audio(
        source,
        "audio/quiz-copy/music-cache",
        {
            "targetLufs": settings["targetLufs"],
            "truePeakDb": settings["truePeakDb"],
            "loudnessRange": settings["loudnessRange"],
            "trimStartSeconds": start,
            "trimDurationSeconds": CLIP_DURATION_SECONDS,
        },
        dry_run,
    )

    return {
        "publicSrc": public_src,
        "sourceName": f"{source.name} @ {start:g}s",
        "fragmentStartSeconds": start,
        "from": 0,
        **{key: settings[key] for key in (
            "volume",
            "duckedVolume",
            "fadeInFrames",
            "fadeOutFrames",
            "duckFadeFrames",
        )},
        "trackCount": len(options),
    }


def prepare_program_audio(episode: dict, dry_run: bool) -> dict[str, str]:
    normalization = episode["audio"]["normalization"]
    voice_settings = {
        "targetLufs": normalization["voiceTargetLufs"],
        "truePeakDb": normalization["voiceTruePeakDb"],
        "loudnessRange": normalization["voiceLoudnessRange"],
    }
    normalized = {}
    voice_sources = [
        *[voice["publicSrc"] for voice in episode["audio"]["genericVoices"]],
        *[voice["publicSrc"] for _, voice, _ in generated_voices(episode)],
    ]
    for public_src in dict.fromkeys(voice_sources):
        normalized[public_src] = normalize_audio(
            public_path(public_src),
            "audio/quiz-copy/normalized",
            voice_settings,
            dry_run,
        )
    for effect_id in ("roulette", "countdownClick", "revealBell"):
        effect = episode["audio"][effect_id]
        normalized[effect["publicSrc"]] = normalize_audio(
            public_path(effect["publicSrc"]),
            "audio/quiz-copy/normalized",
            {"mode": "peak", "targetPeakDb": effect["targetPeakDb"]},
            dry_run,
        )
    return normalized


def build_config(episode: dict, manifest: dict, music: dict, normalized: dict[str, str]) -> dict:
    timeline = episode["timeline"]
    voices = [deepcopy(voice) for voice in episode["audio"]["genericVoices"]]
    for voice in voices:
        voice["publicSrc"] = normalized[voice["publicSrc"]]
    for index, clue in enumerate(episode["clues"]):
        voice = clue["voice"]
        metadata = manifest["voices"][f"clue-{index + 1}"]
        cue_from = (
            timeline["contentStartFrame"]
            + index * timeline["hintDurationInFrames"]
            + voice.get("fromOffsetFrames", 0)
        )
        raw_duration = frames(metadata["durationMs"])
        cue = {
            "id": f"clue-{index + 1}",
            "publicSrc": normalized[voice["publicSrc"]],
            "from": cue_from,
            "durationInFrames": raw_duration,
            "volume": voice["volume"],
        }
        clue_end = timeline["contentStartFrame"] + (index + 1) * timeline["hintDurationInFrames"]
        playback_rate = max(float(voice.get("speed", 1)), raw_duration / max(1, clue_end - cue_from))
        if playback_rate > 1:
            cue["playbackRate"] = round(playback_rate, 3)
        voices.append(cue)

    reveal_scene_from = (
        timeline["contentStartFrame"]
        + len(episode["clues"]) * timeline["hintDurationInFrames"]
    )
    reveal_voice = episode["reveal"]["voice"]
    reveal_metadata = manifest["voices"]["reveal"]
    reveal_raw_duration = frames(reveal_metadata["durationMs"])
    reveal_playback_rate = max(
        float(reveal_voice.get("speed", 1)),
        reveal_raw_duration / max(1, timeline["revealDurationInFrames"]),
    )
    spoken_answer_frame = math.ceil(frames(reveal_metadata["answerStartMs"]) / reveal_playback_rate)
    reveal_from = reveal_scene_from + max(
        0,
        timeline["answerStartFrame"]
        + reveal_voice.get("syncOffsetFrames", 0)
        - spoken_answer_frame,
    )
    voices.append(
        {
            "id": "reveal",
            "publicSrc": normalized[reveal_voice["publicSrc"]],
            "from": reveal_from,
            "durationInFrames": reveal_raw_duration,
            "volume": reveal_voice["volume"],
            **({"playbackRate": round(reveal_playback_rate, 3)} if reveal_playback_rate > 1 else {}),
        },
    )

    result = deepcopy(episode)
    result["thumbnail"]["platforms"] = {"vertical": result["thumbnail"]["platforms"]["vertical"]}
    result["fps"] = FPS
    result["durationInFrames"] = reveal_scene_from + timeline["revealDurationInFrames"]
    if music["fadeInFrames"] + music["fadeOutFrames"] >= result["durationInFrames"]:
        raise RuntimeError("Los fades de musica ocupan toda la duracion del video")
    music["durationInFrames"] = result["durationInFrames"]
    countdown_click = episode["audio"]["countdownClick"]
    reveal_bell = episode["audio"]["revealBell"]
    effects = [
        {
            "id": "roulette-select-bell",
            **deepcopy(reveal_bell),
            "publicSrc": normalized[reveal_bell["publicSrc"]],
            "from": timeline["reelStopFrame"],
        },
    ]
    effects.extend(
        {
            "id": f"countdown-{episode['reveal']['countdownFrom'] - index}",
            **deepcopy(countdown_click),
            "publicSrc": normalized[countdown_click["publicSrc"]],
            "from": reveal_scene_from + index * timeline["countdownStepInFrames"],
        }
        for index in range(episode["reveal"]["countdownFrom"])
    )
    effects.append(
        {
            "id": "reveal-bell",
            **deepcopy(reveal_bell),
            "publicSrc": normalized[reveal_bell["publicSrc"]],
            "from": reveal_scene_from + timeline["answerStartFrame"],
        },
    )
    result["audio"] = {
        "normalization": deepcopy(episode["audio"]["normalization"]),
        "music": music,
        "roulette": {
            **deepcopy(episode["audio"]["roulette"]),
            "publicSrc": normalized[episode["audio"]["roulette"]["publicSrc"]],
        },
        "effects": effects,
        "voices": voices,
    }
    return result


def update_contract(config: dict) -> None:
    contract = read_json(CONTRACT_PATH)
    timeline = config["timeline"]
    reveal_from = (
        timeline["contentStartFrame"]
        + len(config["clues"]) * timeline["hintDurationInFrames"]
    )
    visual_events = {
        "hook": "question-visible",
        "handoff": "three-hints-card-visible",
        "reveal": "spoken-answer-matches-final-icon-and-text",
    }
    voice_cues = []
    for voice in config["audio"]["voices"]:
        cue = {
            "id": f"voice-{voice['id']}",
            "role": "voice",
            "src": voice["publicSrc"],
            "from": voice["from"],
            "durationInFrames": voice["durationInFrames"],
            "volume": voice["volume"],
            "visualEvent": visual_events.get(voice["id"], f"{voice['id']}-card-visible"),
            "maxOffsetFrames": 0,
        }
        for key in ("playbackRate", "fadeOutFrames"):
            if key in voice:
                cue[key] = voice[key]
        voice_cues.append(cue)

    roulette = config["audio"]["roulette"]
    music = config["audio"]["music"]
    effects = config["audio"]["effects"]
    contract["durationInFrames"] = config["durationInFrames"]
    contract["intro"]["hookDurationFrames"] = timeline["contentStartFrame"]
    contract["intro"]["contentStartFrame"] = timeline["contentStartFrame"]
    contract["intro"]["maxContentStartFrame"] = timeline["contentStartFrame"]
    contract["intro"]["visualBeats"] = [
        {
            "id": "mystery-impact",
            "from": 0,
            "description": f"horizontal reel locks on the black {config['answer']['guessType'].lower()} silhouette and type label by frame {timeline['reelStopFrame']}; answer details stay hidden until reveal",
        },
        {
            "id": "first-hint",
            "from": timeline["contentStartFrame"],
            "description": "first configured clue",
        },
    ]
    contract["audio"]["allowedSources"] = list(
        dict.fromkeys(
            [music["publicSrc"], roulette["publicSrc"], *[effect["publicSrc"] for effect in effects], *[voice["publicSrc"] for voice in config["audio"]["voices"]]],
        ),
    )
    contract["audio"]["normalization"] = deepcopy(config["audio"]["normalization"])
    contract["audio"]["cues"] = [
        {
            "id": "music-background",
            "role": "music",
            "src": music["publicSrc"],
            "from": music["from"],
            "durationInFrames": music["durationInFrames"],
            "volume": music["volume"],
            "visualEvent": "full-video-background-bed",
            "maxOffsetFrames": 0,
        },
        *voice_cues,
        {
            "id": "sfx-roulette-ticks-unified",
            "role": "sfx",
            "src": roulette["publicSrc"],
            "from": roulette["from"],
            "durationInFrames": roulette["durationInFrames"],
            "volume": roulette["volume"],
            "visualEvent": "each-reel-item-crossing-and-final-selection",
            "maxOffsetFrames": 0,
        },
        *[
            {
                "id": f"sfx-{effect['id']}",
                "role": "sfx",
                "src": effect["publicSrc"],
                "from": effect["from"],
                "durationInFrames": effect["durationInFrames"],
                "volume": effect["volume"],
                "visualEvent": (
                    "roulette-selection"
                    if effect["id"] == "roulette-select-bell"
                    else "countdown-number-change"
                    if effect["id"].startswith("countdown-")
                    else "answer-icon-appears"
                ),
                "maxOffsetFrames": 0,
            }
            for effect in effects
        ],
    ]
    contract["scenes"] = [
        {"id": "hook", "from": 0, "durationInFrames": timeline["contentStartFrame"]},
        *[
            {
                "id": f"hint-{index + 1}",
                "from": timeline["contentStartFrame"] + index * timeline["hintDurationInFrames"],
                "durationInFrames": timeline["hintDurationInFrames"],
            }
            for index in range(len(config["clues"]))
        ],
        {
            "id": "reveal",
            "from": reveal_from,
            "durationInFrames": timeline["revealDurationInFrames"],
        },
    ]
    contract["thumbnail"] = {
        "generatedConfigPath": "src/generated/thumbnail-config.json",
        "platforms": {
            "vertical": {"compositionId": "ThumbnailVertical", "width": 1080, "height": 1920, "variant": config["thumbnail"]["platforms"]["vertical"]},
        },
        "outputDir": config["thumbnail"]["outputDir"],
    }
    contract["animationPolicy"]["maxScale"] = 1.12
    write_json(CONTRACT_PATH, contract)


def render(episode: dict) -> None:
    output = ROOT / f"out/episodes/{episode['id']}-{episode['answer']['id']}.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "node",
            "node_modules/@remotion/cli/remotion-cli.js",
            "render",
            "QuizCapasCopy",
            str(output),
            f"--concurrency={os.getenv('REMOTION_CONCURRENCY', '1')}",
        ],
        cwd=ROOT,
        check=True,
        timeout=int(os.getenv("REMOTION_RENDER_TIMEOUT_SECONDS", "1800")),
    )


def render_thumbnails(episode: dict) -> None:
    render_official_thumbnails(
        copy_thumbnail_config(episode),
        f"{episode['id']}-{episode['answer']['id']}",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Produce la plantilla definitiva del quiz de Minecraft")
    parser.add_argument("--episode")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--generate-audio", action="store_true")
    parser.add_argument("--seed-audio", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--force-audio", action="store_true")
    parser.add_argument("--force-render", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--thumbnails", action="store_true")
    parser.add_argument("--thumbnails-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    load_env_local()

    bank = read_json(BANK_PATH)
    if bank.get("format") != "minecraft-quiz-copy":
        raise RuntimeError("Formato JSON invalido")
    episodes = [episode for episode in bank.get("episodes", []) if episode.get("uniqueAnswer", True) and not episode.get("needsReview", False)]
    selected = [episode for episode in episodes if episode.get("id") == args.episode] if args.episode else (episodes if args.all else [random.choice(episodes)])
    if not selected:
        raise RuntimeError(f"Episodio inexistente o pendiente: {args.episode}")
    for episode in selected:
        episode = with_target_kind(episode)
        validate_episode(episode)
        with production_lock():
            if args.thumbnails_only:
                write_thumbnail_config(copy_thumbnail_config(episode))
                if not args.dry_run:
                    render_thumbnails(episode)
                continue
            manifest = prepare_audio(episode, args.generate_audio, args.seed_audio, args.force_audio)
            music = prepare_music(episode["audio"]["music"], args.dry_run, "clues")
            normalized = prepare_program_audio(episode, args.dry_run)
            config = build_config(episode, manifest, music, normalized)
            if args.dry_run:
                print(
                    f"ok: {episode['id']} -> {episode['answer']['displayName']} "
                    f"({config['durationInFrames']} frames, {len(config['audio']['voices'])} voices, "
                    f"{music['trackCount']} music tracks, {len(episode['thumbnail']['platforms'])} thumbnails)",
                )
                continue
            write_json(GENERATED_PATH, config)
            write_thumbnail_config(copy_thumbnail_config(episode))
            update_contract(config)
            print(f"config: {GENERATED_PATH.relative_to(ROOT)}")
            print(f"music: {music['sourceName']} -> {music['publicSrc']}")
            if args.render or args.force_render:
                render(episode)
            if args.thumbnails or args.render or args.force_render:
                render_thumbnails(episode)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
