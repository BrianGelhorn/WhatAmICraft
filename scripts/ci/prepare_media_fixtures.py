#!/usr/bin/env python3
"""Create disposable media fixtures for CI; never stores media in Git."""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MEDIA_SUFFIXES = {".mp3", ".m4a", ".wav", ".ogg", ".png", ".jpg", ".jpeg", ".webp", ".otf"}
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def strings(value: object):
    if isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)
    elif isinstance(value, str):
        yield value


def media_targets() -> set[Path]:
    targets: set[Path] = {
        ROOT / "public/images/template-layers/background.png",
        ROOT / "public/images/thumbnail-assets/quiz-player.png",
        ROOT / "public/fonts/Minecraft-Bold.otf",
    }
    json_sources = list((ROOT / "data").glob("*.json")) + list((ROOT / "src/generated").glob("*.json"))
    for source in json_sources:
        for value in strings(json.loads(source.read_text(encoding="utf-8"))):
            relative = value.removeprefix("public/")
            if relative.startswith(("audio/", "images/", "fonts/", "mc-assets/")):
                path = ROOT / "public" / relative
                if path.suffix.lower() in MEDIA_SUFFIXES:
                    targets.add(path)
    kinds = set()
    for source in (ROOT / "data").glob("*.json"):
        for value in strings(json.loads(source.read_text(encoding="utf-8"))):
            if value in {"Block", "Enchantment", "Food", "Item", "Mineral", "Mob", "Plant", "Potion", "Structure", "Tool", "Weapon"}:
                kinds.add(value)
    for kind in kinds:
        targets.update({ROOT / "public/images/guess-types" / visibility / f"{kind}.png" for visibility in ("hidden", "visible")})
        slug = kind.casefold().replace(" ", "_")
        targets.add(ROOT / f"out/thumbnails/{slug}/default/{slug}.vertical.jpg")
    return targets


def main() -> None:
    targets = media_targets()
    image_targets = {path for path in targets if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}}
    for path in image_targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(PNG)

    audio_targets = {path for path in targets if path.suffix.lower() in {".mp3", ".m4a", ".wav", ".ogg"}}
    if audio_targets:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("CI necesita ffmpeg para crear audio fixture")
        with tempfile.TemporaryDirectory() as directory:
            for suffix, codec in ((".mp3", "libmp3lame"), (".m4a", "aac"), (".wav", "pcm_s16le"), (".ogg", "libvorbis")):
                source = Path(directory) / f"fixture{suffix}"
                subprocess.run(
                    [ffmpeg, "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "1", "-c:a", codec, str(source)],
                    check=True,
                )
                for path in (target for target in audio_targets if target.suffix.lower() == suffix):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if not path.exists():
                        path.write_bytes(source.read_bytes())

    for path in targets:
        if path.suffix.lower() == ".otf" and not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            font = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
            path.write_bytes(font.read_bytes() if font.is_file() else b"")
    print(f"prepared disposable media fixtures: {len(targets)} files")


if __name__ == "__main__":
    main()
