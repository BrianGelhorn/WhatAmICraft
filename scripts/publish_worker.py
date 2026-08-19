#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from publishing.settings import (
    apply_runtime,
    load_config,
    load_generation_schedule,
    load_schedule,
    next_run_iso,
    save_generation_schedule,
    save_schedule,
)
from review.storage import pending_queue_ids, read_json
from review.storage import publishing_state, save_stock_alert_state, stock_alert_state
from review.telegram import configured as telegram_configured
from review.telegram import send_message
from publishing.common import sha256
from video_formats import (
    current_template_video_names,
    format_id_for,
    format_label,
    priority_targets,
    ready_episodes,
    video_path,
)
from job_status import append_job_line, begin_job, finish_job

ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "data/quiz-copy-episodes.json"
OUTPUT_DIR = ROOT / "out/episodes"
LOG_DIR = ROOT / "out/logs"
PUBLISH_LOCK = ROOT / "out/publishing.lock"
CPUSETS = {
    "generation": os.getenv("GENERATION_CPUSET", "0-2"),
    "publishing": os.getenv("PUBLISHING_CPUSET", "3"),
}


def log(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now(timezone.utc).isoformat()} {text}"
    print(line, flush=True)
    with path.open("a", encoding="utf-8", errors="replace") as file:
        file.write(line + "\n")


def run_logged(command: list[str], log_name: str, label: str, lane: str = "main") -> subprocess.CompletedProcess:
    if lane in CPUSETS and shutil.which("taskset"):
        command = ["taskset", "-c", CPUSETS[lane], *command]
    path = LOG_DIR / log_name
    try:
        begin_job(label, "automatic", str(path), lane)
    except RuntimeError:
        log(path, "skip: another task is already running")
        return subprocess.CompletedProcess(command, 1)
    log(path, "run: " + " ".join(command))
    try:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert process.stdout
        for line in process.stdout:
            log(path, line.rstrip())
            append_job_line(line.rstrip(), lane)
        code = process.wait()
        log(path, f"exit: {code}")
        finish_job("completed" if code == 0 else "failed", code, lane=lane)
        return subprocess.CompletedProcess(command, code)
    except Exception as error:
        log(path, f"error: {error}")
        finish_job("failed", 1, str(error), lane)
        return subprocess.CompletedProcess(command, 1)


def _date(value: str | None) -> datetime | None:
    if not value:
        return None
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result


def is_due(config: dict, schedule: dict, now: datetime | None = None) -> bool:
    if not config["schedule"]["enabled"]:
        return False
    due = _date(schedule.get("nextRunAt"))
    return due is None or due <= (now or datetime.now(timezone.utc))


def generation_window_open(config: dict, schedule: dict, now: datetime | None = None) -> bool:
    if not config["schedule"]["enabled"]:
        return True
    due = _date(schedule.get("nextRunAt"))
    if due is None:
        return False
    guard = timedelta(minutes=config["generation"]["publishGuardMinutes"])
    return due - (now or datetime.now(timezone.utc)) > guard


def publishing_active() -> bool:
    return PUBLISH_LOCK.exists() and time.time() - PUBLISH_LOCK.stat().st_mtime <= 6 * 60 * 60


def episodes() -> list[dict]:
    return ready_episodes()


def video_for(episode: dict) -> Path:
    return video_path(episode)


def inventory() -> dict[str, list[str]]:
    current = episodes()
    current_names = current_template_video_names()
    videos = {
        episode["id"]
        for episode in current
        if video_for(episode).exists() and video_for(episode).name in current_names
    }
    published_state = publishing_state()["videos"]
    published = {
        episode["id"]
        for episode in current
        if video_for(episode).exists()
        and published_state.get(episode["id"], {}).get("sha256") == sha256(video_for(episode))
    }
    approved = set(pending_queue_ids()).intersection(videos)
    candidates = (videos - published) - approved
    by_format = {}
    for format_id in {format_id_for(episode) for episode in current}:
        format_episodes = [episode for episode in current if format_id_for(episode) == format_id]
        format_videos = {
            episode["id"]
            for episode in format_episodes
            if video_for(episode).exists() and video_for(episode).name in current_names
        }
        format_approved = approved.intersection(format_videos)
        format_candidates = candidates.intersection(format_videos)
        by_format[format_id] = {
            "label": format_label(format_id),
            "pending": sorted(format_approved),
            "candidates": sorted(format_candidates),
            "missing": [episode["id"] for episode in format_episodes if episode["id"] not in format_videos],
        }
    return {
        "pending": sorted(approved),
        "candidates": sorted(candidates),
        "stock": sorted(approved | candidates),
        "missing": [episode["id"] for episode in current if episode["id"] not in videos],
        "formats": by_format,
    }


def repost_episode() -> dict | None:
    state = publishing_state()["videos"]
    current_names = current_template_video_names()
    candidates = []
    for episode in episodes():
        record = state.get(episode["id"], {})
        if (
            not video_for(episode).exists()
            or video_for(episode).name not in current_names
            or record.get("sha256") != sha256(video_for(episode))
            or not record.get("platforms")
        ):
            continue
        dates = [
            platform.get("publishedAt", "")
            for platform in record["platforms"].values()
            if platform.get("publishedAt")
        ]
        candidates.append((max(dates, default=""), episode["id"], episode))
    return min(candidates, default=(None, None, None))[2]


def notify(text: str) -> None:
    if not telegram_configured():
        return
    try:
        send_message(os.environ["TELEGRAM_REVIEW_CHAT_ID"], text)
    except Exception as error:
        print(f"Telegram: {error}", file=sys.stderr, flush=True)


