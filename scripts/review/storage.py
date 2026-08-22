import json
import re
import shutil
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANK_PATH = ROOT / "data/quiz-copy-episodes.json"
HINTS_PENDING_PATH = ROOT / "data/pending-hint-regenerations.json"
QUEUE_PATH = ROOT / "out/publishing-queue.json"
PUBLISHING_STATE_PATH = ROOT / "out/publishing-state.json"
PUBLISHING_SCHEDULE_PATH = ROOT / "out/publishing-schedule.json"
GENERATION_SCHEDULE_PATH = ROOT / "out/generation-schedule.json"
STOCK_ALERT_PATH = ROOT / "out/stock-alert-state.json"

import state_db
from template_artifacts import validate_artifact
from video_formats import FORMAT_DEFINITIONS, ROOT as FORMAT_ROOT, format_id_for, normalize_episode, video_path


def read_json(path: Path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


@contextmanager
def _lock(path: Path):
    lock = path.with_suffix(path.suffix + ".lock")
    deadline = time.monotonic() + 10
    while True:
        try:
            lock.mkdir(parents=True)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise RuntimeError(f"No se pudo bloquear {path.name}")
            time.sleep(0.1)
    try:
        yield
    finally:
        lock.rmdir()


def state_db_path() -> Path:
    return ROOT / "out/app-state.sqlite3"


def ensure_state_db() -> None:
    state_db.migrate_json_state(
        db_path=state_db_path(),
        queue_path=QUEUE_PATH,
        publishing_state_path=PUBLISHING_STATE_PATH,
        pending_hints_path=HINTS_PENDING_PATH,
        publishing_schedule_path=PUBLISHING_SCHEDULE_PATH,
        generation_schedule_path=GENERATION_SCHEDULE_PATH,
        stock_alert_path=STOCK_ALERT_PATH,
    )


def queue_items() -> list[dict]:
    ensure_state_db()
    return state_db.queue_items(state_db_path())


def pending_hints_items() -> list[dict]:
    ensure_state_db()
    return state_db.pending_hints_items(state_db_path())


def publishing_state() -> dict:
    ensure_state_db()
    return state_db.publishing_state(state_db_path())


def save_published_platform(episode_id: str, fingerprint: str, platform: str, payload: dict) -> None:
    ensure_state_db()
    state_db.set_published_platform(episode_id, fingerprint, platform, payload, state_db_path())


def save_video_metrics(episode_id: str, platform: str, video: dict) -> None:
    ensure_state_db()
    state_db.set_video_metrics(episode_id, platform, video, state_db_path())


def video_metrics() -> list[dict]:
    ensure_state_db()
    return state_db.video_metrics(state_db_path())


def video_metric_snapshots() -> list[dict]:
    ensure_state_db()
    return state_db.video_metric_snapshots(state_db_path())


def stock_alert_state() -> dict:
    ensure_state_db()
    return state_db.load_flag("stock_alert", {"low": False}, state_db_path())


def save_stock_alert_state(value: dict) -> None:
    ensure_state_db()
    state_db.save_flag("stock_alert", value, state_db_path())


def _episode_id(value: str) -> str:
    if not re.fullmatch(r"mc-\d+", value):
        raise ValueError("ID de episodio inválido")
    return value


def _episode(episode_id: str) -> tuple[str, dict] | None:
    for format_id, definition in FORMAT_DEFINITIONS.items():
        bank_path = ROOT / definition["bank"].relative_to(FORMAT_ROOT)
        bank = read_json(bank_path, {"episodes": []})
        for raw_episode in bank.get("episodes", []):
            episode = normalize_episode(raw_episode, format_id)
            if episode["id"] == episode_id:
                return format_id_for(episode), episode
    return None


def queue_episode(episode_id: str) -> None:
    episode_id = _episode_id(episode_id)
    found = _episode(episode_id)
    episode = found[1] if found else None
    if not episode or not episode.get("unique_answer") or episode.get("needs_review"):
        raise RuntimeError(f"{episode_id} todavía no está listo para publicar")
    video = video_path(episode, ROOT)
    if not video.exists():
        raise RuntimeError(f"Falta el video de {episode_id}")
    validate_artifact(video, episode_id=episode_id, root=ROOT)
    ensure_state_db()
    state_db.upsert_queue_item(episode_id, db_path=state_db_path())


def pending_queue_ids() -> list[str]:
    ensure_state_db()
    return state_db.pending_queue_ids(state_db_path())


def remove_queue_item(episode_id: str) -> None:
    episode_id = _episode_id(episode_id)
    ensure_state_db()
    state_db.remove_queue_item(episode_id, state_db_path())


def set_queue_status(episode_id: str, status: str, error: str | None = None) -> None:
    ensure_state_db()
    state_db.set_queue_status(episode_id, status, error, state_db_path())


def pend_hints(episode_id: str) -> None:
    episode_id = _episode_id(episode_id)
    found = _episode(episode_id)
    if not found or found[0] != "clues":
        raise RuntimeError("Las pistas solo están disponibles para el quiz definitivo")
    bank = read_json(BANK_PATH)
    episode = next((item for item in bank["episodes"] if item["id"] == episode_id), None)
    if not episode:
        raise RuntimeError(f"No existe {episode_id}")
    episode["needsReview"] = True
    write_json(BANK_PATH, bank)

    ensure_state_db()
    localized = {
        "target": episode["answer"]["displayName"],
        "clues": [clue["text"] for clue in episode["clues"]],
    }
    state_db.upsert_pending_hint(episode_id, episode, localized, state_db_path())


def clear_hints(episode_id: str) -> None:
    episode_id = _episode_id(episode_id)
    found = _episode(episode_id)
    if not found or found[0] != "clues":
        raise RuntimeError("Las pistas solo están disponibles para el quiz definitivo")
    bank = read_json(BANK_PATH)
    episode = next((item for item in bank["episodes"] if item["id"] == episode_id), None)
    if not episode:
        raise RuntimeError(f"No existe {episode_id}")
    episode["needsReview"] = False
    write_json(BANK_PATH, bank)
    ensure_state_db()
    state_db.remove_pending_hint(episode_id, state_db_path())


def reject_episode(episode_id: str) -> None:
    episode_id = _episode_id(episode_id)
    found = _episode(episode_id)
    if not found:
        raise RuntimeError(f"No existe {episode_id}")
    format_id = found[0]
    bank_path = ROOT / FORMAT_DEFINITIONS[format_id]["bank"].relative_to(FORMAT_ROOT)
    bank = read_json(bank_path)
    bank["episodes"] = [item for item in bank["episodes"] if item["id"] != episode_id]
    write_json(bank_path, bank)

    for video in (ROOT / "out/episodes").glob(f"{episode_id}-*.mp4"):
        video.unlink()
    for artifact in (ROOT / "out/episodes").glob(f"{episode_id}-*.artifact.json"):
        artifact.unlink()
    for thumbnail in (ROOT / "out/thumbnails").rglob(f"{episode_id}-*.jpg"):
        thumbnail.unlink()
    audio = ROOT / f"public/audio/quiz-copy/{episode_id}"
    if audio.exists():
        shutil.rmtree(audio)

    ensure_state_db()
    state_db.remove_pending_hint(episode_id, state_db_path())
    state_db.remove_queue_item(episode_id, state_db_path())
    state_db.remove_published(episode_id, state_db_path())
