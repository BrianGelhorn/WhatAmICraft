#!/usr/bin/env python3
import argparse
import shutil
import subprocess
from pathlib import Path

from mystery_prefabs import GENERATED_PATH, ROOT, load_prefab_catalog
from production_common import write_json


OUTPUT = ROOT / "out/previews/mystery-prefab-gallery.mp4"
POSTER = ROOT / "out/previews/mystery-prefab-gallery.png"


def main() -> int:
    parser = argparse.ArgumentParser(description="Produce the numbered Mystery V2 prefab gallery")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--poster", action="store_true")
    args = parser.parse_args()
    catalog = load_prefab_catalog()
    if args.dry_run:
        print(f"ok: {len(catalog['prefabs'])} draft prefabs")
        return 0
    write_json(GENERATED_PATH, catalog)
    print(f"config: {GENERATED_PATH.relative_to(ROOT)}")
    if args.render:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            "node", "node_modules/@remotion/cli/remotion-cli.js", "render", "MysteryPrefabGallery", str(OUTPUT),
            "--frames=0-119", "--concurrency=1", "--codec=h264", "--crf=20",
        ], cwd=ROOT, check=True, timeout=1800)
        print(f"render: {OUTPUT.relative_to(ROOT)}")
    if args.poster:
        if not OUTPUT.is_file():
            raise RuntimeError("Usa --render antes de --poster")
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("Poster requiere ffmpeg en PATH")
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-ss", "2", "-i", str(OUTPUT), "-frames:v", "1", str(POSTER)], cwd=ROOT, check=True, timeout=180)
        print(f"poster: {POSTER.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