def choose_generation_format(config: dict, stock: dict) -> str | None:
    settings = config["generation"].get("formats", {})
    choices = []
    for format_id, value in settings.items():
        if not value.get("enabled") or format_id not in stock["formats"]:
            continue
        available = len(stock["formats"][format_id]["pending"]) + len(stock["formats"][format_id]["candidates"])
        choices.append((format_id, max(1, int(value.get("priority", 1))), available))
    if not choices:
        return None

    targets = priority_targets(settings, config["generation"]["targetStock"], [item[0] for item in choices])
    available_by_format = {format_id: available for format_id, _, available in choices}
    deficits = {
        format_id: targets[format_id] - available
        for format_id, _, available in choices
    }
    positive = [format_id for format_id, deficit in deficits.items() if deficit > 0 and stock["formats"][format_id]["missing"]]
    if positive:
        return min(positive, key=lambda format_id: (
            available_by_format[format_id] / targets[format_id],
            -targets[format_id],
            format_id,
        ))
    available_formats = [format_id for format_id, _, _ in choices if stock["formats"][format_id]["missing"]]
    if not available_formats:
        return None
    return min(
        available_formats,
        key=lambda format_id: (
            (len(stock["formats"][format_id]["pending"]) + len(stock["formats"][format_id]["candidates"]))
            / max(1, int(settings[format_id].get("priority", 1))),
            format_id,
        ),
    )


def alert_low_stock(approved_count: int, threshold: int) -> None:
    state = stock_alert_state()
    low = approved_count <= threshold
    empty = approved_count == 0
    if empty and not state.get("empty"):
        notify("ALERTA: No quedan videos aprobados en cola. Si toca publicar, voy a repostear el mas viejo disponible.")
    if 0 < approved_count <= threshold and not state.get("low"):
        notify(
            f"ALERTA: Quedan {approved_count} video(s) aprobados en la cola. "
            "La mini PC seguira generando candidatos; aproba los nuevos desde Telegram."
        )
    if state.get("low") != low or state.get("empty") != empty:
        save_stock_alert_state({"low": low, "empty": empty})


def publish_or_repost(config: dict, stock: dict[str, list[str]]) -> bool:
    if stock["pending"]:
        result = run_logged(
            [sys.executable, "-u", str(ROOT / "scripts/publish.py"), "--queue", "--limit", "1"],
            "publisher.log",
            "Publicación automática",
            "publishing",
        )
        return result.returncode == 0

    episode = repost_episode()
    if not episode:
        notify("ALERTA: No quedan videos aprobados ni publicaciones anteriores disponibles para reutilizar.")
        return True
    episode_id = episode["id"]
    target = episode["target"]["display_name"]
    notify(f"ALERTA: La cola quedo vacia. Voy a republicar {episode_id} - {target} para mantener la frecuencia.")
    result = run_logged(
        [sys.executable, "-u", str(ROOT / "scripts/publish.py"), "--episode", episode_id, "--force"],
        "publisher.log",
        f"Republicando automáticamente {episode_id} · {target}",
        "publishing",
    )
    if result.returncode == 0:
        notify(f"Repost completado: {episode_id} - {target}.")
    else:
        notify(f"No pude republicar {episode_id} - {target}. Revisa las credenciales en el panel.")
    return result.returncode == 0


def maybe_generate(config: dict, stock: dict[str, list[str]]) -> None:
    generation = config["generation"]
    schedule = load_generation_schedule()
    if not generation["enabled"] or not is_due({"schedule": generation}, schedule):
        return
    if publishing_active():
        log(LOG_DIR / "generator.log", "skip: publishing in progress")
        return
    if not generation_window_open(config, load_schedule()):
        log(LOG_DIR / "generator.log", "skip: publish window guard")
        return

    approved = len(stock["pending"])
    total_buffer = approved + len(stock["candidates"])
    retry_minutes = generation["intervalMinutes"]
    format_id = choose_generation_format(config, stock)
    if approved < generation["lowStockThreshold"] and total_buffer < generation["targetStock"] and format_id:
        missing_ids = stock["formats"].get(format_id, {}).get("missing", [])
        for episode_id in missing_ids:
            log(
                LOG_DIR / "generator.log",
                f"select episode={episode_id} format={format_id} label={format_label(format_id)}",
            )
            result = run_logged(
                [
                    sys.executable,
                    "-u",
                    str(ROOT / "scripts/produce_quiz_copy.py"),
                    "--render",
                    "--generate-audio",
                    "--episode",
                    episode_id,
                ],
                "generator.log",
                f"Generación automática · {episode_id} · {format_label(format_id)}",
                "generation",
            )
            if result.returncode == 0:
                if len(inventory()["stock"]) < generation["targetStock"]:
                    retry_minutes = 0
                break
            log(LOG_DIR / "generator.log", f"skip: {episode_id} falló; se prueba el siguiente")
    else:
        log(
            LOG_DIR / "generator.log",
            f"skip: approved={approved} buffer={total_buffer} target={generation['targetStock']} trigger={generation['lowStockThreshold']}",
        )
    save_generation_schedule(next_run_iso(retry_minutes))


def main() -> None:
    interval = int(os.getenv("PUBLISH_QUEUE_INTERVAL", "30"))
    while True:
        try:
            config = load_config()
            apply_runtime(config)
            stock = inventory()
            alert_low_stock(len(stock["pending"]), config["generation"]["lowStockThreshold"])
            if is_due(config, load_schedule()):
                published_ok = publish_or_repost(config, stock)
                retry_minutes = config["schedule"]["intervalMinutes"] if published_ok else min(15, config["schedule"]["intervalMinutes"])
                save_schedule(next_run_iso(retry_minutes))
            else:
                maybe_generate(config, stock)
        except Exception as error:
            log(LOG_DIR / "publisher-worker.log", f"Scheduler: {error}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
