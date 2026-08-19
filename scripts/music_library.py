#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from production_common import write_json
from video_formats import FORMAT_DEFINITIONS

ROOT = Path(__file__).resolve().parents[1]
LIBRARY_PATH = ROOT / "data/music-library.json"
AUDIO_ROOT = ROOT / "public/audio/music-library"
ORIGINAL_ROOT = ROOT / "public/audio/music"
MAX_DURATION_SECONDS = 30 * 60
MAX_FILE_BYTES = 150 * 1024 * 1024
CLIP_DURATION_SECONDS = 2 * 60
MUSIC_EXTENSIONS = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav"}
YTDLP_YOUTUBE_ARGS = [
    "--js-runtimes", "node",
    "--compat-options", "prefer-legacy-http-handler",
    "--extractor-args", "youtube:player_client=android_vr",
]


def load_library() -> dict:
    if not LIBRARY_PATH.exists():
        return {"version": 1, "tracks": [], "originalStarts": {}}
    value = json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
    if not isinstance(value.get("tracks"), list):
        raise RuntimeError("La biblioteca musical esta dañada")
    value.setdefault("originalStarts", {})
    return value


def save_library(value: dict) -> None:
    write_json(LIBRARY_PATH, value)


def validate_youtube_url(value: str) -> str:
    url = value.strip()
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if parsed.scheme != "https" or host not in {"youtube.com", "music.youtube.com", "youtu.be"}:
        raise ValueError("Usa un enlace HTTPS de YouTube")
    return url


def youtube_video_id(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if host == "youtu.be":
        candidate = parsed.path.strip("/").split("/")[0]
    elif parsed.path.startswith(("/shorts/", "/embed/")):
        candidate = parsed.path.split("/")[2]
    else:
        candidate = (parse_qs(parsed.query).get("v") or [""])[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{6,64}", candidate):
        raise ValueError("El enlace no contiene un video de YouTube valido")
    return candidate


def validate_templates(template_ids: list[str]) -> list[str]:
    result = sorted(set(template_ids))
    if not result or not set(result) <= set(FORMAT_DEFINITIONS):
        raise ValueError("Selecciona al menos una plantilla valida")
    return result


def parse_start(value: str) -> float:
    parts = value.strip().split(":")
    if not 1 <= len(parts) <= 3:
        raise ValueError(f"Momento invalido: {value}")
    try:
        numbers = [float(part) for part in parts]
    except ValueError as error:
        raise ValueError(f"Momento invalido: {value}") from error
    if any(not math.isfinite(number) or number < 0 for number in numbers) or any(number >= 60 for number in numbers[1:]):
        raise ValueError(f"Momento invalido: {value}")
    seconds = sum(number * 60 ** index for index, number in enumerate(reversed(numbers)))
    return round(seconds, 2)


def validate_starts(values: list[str]) -> list[float]:
    result = sorted(set(parse_start(value) for value in values if value.strip()))
    if not result or len(result) > 20:
        raise ValueError("Carga entre 1 y 20 momentos")
    return result


def _run(command: list[str], *, timeout: int = 600):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:].strip() or "El proceso de audio fallo")
    return result


def _metadata(url: str) -> dict:
    result = _run([
        "yt-dlp", "--ignore-config", "--no-playlist", "--no-warnings", *YTDLP_YOUTUBE_ARGS,
        "--dump-single-json", "--skip-download", url,
    ], timeout=120)
    return json.loads(result.stdout)


def _ffmpeg_dir() -> Path:
    names = ("ffmpeg.exe", "ffmpeg") if sys.platform == "win32" else ("ffmpeg",)
    for name in names:
        matches = list((ROOT / "node_modules").glob(f"@remotion/compositor-*/{name}"))
        if matches:
            return matches[0].parent
    raise RuntimeError("No se encontro FFmpeg de Remotion")


def original_starts(filename: str) -> list[float]:
    starts = load_library().get("originalStarts", {}).get(filename, [0])
    return starts if isinstance(starts, list) and starts else [0]


def set_original_starts(filename: str, values: list[str]) -> list[float]:
    path = (ORIGINAL_ROOT / filename).resolve()
    if path.parent != ORIGINAL_ROOT.resolve() or not path.is_file() or path.suffix.lower() not in MUSIC_EXTENSIONS:
        raise ValueError("Cancion original invalida")
    starts = validate_starts(values)
    ffprobe = _ffmpeg_dir() / ("ffprobe.exe" if sys.platform == "win32" else "ffprobe")
    duration = float(_run([
        str(ffprobe), "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path),
    ], timeout=30).stdout.strip())
    required = max(float(item.get("durationSeconds", 28)) for item in FORMAT_DEFINITIONS.values())
    if any(start + required > duration for start in starts):
        raise ValueError(f"Deja al menos {required:g} segundos disponibles despues de cada inicio")
    library = load_library()
    library["originalStarts"][filename] = starts
    save_library(library)
    return starts


