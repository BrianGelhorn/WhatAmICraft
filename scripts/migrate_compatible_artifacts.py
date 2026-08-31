#!/usr/bin/env python3
"""Keep artifacts active when a deploy does not change their template."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

TEMPLATE_PATHS = (
    "src/",
    "templates/",
    "public/mc-assets/",
    "remotion.config.ts",
    "package.json",
    "package-lock.json",
    "scripts/produce_quiz_copy.py",
    "scripts/produce_mystery_v2.py",
    "scripts/produce_mystery_prefab_gallery.py",
    "scripts/thumbnails.py",
    "scripts/video_formats.py",
)


def compatible(repo: Path, previous: str, release: str) -> bool:
    if not re.fullmatch(r"[0-9a-f]{40}", previous):
        return False
    exists = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{previous}^{{commit}}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if exists.returncode:
        return False
    unchanged = subprocess.run(
        ["git", "-C", str(repo), "diff", "--quiet", previous, release, "--", *TEMPLATE_PATHS],
    )
    return unchanged.returncode == 0


def migrate(episodes_dir: Path, release: str, is_compatible) -> int:
    if not episodes_dir.is_dir():
        raise FileNotFoundError(f"Video storage is unavailable: {episodes_dir}")
    migrated = 0
    for path in episodes_dir.glob("*.artifact.json"):
        try:
            artifact = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(artifact, dict):
            continue
        previous = artifact.get("templateVersion")
        if artifact.get("legacy") or previous == release or not isinstance(previous, str):
            continue
        if not is_compatible(previous):
            continue
        artifact["templateVersion"] = release
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(path)
        migrated += 1
    return migrated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes-dir", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--release", required=True)
    args = parser.parse_args()
    count = migrate(args.episodes_dir, args.release, lambda previous: compatible(args.repo, previous, args.release))
    print(f"Compatible template artifacts migrated: {count}")


if __name__ == "__main__":
    main()
