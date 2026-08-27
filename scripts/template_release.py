#!/usr/bin/env python3
"""Promote the installed template release after a canary review."""

from __future__ import annotations

import argparse

from template_artifacts import (
    activate_template_version,
    active_template_version,
    read_artifact,
    release_version,
    write_legacy_artifact,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Administra la versión activa de la plantilla instalada")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--status", action="store_true")
    group.add_argument("--activate")
    group.add_argument("--migrate-legacy", action="store_true")
    args = parser.parse_args()
    if args.status:
        print(f"release={release_version()}")
        print(f"active={active_template_version()}")
        return 0
    if args.migrate_legacy:
        from video_formats import all_episodes, thumbnail_path, video_path

        migrated = 0
        skipped = 0
        for episode in all_episodes():
            video = video_path(episode)
            if not video.is_file() or read_artifact(video):
                continue
            thumbnail = thumbnail_path(episode, "vertical")
            if not thumbnail.is_file():
                skipped += 1
                continue
            write_legacy_artifact(episode_id=episode["id"], video=video, thumbnail=thumbnail)
            migrated += 1
        print(f"manifests legacy creados: {migrated}; omitidos por falta de miniatura: {skipped}")
        return 0
    activate_template_version(args.activate)
    print(f"plantilla activa: {args.activate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