def _download(url: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    error = None
    for selector in ("bestaudio[ext=m4a]", "139", "bestaudio"):
        try:
            _run([
                "yt-dlp", "--ignore-config", "--no-playlist", "--no-progress",
                *YTDLP_YOUTUBE_ARGS, "--max-filesize", "150M",
                "-f", selector, "-o", str(destination / "download.%(ext)s"), url,
            ])
            break
        except RuntimeError as current_error:
            error = current_error
            for partial in destination.glob("download.*"):
                partial.unlink(missing_ok=True)
            print("Reintentando con una pista alternativa...", flush=True)
    else:
        raise error or RuntimeError("YouTube no devolvio un audio utilizable")
    downloads = list(destination.glob("download.*"))
    if len(downloads) != 1 or downloads[0].stat().st_size > MAX_FILE_BYTES:
        raise RuntimeError("YouTube no devolvio un audio utilizable")
    downloaded = downloads[0]
    source = destination / "source.m4a"
    ffmpeg = _ffmpeg_dir() / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    _run([
        str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y", "-i", str(downloaded), "-vn",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-f", "mp4", str(source),
    ])
    downloaded.unlink()


def _fragment(source: Path, destination: Path, start: float, duration: float) -> None:
    ffmpeg = _ffmpeg_dir() / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    _run([
        str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
        "-ss", str(start), "-i", str(source), "-t", str(duration), "-vn",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-f", "mp4", str(destination),
    ])


def _add_clips(track: dict, folder: Path, starts: list[float], template_ids: list[str], source_duration: float) -> None:
    clips = track.setdefault("clips", [])
    for template_id in template_ids:
        duration = CLIP_DURATION_SECONDS
        invalid = next((start for start in starts if start + duration > source_duration), None)
        if invalid is not None:
            raise ValueError(f"El fragmento {invalid:g}s no tiene {duration:g}s disponibles hasta el final")
    for template_id in template_ids:
        duration = CLIP_DURATION_SECONDS
        for start in starts:
            if any(
                clip.get("templateId") == template_id and abs(float(clip.get("startSeconds", -1)) - start) < 0.01
                for clip in clips
            ):
                continue
            clip_id = hashlib.sha256(f"{template_id}:{start}:{duration}".encode()).hexdigest()[:12]
            filename = f"clip-{clip_id}.m4a"
            print(f"Cortando {template_id} desde {start:g}s...", flush=True)
            _fragment(folder / "source.m4a", folder / filename, start, duration)
            clips.append({
                "id": clip_id,
                "templateId": template_id,
                "startSeconds": start,
                "durationSeconds": duration,
                "publicSrc": f"audio/music-library/{track['id']}/{filename}",
            })
    track["templateIds"] = sorted({clip["templateId"] for clip in clips})


def import_track(url: str, template_ids: list[str], starts: list[str], rights_confirmed: bool) -> dict:
    if not rights_confirmed:
        raise ValueError("Confirma que tenes permiso para reutilizar este audio")
    url = validate_youtube_url(url)
    template_ids, parsed_starts = validate_templates(template_ids), validate_starts(starts)
    video_id = youtube_video_id(url)
    track_id = f"youtube-{video_id}"
    library = load_library()
    existing = next((item for item in library["tracks"] if item.get("id") == track_id), None)
    if existing:
        folder = AUDIO_ROOT / track_id
        if not (folder / "source.m4a").exists():
            raise RuntimeError("La fuente de esta cancion falta; elimina la entrada e importala de nuevo")
        duration = float(existing["durationSeconds"])
        _add_clips(existing, folder, parsed_starts, template_ids, duration)
        existing["updatedAt"] = datetime.now(timezone.utc).isoformat()
        save_library(library)
        print(f"Actualizada: {existing['title']}", flush=True)
        return existing

    AUDIO_ROOT.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{track_id}-", dir=AUDIO_ROOT))
    destination = AUDIO_ROOT / track_id
    try:
        print("Leyendo YouTube...", flush=True)
        metadata = _metadata(url)
        duration = float(metadata.get("duration") or 0)
        if duration <= 0 or duration > MAX_DURATION_SECONDS:
            raise RuntimeError("El audio debe durar entre 1 segundo y 30 minutos")
        print("Descargando audio...", flush=True)
        _download(url, temporary)
        track = {
            "id": track_id,
            "source": "youtube",
            "url": url,
            "videoId": video_id,
            "title": str(metadata.get("title") or video_id)[:160],
            "channel": str(metadata.get("channel") or metadata.get("uploader") or "")[:120],
            "durationSeconds": round(duration, 2),
            "templateIds": [],
            "clips": [],
            "status": "ready",
            "rightsConfirmed": True,
            "importedAt": datetime.now(timezone.utc).isoformat(),
        }
        _add_clips(track, temporary, parsed_starts, template_ids, duration)
        temporary.replace(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    library["tracks"].append(track)
    save_library(library)
    print(f"Lista: {track['title']} ({len(track['clips'])} fragmentos)", flush=True)
    return track


def delete_track(track_id: str) -> None:
    library = load_library()
    track = next((item for item in library["tracks"] if item.get("id") == track_id), None)
    if not track:
        raise ValueError("Cancion inexistente")
    folder = (AUDIO_ROOT / track_id).resolve()
    if folder.parent != AUDIO_ROOT.resolve():
        raise RuntimeError("Ruta musical invalida")
    shutil.rmtree(folder, ignore_errors=True)
    library["tracks"] = [item for item in library["tracks"] if item.get("id") != track_id]
    save_library(library)


def ready_clips_for_template(template_id: str) -> list[dict]:
    clips = []
    for track in load_library()["tracks"]:
        if track.get("status") != "ready":
            continue
        for clip in track.get("clips", []):
            path = ROOT / "public" / clip.get("publicSrc", "")
            if clip.get("templateId") == template_id and path.is_file():
                clips.append({**clip, "trackId": track["id"], "title": track["title"], "url": track["url"]})
    return clips


def main() -> int:
    parser = argparse.ArgumentParser(description="Biblioteca musical por plantilla")
    subparsers = parser.add_subparsers(dest="command", required=True)
    importer = subparsers.add_parser("import")
    importer.add_argument("--url", required=True)
    importer.add_argument("--templates", nargs="+", required=True)
    importer.add_argument("--starts", nargs="+", required=True)
    importer.add_argument("--rights-confirmed", action="store_true")
    args = parser.parse_args()
    if args.command == "import":
        import_track(args.url, args.templates, args.starts, args.rights_confirmed)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
