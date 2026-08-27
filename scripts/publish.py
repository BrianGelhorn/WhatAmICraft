#!/usr/bin/env python3
import argparse
import json
import sys
import time
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from publishing import PUBLISHERS
from publishing.common import PublishRequest, sha256
from publishing.settings import apply_runtime, enabled_platforms, load_config
from review.storage import pending_queue_ids, publishing_state, save_published_platform, set_queue_status
from template_artifacts import validate_artifact
from thumbnails import copy_thumbnail_config, render_thumbnails
from video_formats import ready_episodes, thumbnail_path, video_stem

ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "data/quiz-copy-episodes.json"
OUTPUT_DIR = ROOT / "out/episodes"
THUMBNAIL_DIR = ROOT / "out/thumbnails"
PUBLISH_LOCK = ROOT / "out/publishing.lock"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def episodes() -> list[dict]:
    return ready_episodes()


def video_for(episode: dict) -> Path:
    return OUTPUT_DIR / f"{video_stem(episode)}.mp4"


def thumbnail_for(episode: dict) -> Path | None:
    path = thumbnail_path(episode, "vertical")
    return path if path.exists() else None


def ensure_thumbnail(episode: dict) -> Path:
    path = thumbnail_for(episode)
    if path is None:
        render_thumbnails(copy_thumbnail_config(episode), video_stem(episode))
        path = thumbnail_for(episode)
    if path is None:
        raise RuntimeError(f"No se pudo generar la miniatura vertical de {episode['id']}")
    return path


def publish_request(episode: dict, config: dict) -> PublishRequest:
    kind = episode["target"]["kind"].replace("_", " ").title()
    values = {"episode_id": episode["id"], "kind": kind}
    return PublishRequest(
        episode_id=episode["id"],
        video=video_for(episode),
        thumbnail=thumbnail_for(episode),
        title=config["title"].format(**values),
        caption=config["caption"].format(**values),
        hashtags=config["hashtags"],
    )


def already_published(episode: dict, platforms: list[str], state: dict) -> bool:
    video = video_for(episode)
    record = state["videos"].get(episode["id"], {})
    return (
        video.exists()
        and record.get("sha256") == sha256(video)
        and all(platform in record.get("platforms", {}) for platform in platforms)
    )


def mark_completed_if_done(episode_id: str, required_platforms: list[str], record: dict) -> None:
    if required_platforms and all(platform in record.get("platforms", {}) for platform in required_platforms):
        set_queue_status(episode_id, "completed")


@contextmanager
def publish_lock():
    try:
        PUBLISH_LOCK.mkdir(parents=True)
    except FileExistsError:
        if time.time() - PUBLISH_LOCK.stat().st_mtime <= 6 * 60 * 60:
            raise RuntimeError("Ya hay una publicacion en curso")
        PUBLISH_LOCK.rmdir()
        PUBLISH_LOCK.mkdir()
    try:
        yield
    finally:
        PUBLISH_LOCK.rmdir()


def main() -> int:
    parser = argparse.ArgumentParser(description="Publica episodios renderizados en redes sociales")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--episode", help="ID del episodio, por ejemplo mc-04")
    group.add_argument("--queue", action="store_true", help="Procesa la cola aprobada por el bot")
    parser.add_argument("--platform", action="append", choices=[*PUBLISHERS, "all"])
    parser.add_argument("--limit", type=int, help="Cantidad máxima de episodios a procesar")
    parser.add_argument("--force", action="store_true", help="Vuelve a publicar aunque ya exista en el registro")
    parser.add_argument("--dry-run", action="store_true", help="Muestra el plan sin subir nada")
    args = parser.parse_args()

    with publish_lock():
        return run(args)


def run(args: argparse.Namespace) -> int:
    selected = episodes()
    if args.episode:
        selected = [episode for episode in selected if episode["id"] == args.episode]
        if not selected:
            raise RuntimeError(f"Episodio inexistente o inválido: {args.episode}")
    elif args.queue:
        queued = set(pending_queue_ids())
        selected = [episode for episode in selected if episode["id"] in queued]
    config = load_config()
    apply_runtime(config)
    active_platforms = enabled_platforms(config)
    platforms = enabled_platforms(config) if not args.platform else (
        list(PUBLISHERS) if "all" in args.platform else list(dict.fromkeys(args.platform))
    )
    if not platforms:
        raise RuntimeError("No hay plataformas activadas")
    state = publishing_state()
    if args.queue and not args.force:
        pending = []
        for episode in selected:
            if already_published(episode, platforms, state):
                if not args.dry_run:
                    set_queue_status(episode["id"], "completed")
            else:
                pending.append(episode)
        selected = pending
    if args.limit is not None:
        if args.limit < 1:
            raise ValueError("--limit debe ser mayor que cero")
        selected = selected[: args.limit]
    failed = False

    for episode in selected:
        item = publish_request(episode, config)
        if not item.video.exists():
            print(f"{episode['id']}: omitido, falta {item.video.name}")
            if args.queue and not args.dry_run:
                set_queue_status(episode["id"], "failed", f"Falta {item.video.name}")
                failed = True
            continue
        try:
            artifact = validate_artifact(item.video, episode_id=episode["id"], root=ROOT)
        except RuntimeError as error:
            print(f"{episode['id']}: omitido, {error}", file=sys.stderr)
            if args.queue and not args.dry_run:
                set_queue_status(episode["id"], "failed", str(error))
            failed = True
            continue
        print(f"{episode['id']}: {item.video.name}")
        print(f"  plantilla: {artifact['templateVersion']}")
        if args.dry_run:
            print(f"  publicar: {', '.join(platforms)}")
            continue

        fingerprint = sha256(item.video)
        record = state["videos"].setdefault(episode["id"], {"sha256": fingerprint, "platforms": {}})
        if record.get("sha256") != fingerprint:
            record.update({"sha256": fingerprint, "platforms": {}})
        episode_errors = []
        for platform in platforms:
            if platform in record["platforms"] and not args.force:
                print(f"  {platform}: ya publicado")
                continue
            try:
                platform_item = replace(item, thumbnail=ensure_thumbnail(episode)) if platform == "youtube" else item
                result = PUBLISHERS[platform](platform_item)
                record["platforms"][platform] = {
                    **result,
                    "publishedAt": datetime.now(timezone.utc).isoformat(),
                    "publishedTitle": platform_item.title,
                    "publishedCaption": platform_item.caption,
                    "publishedHashtags": list(platform_item.hashtags),
                    "templateVersion": artifact.get("templateVersion"),
                }
                save_published_platform(episode["id"], fingerprint, platform, record["platforms"][platform])
                print(f"  {platform}: listo")
            except Exception as error:
                failed = True
                episode_errors.append(f"{platform}: {error}")
                print(f"  {platform}: ERROR: {error}", file=sys.stderr)
        if args.queue:
            set_queue_status(
                episode["id"],
                "failed" if episode_errors else "completed",
                "; ".join(episode_errors) or None,
            )
        elif not episode_errors:
            mark_completed_if_done(episode["id"], active_platforms, record)
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
