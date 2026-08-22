#!/usr/bin/env python3
import hashlib
import json
import os
import secrets
import signal
import shutil
import socket
import subprocess
import sys
import threading
import time
import re
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review.storage import (  # noqa: E402
    pend_hints,
    clear_hints,
    pending_hints_items,
    pending_queue_ids,
    publishing_state,
    queue_episode,
    queue_items,
    read_json,
    remove_queue_item,
    reject_episode,
)
from analytics import build_snapshot, sync_all, write_exports  # noqa: E402
from analytics_client import AnalyticsApiError, request_json as analytics_request, request_text as analytics_text  # noqa: E402
from clues_client import CluesApiError, request_json as clues_request  # noqa: E402
from monitor_client import MonitorApiError, request_json as monitor_request  # noqa: E402
from publishing import PUBLISHERS  # noqa: E402
from publishing.common import json_request, sha256  # noqa: E402
from publishing.settings import (  # noqa: E402
    apply_runtime,
    credential_status,
    delete_secrets,
    load_config,
    load_generation_schedule,
    load_schedule,
    next_run_iso,
    save_config,
    save_generation_schedule,
    save_schedule,
    save_secrets,
    stored_secrets,
    tiktok_account,
)
from video_formats import (  # noqa: E402
    FORMAT_DEFINITIONS,
    choose_weighted_format,
    all_episodes,
    current_template_video_names,
    format_id_for,
    format_label,
    priority_targets,
    video_path,
    thumbnail_path,
)
from job_status import (  # noqa: E402
    append_job_line,
    begin_job,
    finish_job,
    read_job,
    set_job_pid,
)
from music_library import (  # noqa: E402
    MUSIC_EXTENSIONS,
    delete_track,
    load_library,
    original_starts,
    set_original_starts,
    validate_starts,
    validate_templates,
    validate_youtube_url,
)

INDEX_PATH = ROOT / "dashboard/index.html"
BANK_PATH = ROOT / "data/quiz-copy-episodes.json"
OUTPUT_DIR = ROOT / "out/episodes"
LEGACY_OUTPUT_DIR = ROOT / "backups/legacy-template-20260814/episodes"
THUMBNAIL_DIR = ROOT / "out/thumbnails"
STATE_DB_PATH = ROOT / "out/app-state.sqlite3"
LOG_DIR = ROOT / "out/logs"
BACKUP_DIR = ROOT / "backups/ops"
CONTEXT_SNAPSHOT_PATH = ROOT / "out/context-snapshot.md"
JOB_LOCK = threading.Lock()
ANALYTICS_LOCK = threading.Lock()
ANALYTICS_API_URL = os.getenv("ANALYTICS_API_URL", "").rstrip("/")
MONITOR_API_URL = os.getenv("MONITOR_API_URL", "").rstrip("/")
JOB = {"status": "idle", "label": "", "lines": [], "returnCode": None}
ACTIVE_PROCESSES = {}
CANCEL_REQUESTED = {}
CPUSETS = {
    "generation": os.getenv("GENERATION_CPUSET", "0-2"),
    "publishing": os.getenv("PUBLISHING_CPUSET", "3"),
}
TIKTOK_REDIRECT_URI = os.getenv(
    "TIKTOK_REDIRECT_URI",
    "https://what-am-i-craft.tail6cc348.ts.net:8443/api/tiktok/callback/",
)
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://what-am-i-craft.tail6cc348.ts.net:8443/")
YOUTUBE_REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI", DASHBOARD_URL.rstrip("/") + "/api/youtube/callback/")
TIKTOK_TOKEN_KEYS = {
    "TIKTOK_ACCESS_TOKEN", "TIKTOK_REFRESH_TOKEN", "TIKTOK_ACCESS_EXPIRES_AT",
    "TIKTOK_OPEN_ID", "TIKTOK_DISPLAY_NAME", "TIKTOK_AVATAR_URL",
}
OAUTH_REQUESTS: dict[str, tuple[str, float]] = {}
YOUTUBE_OAUTH_STATES: dict[str, float] = {}
TIKTOK_SCOPES = {"user.info.basic", "video.publish", "video.list"}
YOUTUBE_SCOPES = {
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
}


def _pkce_challenge(verifier: str) -> str:
    return hashlib.sha256(verifier.encode("ascii")).hexdigest()


def tiktok_connect_url() -> str:
    apply_runtime()
    client_key = os.getenv("TIKTOK_CLIENT_KEY")
    if not client_key or not os.getenv("TIKTOK_CLIENT_SECRET"):
        raise RuntimeError("Guardá primero el Client Key y Client Secret de TikTok")
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(64)
    OAUTH_REQUESTS[state] = (verifier, time.time() + 600)
    return "https://www.tiktok.com/v2/auth/authorize/?" + urlencode({
        "client_key": client_key,
        "response_type": "code",
        "scope": ",".join(sorted(TIKTOK_SCOPES)),
        "redirect_uri": TIKTOK_REDIRECT_URI,
        "state": state,
        "code_challenge": _pkce_challenge(verifier),
        "code_challenge_method": "S256",
        "disable_auto_auth": "1",
    })


def complete_tiktok_login(query: dict[str, list[str]]) -> None:
    state = query.get("state", [""])[0]
    pending = OAUTH_REQUESTS.pop(state, None)
    if not pending or pending[1] < time.time():
        raise RuntimeError("La conexión venció; volvé a intentar")
    if query.get("error"):
        raise RuntimeError(query.get("error_description", query["error"])[0])
    code = query.get("code", [""])[0]
    if not code:
        raise RuntimeError("TikTok no devolvió el código de autorización")
    apply_runtime()
    token, _ = json_request(
        "https://open.tiktokapis.com/v2/oauth/token/",
        method="POST",
        form={
            "client_key": os.environ["TIKTOK_CLIENT_KEY"],
            "client_secret": os.environ["TIKTOK_CLIENT_SECRET"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": TIKTOK_REDIRECT_URI,
            "code_verifier": pending[0],
        },
    )
    if not TIKTOK_SCOPES.issubset(set(str(token.get("scope", "")).split(","))):
        raise RuntimeError("TikTok no autorizó todos los permisos necesarios")
    profile, _ = json_request(
        "https://open.tiktokapis.com/v2/user/info/?fields=open_id,display_name,avatar_url",
        headers={"Authorization": f"Bearer {token['access_token']}"},
    )
    user = profile["data"]["user"]
    save_secrets({
        "TIKTOK_ACCESS_TOKEN": token["access_token"],
        "TIKTOK_REFRESH_TOKEN": token["refresh_token"],
        "TIKTOK_ACCESS_EXPIRES_AT": str(int(time.time()) + int(token["expires_in"])),
        "TIKTOK_OPEN_ID": token.get("open_id", user.get("open_id", "")),
        "TIKTOK_DISPLAY_NAME": user.get("display_name", ""),
        "TIKTOK_AVATAR_URL": user.get("avatar_url", ""),
    })


def disconnect_tiktok() -> None:
    apply_runtime()
    values = stored_secrets()
    token = values.get("TIKTOK_ACCESS_TOKEN")
    if token and values.get("TIKTOK_CLIENT_KEY") and values.get("TIKTOK_CLIENT_SECRET"):
        json_request(
            "https://open.tiktokapis.com/v2/oauth/revoke/",
            method="POST",
            form={"client_key": values["TIKTOK_CLIENT_KEY"], "client_secret": values["TIKTOK_CLIENT_SECRET"], "token": token},
        )
    delete_secrets(TIKTOK_TOKEN_KEYS)


def youtube_connect_url() -> str:
    apply_runtime()
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    if not client_id or not os.getenv("YOUTUBE_CLIENT_SECRET"):
        raise RuntimeError("Guardá primero el Client ID y Client Secret de YouTube")
    state = secrets.token_urlsafe(32)
    YOUTUBE_OAUTH_STATES[state] = time.time() + 600
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": client_id,
        "redirect_uri": YOUTUBE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(sorted(YOUTUBE_SCOPES)),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "state": state,
    })


def complete_youtube_login(query: dict[str, list[str]]) -> None:
    state = query.get("state", [""])[0]
    expires_at = YOUTUBE_OAUTH_STATES.pop(state, 0)
    if expires_at < time.time():
        raise RuntimeError("La conexión venció; volvé a intentar")
    if query.get("error"):
        raise RuntimeError(query.get("error_description", query["error"])[0])
    code = query.get("code", [""])[0]
    if not code:
        raise RuntimeError("YouTube no devolvió el código de autorización")
    apply_runtime()
    token, _ = json_request(
        "https://oauth2.googleapis.com/token",
        method="POST",
        form={
            "client_id": os.environ["YOUTUBE_CLIENT_ID"],
            "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": YOUTUBE_REDIRECT_URI,
        },
    )
    if not token.get("refresh_token"):
        raise RuntimeError("Google no devolvió un permiso permanente; volvé a conectar la cuenta")
    save_secrets({"YOUTUBE_REFRESH_TOKEN": token["refresh_token"]})


def episode_video(episode: dict) -> Path:
    return video_path(episode)


def episode_thumbnail(episode: dict) -> Path:
    return thumbnail_path(episode)


def thumbnail_url(path: Path) -> str:
    return f"/thumbnails/{quote(path.relative_to(THUMBNAIL_DIR).as_posix(), safe='/')}"


def internet_ok() -> bool:
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=3):
            return True
    except OSError:
        return False


def tail(path: Path, lines: int = 25) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:]


def safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-").lower() or "job"


def append_log(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", errors="replace") as file:
        file.write(line.rstrip() + "\n")


def diagnostics_state() -> dict:
    config = load_config()
    episodes = all_episodes()
    videos = list(OUTPUT_DIR.glob("*.mp4"))
    video_ids = {episode["id"] for episode in episodes if episode_video(episode).exists()}
    queue = queue_items()
    approved = [item for item in queue if item.get("status") == "pending"]
    publishing = publishing_state()["videos"]
    candidates = video_ids - set(publishing) - {item["episodeId"] for item in approved}
    disk = shutil.disk_usage(OUTPUT_DIR if OUTPUT_DIR.exists() else ROOT)
    failed = [item for item in queue if item.get("status") == "failed"]
    backups = sorted(BACKUP_DIR.glob("state-*.zip")) if BACKUP_DIR.exists() else []
    logs = []
    log_paths = sorted(LOG_DIR.glob("*.log")) + sorted((LOG_DIR / "jobs").glob("*.log")) if LOG_DIR.exists() else []
    for path in log_paths[-6:]:
        logs.append({"name": path.name, "lines": tail(path, 12)})
    return {
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "internet": internet_ok(),
        "database": {
            "path": str(STATE_DB_PATH),
            "exists": STATE_DB_PATH.exists(),
            "sizeKb": round(STATE_DB_PATH.stat().st_size / 1024, 1) if STATE_DB_PATH.exists() else 0,
        },
        "disk": {
            "totalGb": round(disk.total / 1024**3, 1),
            "usedGb": round(disk.used / 1024**3, 1),
            "freeGb": round(disk.free / 1024**3, 1),
            "usedPct": round(disk.used / disk.total * 100, 1),
        },
        "counts": {
            "episodes": len(episodes),
            "videos": len(videos),
            "published": len(publishing),
            "queue": len(queue),
            "pending": len(approved),
            "candidates": len(candidates),
            "failed": len(failed),
            "pendingHints": len(pending_hints_items()),
        },
        "schedules": {
            "publishing": load_schedule().get("nextRunAt"),
            "generation": load_generation_schedule().get("nextRunAt"),
        },
        "access": {
            "dashboard": DASHBOARD_URL,
            "publicVideos": config["platforms"]["instagram"].get("publicVideoBaseUrl") or os.getenv("PUBLIC_VIDEO_BASE_URL", ""),
        },
        "ops": {
            "backups": len(backups),
            "latestBackup": datetime.fromtimestamp(backups[-1].stat().st_mtime, timezone.utc).isoformat() if backups else None,
            "contextSnapshot": str(CONTEXT_SNAPSHOT_PATH),
            "contextUpdated": datetime.fromtimestamp(CONTEXT_SNAPSHOT_PATH.stat().st_mtime, timezone.utc).isoformat()
            if CONTEXT_SNAPSHOT_PATH.exists()
            else None,
        },
        "services": [
            {"name": "dashboard", "state": "running", "status": "responding"},
            {"name": "analytics-api", "state": "external" if ANALYTICS_API_URL else "embedded", "status": "configured" if ANALYTICS_API_URL else "local fallback"},
            {"name": "monitor", "state": "external" if MONITOR_API_URL else "disabled", "status": "configured" if MONITOR_API_URL else "not configured"},
            {"name": "bot", "state": "external", "status": "check via SSH"},
            {"name": "publisher-worker", "state": "external", "status": "check via SSH"},
            {"name": "media", "state": "external", "status": "check via SSH"},
        ],
        "errors": failed[-5:],
        "logs": logs,
    }


def analytics_snapshot() -> dict:
    if not ANALYTICS_API_URL:
        return build_snapshot()
    try:
        status, result = analytics_request("/api/analytics")
        if not isinstance(result, dict):
            raise RuntimeError("El servicio de analytics devolvió una respuesta inválida")
        if status != HTTPStatus.OK:
            raise RuntimeError(result.get("error", "El servicio de analytics rechazó la consulta"))
        return result
    except (AnalyticsApiError, RuntimeError, ValueError) as error:
        now = datetime.now(timezone.utc).isoformat()
        message = str(error)[:240]
        return {
            "schemaVersion": 1,
            "generatedAt": now,
            "summary": {"videos": 0, "views": 0, "engagements": 0, "engagementRateByViews": None},
            "platforms": [{"platform": platform, "videos": 0, "views": 0, "engagements": 0, "error": message} for platform in ("youtube", "tiktok", "instagram", "facebook")],
            "series": [],
            "cohorts": [],
            "quality": [],
            "trends": [],
            "alerts": [],
            "recommendations": [],
            "videos": [],
            "observations": [f"Analytics no disponible: {message}"],
            "definitions": {},
            "limitations": [],
        }


def dashboard_state() -> dict:
    queue = {"items": queue_items()}
    queue_by_id = {item["episodeId"]: item for item in queue["items"]}
    failed = [item for item in queue["items"] if item.get("status") == "failed" and item.get("error")]
    pending = {"items": pending_hints_items()}
    pending_ids = {item["episodeId"] for item in pending["items"]}
    publishing = publishing_state()["videos"]
    new_video_names = current_template_video_names()
    legacy_videos = []
    items = []
    episodes = all_episodes()
    active_episodes = episodes
    for episode in active_episodes:
        video = episode_video(episode)
        thumbnail = episode_thumbnail(episode)
        thumbnails = {"vertical": thumbnail_path(episode, "vertical")}
        thumbnail_urls = {
            variant: thumbnail_url(path)
            for variant, path in thumbnails.items()
            if path.exists()
        }
        queue_item = queue_by_id.get(episode["id"])
        has_new_video = video.exists() and video.name in new_video_names
        record = publishing.get(episode["id"], {})
        current_publication = has_new_video and record.get("sha256") == sha256(video)
        platforms = list(record.get("platforms", {})) if current_publication else []
        if queue_item and not current_publication and queue_item["status"] != "pending":
            queue_item = None
        if episode["id"] in pending_ids or episode.get("needs_review"):
            status = "Pistas pendientes"
        elif platforms:
            status = "Publicado"
        elif queue_item:
            status = {"pending": "En cola", "failed": "Error al publicar", "completed": "Publicado"}.get(
                queue_item["status"], queue_item["status"]
            )
        elif has_new_video:
            status = "Esperando aprobación"
        else:
            status = "Sin generar"

        clue_details = [
            {
                "number": index + 1,
                "text": clue.get("text", ""),
                "voiceText": clue.get("voice", {}).get("text", ""),
                "voiceUrl": (
                    f"/audio/{quote(str(clue.get('voice', {}).get('publicSrc', '')).removeprefix('audio/'), safe='/')}"
                    if clue.get("voice", {}).get("publicSrc") else None
                ),
            }
            for index, clue in enumerate(episode.get("clues", []))
        ]

        items.append(
            {
                "id": episode["id"],
                "target": episode["target"].get("display_name", episode["target"]["id"].replace("_", " ").title()),
                "kind": episode["target"]["kind"].replace("_", " ").title(),
                "format": format_id_for(episode),
                "formatLabel": format_label(format_id_for(episode)),
                "clues": len(episode.get("clues", [])),
                "needsReview": episode.get("needs_review", False),
                "hasVideo": has_new_video,
                "hasLegacyVideo": False,
                "hasThumbnail": thumbnail.exists(),
                "hasThumbnails": len(thumbnail_urls) == len(thumbnails),
                "videoUrl": f"/videos/{video.name}" if has_new_video else None,
                "thumbnailUrl": thumbnail_url(thumbnail) if thumbnail.exists() else None,
                "thumbnailUrls": thumbnail_urls,
                "status": status,
                "queueStatus": queue_item["status"] if queue_item else None,
                "platforms": platforms,
                "answer": episode["answer"].get("displayName", episode["answer"].get("id", "")),
                "clueDetails": clue_details,
                "revealText": episode.get("reveal", {}).get("voice", {}).get("text", ""),
            }
        )
    job = read_job()
    job["lines"] = job["lines"][-12:]
    config = load_config()
    format_settings = config["generation"].get("formats", {})
    targets = priority_targets(format_settings, config["generation"]["targetStock"])
    enabled_weight = sum(
        max(1, int(format_settings.get(format_id, {}).get("priority", 1)))
        for format_id in FORMAT_DEFINITIONS
        if format_settings.get(format_id, {}).get("enabled", True)
    )
    format_stats = []
    for format_id in FORMAT_DEFINITIONS:
        format_episodes = [episode for episode in active_episodes if format_id_for(episode) == format_id]
        enabled = format_settings.get(format_id, {}).get("enabled", True)
        priority = max(1, int(format_settings.get(format_id, {}).get("priority", 1)))
        format_stats.append(
            {
                "id": format_id,
                "label": format_label(format_id),
                "enabled": enabled,
                "priority": priority,
                "sharePct": round(priority / enabled_weight * 100, 1) if enabled and enabled_weight else 0,
                "targetStock": targets.get(format_id, 0),
                "total": len(format_episodes),
                "rendered": sum(
                    episode_video(episode).exists() and episode_video(episode).name in new_video_names
                    for episode in format_episodes
                ),
                "stock": sum(
                    episode_video(episode).exists()
                    and episode_video(episode).name in new_video_names
                    and episode["id"] not in publishing
                    for episode in format_episodes
                ),
                "review": sum(
                    episode_video(episode).exists()
                    and not episode.get("needs_review")
                    and not queue_by_id.get(episode["id"])
                    for episode in format_episodes
                ),
                "queued": sum(queue_by_id.get(episode["id"], {}).get("status") == "pending" for episode in format_episodes),
            }
        )
    return {
        "episodes": items,
        "legacyVideos": legacy_videos,
        "toGenerate": [item for item in items if not item["hasVideo"]],
        "formats": format_stats,
        "music": {
            "originals": [
                {"filename": path.name, "title": path.stem, "starts": original_starts(path.name)}
                for path in sorted((ROOT / "public/audio/music").glob("*"))
                if path.is_file() and path.suffix.lower() in MUSIC_EXTENSIONS
            ],
            "tracks": [
                {
                    **track,
                    "clips": [
                        {
                            **clip,
                            "audioUrl": f"/music/{track['id']}/{clip['id']}",
                            "templateLabel": format_label(clip["templateId"]),
                        }
                        for clip in track.get("clips", [])
                    ],
                }
                for track in load_library()["tracks"]
            ],
        },
        "job": job,
        "analytics": analytics_snapshot(),
        "publishing": {
            "config": config,
            "credentials": credential_status(config),
            "nextRunAt": load_schedule().get("nextRunAt"),
            "nextGenerationAt": load_generation_schedule().get("nextRunAt"),
            "lastError": max(failed, key=lambda item: item.get("updatedAt", "")) if failed else None,
            "tiktokAccount": tiktok_account(),
            "tiktokRedirectUri": TIKTOK_REDIRECT_URI,
            "youtubeRedirectUri": YOUTUBE_REDIRECT_URI,
        },
    }


def _terminate_process(process: subprocess.Popen | None, pid: int | None = None) -> None:
    target = process.pid if process else pid
    if not target:
        return
    try:
        os.killpg(target, signal.SIGTERM)
    except (AttributeError, ProcessLookupError, PermissionError):
        try:
            if process and process.poll() is None:
                process.terminate()
            else:
                os.kill(target, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            return
    if process:
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(target, signal.SIGKILL)
            except (AttributeError, ProcessLookupError, PermissionError):
                process.kill()


def cancel_active_job(lane: str | None = None) -> None:
    running = [name for name in ("generation", "publishing", "main") if read_job(name)["status"] == "running"]
    lane = lane or ("publishing" if "publishing" in running else running[0] if running else None)
    if not lane:
        raise RuntimeError("No hay una tarea en curso")
    with JOB_LOCK:
        job = read_job(lane)
        if job["status"] != "running":
            raise RuntimeError("No hay una tarea en curso")
        CANCEL_REQUESTED[lane] = True
        process = ACTIVE_PROCESSES.get(lane)
        pid = process.pid if process else job.get("pid") if job.get("pid") != os.getpid() else None
    _terminate_process(process, pid)
    append_job_line("Cancelación solicitada por el usuario", lane)
    finish_job("cancelled", -15, "Cancelada por el usuario.", lane)
    with JOB_LOCK:
        JOB.update({"status": "cancelled", "returnCode": -15})


def start_command(
    label: str,
    command: list[str],
    on_success=None,
    source: str = "manual",
    lane: str = "main",
) -> None:
    command = ["taskset", "-c", CPUSETS[lane], *command] if lane in CPUSETS else command
    log_path = LOG_DIR / "jobs" / f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{safe_name(label)}.log"
    with JOB_LOCK:
        if read_job(lane)["status"] == "running":
            raise RuntimeError("Ya hay una tarea en curso")
        ACTIVE_PROCESSES[lane] = None
        CANCEL_REQUESTED[lane] = False
        begin_job(label, source, str(log_path), lane)
        JOB.update({"status": "running", "label": label, "lines": [], "returnCode": None, "log": str(log_path)})

    def run() -> None:
        process = None
        try:
            append_log(log_path, f"started={datetime.now(timezone.utc).isoformat()}")
            append_log(log_path, "command=" + " ".join(command))
            process = subprocess.Popen(
                command,
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                start_new_session=True,
            )
            with JOB_LOCK:
                ACTIVE_PROCESSES[lane] = process
            set_job_pid(process.pid, lane)
            with JOB_LOCK:
                cancelled_before_start = CANCEL_REQUESTED.get(lane, False)
            if cancelled_before_start:
                _terminate_process(process)
            assert process.stdout
            for line in process.stdout:
                append_log(log_path, line)
                append_job_line(line.rstrip(), lane)
                with JOB_LOCK:
                    JOB["lines"].append(line.rstrip())
            code = process.wait()
            append_log(log_path, f"exit={code}")
            with JOB_LOCK:
                cancelled = CANCEL_REQUESTED.get(lane, False)
            if code == 0 and not cancelled and on_success:
                on_success()
            status = "cancelled" if cancelled else "completed" if code == 0 else "failed"
            finish_job(status, -15 if cancelled else code, "Cancelada por el usuario." if cancelled else None, lane)
            with JOB_LOCK:
                JOB.update({"status": status, "returnCode": -15 if cancelled else code})
        except Exception as error:
            append_log(log_path, f"error={error}")
            with JOB_LOCK:
                cancelled = CANCEL_REQUESTED.get(lane, False)
            finish_job("cancelled" if cancelled else "failed", -15 if cancelled else 1, "Cancelada por el usuario." if cancelled else str(error), lane)
            with JOB_LOCK:
                JOB.update({"status": "cancelled" if cancelled else "failed", "lines": [*JOB["lines"], "Cancelada por el usuario." if cancelled else str(error)], "returnCode": -15 if cancelled else 1})
        finally:
            with JOB_LOCK:
                if ACTIVE_PROCESSES.get(lane) is process:
                    ACTIVE_PROCESSES[lane] = None
                CANCEL_REQUESTED[lane] = False

    threading.Thread(target=run, daemon=True).start()


def start_job(
    episode_id: str | None,
    format_id: str | None = None,
    *,
    force_audio: bool = False,
    force_render: bool = False,
) -> None:
    config = load_config()
    if episode_id and not format_id:
        episode = next((item for item in all_episodes() if item["id"] == episode_id), None)
        format_id = format_id_for(episode) if episode else None
    if not format_id or format_id == "all":
        format_id = choose_weighted_format(config["generation"].get("formats", {}))
    command = [
        sys.executable,
        "-u",
        str(ROOT / "scripts/produce_quiz_copy.py"),
        "--render",
        "--generate-audio",
    ]
    if episode_id:
        command.extend(["--episode", episode_id])
    if force_audio:
        command.extend(["--generate-audio", "--force-audio"])
    if force_render:
        command.append("--force-render")
    start_command(
        f"Generando {episode_id}" if episode_id else f"Generando {format_label(format_id)}",
        command,
        lane="generation",
    )


def start_publish_job() -> None:
    if not pending_queue_ids():
        raise RuntimeError("No hay videos aprobados en cola")

    def reschedule() -> None:
        config = load_config()
        save_schedule(next_run_iso(config["schedule"]["intervalMinutes"]))

    start_command(
        "Publicando próximo video",
        [sys.executable, "-u", str(ROOT / "scripts/publish.py"), "--queue", "--limit", "1"],
        reschedule,
        lane="publishing",
    )


def start_platform_publish(episode_id: str, platform: str) -> None:
    if platform not in PUBLISHERS:
        raise ValueError("Plataforma inválida")
    if not credential_status(load_config())[platform]:
        raise RuntimeError(f"Faltan datos para publicar en {platform}")
    start_command(
        f"Publicando {episode_id} en {platform}",
        [sys.executable, "-u", str(ROOT / "scripts/publish.py"), "--episode", episode_id, "--platform", platform],
        lane="publishing",
    )


def start_backup_job() -> None:
    start_command("Backup de estado", [sys.executable, "-u", str(ROOT / "scripts/backup_state.py")])


def start_context_snapshot_job() -> None:
    start_command("Snapshot para Codex", [sys.executable, "-u", str(ROOT / "scripts/context_snapshot.py")])


def start_music_import(payload: dict) -> None:
    if not payload.get("rightsConfirmed"):
        raise ValueError("Confirma que tenes permiso para reutilizar este audio")
    templates = payload.get("templateIds")
    starts = payload.get("starts")
    if not isinstance(templates, list) or not isinstance(starts, list):
        raise ValueError("Selecciona plantilla y momentos")
    url = validate_youtube_url(str(payload.get("url", "")))
    templates = validate_templates(list(map(str, templates)))
    starts = [str(value) for value in validate_starts(list(map(str, starts)))]
    command = [
        sys.executable, "-u", str(ROOT / "scripts/music_library.py"), "import",
        "--url", url, "--templates", *templates, "--starts", *starts, "--rights-confirmed",
    ]
    start_command("Importando musica", command, source="music")


def start_analytics_sync() -> None:
    if ANALYTICS_API_URL:
        status, result = analytics_request("/api/analytics/sync", method="POST")
        if status not in {HTTPStatus.OK, HTTPStatus.ACCEPTED}:
            raise RuntimeError(result.get("error", "El servicio de analytics rechazó la sincronización"))
        return
    if not ANALYTICS_LOCK.acquire(blocking=False):
        raise RuntimeError("Las estadísticas ya se están actualizando")

    def run() -> None:
        try:
            sync_all()
        finally:
            ANALYTICS_LOCK.release()

    threading.Thread(target=run, daemon=True).start()


def analytics_scheduler() -> None:
    while True:
        start_analytics_sync()
        time.sleep(6 * 60 * 60)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        line = f"Dashboard: {format % args}"
        print(line, flush=True)
        append_log(LOG_DIR / "dashboard.log", f"{datetime.now(timezone.utc).isoformat()} {line}")

    def send_json(self, value: dict, status: int = 200) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", location)
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/tiktok/connect":
            try:
                self.redirect(tiktok_connect_url())
            except RuntimeError as error:
                self.redirect("/?" + urlencode({"tiktok": "error", "message": str(error)}))
        elif path.rstrip("/") == "/api/tiktok/callback":
            try:
                complete_tiktok_login(parse_qs(urlparse(self.path).query))
                self.redirect("/?tiktok=connected")
            except (KeyError, RuntimeError) as error:
                self.redirect("/?" + urlencode({"tiktok": "error", "message": str(error)}))
        elif path == "/api/youtube/connect":
            try:
                self.redirect(youtube_connect_url())
            except RuntimeError as error:
                self.redirect("/?" + urlencode({"youtube": "error", "message": str(error)}))
        elif path.rstrip("/") == "/api/youtube/callback":
            try:
                complete_youtube_login(parse_qs(urlparse(self.path).query))
                self.redirect("/?youtube=connected")
            except (KeyError, RuntimeError) as error:
                self.redirect("/?" + urlencode({"youtube": "error", "message": str(error)}))
        elif path == "/":
            body = INDEX_PATH.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/health":
            self.send_json({"ok": True, "service": "dashboard"})
        elif path == "/api/state":
            self.send_json(dashboard_state())
        elif path == "/api/clues":
            if not os.getenv("CLUES_API_URL"):
                self.send_json({"ok": False, "error": "La API de pistas no está configurada"}, HTTPStatus.SERVICE_UNAVAILABLE)
            else:
                try:
                    status, result = clues_request(f"/api/clues?{urlparse(self.path).query}" if urlparse(self.path).query else "/api/clues")
                    self.send_json(result, status)
                except CluesApiError:
                    self.send_json({"ok": False, "error": "La API de pistas no responde"}, HTTPStatus.BAD_GATEWAY)
        elif path == "/api/diagnostics":
            self.send_json(diagnostics_state())
        elif path.startswith("/api/monitor/"):
            if not MONITOR_API_URL:
                self.send_json({"ok": False, "error": "El servicio de monitoreo no está configurado"}, HTTPStatus.SERVICE_UNAVAILABLE)
            else:
                try:
                    target = path + (f"?{urlparse(self.path).query}" if urlparse(self.path).query else "")
                    status, result = monitor_request(target)
                    self.send_json(result, status)
                except MonitorApiError:
                    self.send_json({"ok": False, "error": "El servicio de monitoreo no responde"}, HTTPStatus.BAD_GATEWAY)
        elif path == "/api/analytics/export.json":
            if ANALYTICS_API_URL:
                status, result = analytics_request("/api/analytics/export.json")
                self.send_json(result, status)
            else:
                self.send_json(write_exports())
        elif path == "/api/analytics/export.md":
            if ANALYTICS_API_URL:
                status, body = analytics_text("/api/analytics/export.md")
                body = body.encode("utf-8")
            else:
                write_exports()
                status, body = HTTPStatus.OK, (ROOT / "out/analytics/gpt-analytics.md").read_bytes()
            self.send_response(status)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path.startswith("/videos/") or path.startswith("/legacy-videos/"):
            legacy = path.startswith("/legacy-videos/")
            prefix = "/legacy-videos/" if legacy else "/videos/"
            filename = unquote(path.removeprefix(prefix))
            directory = LEGACY_OUTPUT_DIR if legacy else OUTPUT_DIR
            video = directory / filename
            if video.parent != directory or not video.is_file() or video.suffix.lower() != ".mp4":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(video.stat().st_size))
            self.end_headers()
            with video.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    self.wfile.write(chunk)
        elif path.startswith("/thumbnails/"):
            filename = unquote(path.removeprefix("/thumbnails/"))
            image = (THUMBNAIL_DIR / filename).resolve()
            if THUMBNAIL_DIR.resolve() not in image.parents or not image.is_file() or image.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(image.stat().st_size))
            self.end_headers()
            self.wfile.write(image.read_bytes())
        elif path.startswith("/audio/"):
            filename = unquote(path.removeprefix("/audio/"))
            audio = (ROOT / "public" / "audio" / filename).resolve()
            public_audio = (ROOT / "public" / "audio").resolve()
            if public_audio not in audio.parents or not audio.is_file() or audio.suffix.lower() not in {".mp3", ".wav", ".m4a", ".ogg"}:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", {".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4", ".ogg": "audio/ogg"}[audio.suffix.lower()])
            self.send_header("Content-Length", str(audio.stat().st_size))
            self.end_headers()
            with audio.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    self.wfile.write(chunk)
        elif path.startswith("/music/"):
            parts = path.removeprefix("/music/").split("/")
            library = load_library()
            track = next((item for item in library["tracks"] if item.get("id") == parts[0]), None) if len(parts) == 2 else None
            clip = next((item for item in track.get("clips", []) if item.get("id") == parts[1]), None) if track else None
            audio = (ROOT / "public" / clip["publicSrc"]).resolve() if clip else None
            public_root = (ROOT / "public").resolve()
            if not audio or public_root not in audio.parents or not audio.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "audio/mp4")
            self.send_header("Content-Length", str(audio.stat().st_size))
            self.end_headers()
            self.wfile.write(audio.read_bytes())
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        try:
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size) or b"{}")
            path = urlparse(self.path).path
            if path == "/api/job/cancel":
                cancel_active_job(payload.get("lane"))
            elif path == "/api/generate":
                start_job(payload.get("episodeId"), payload.get("formatId"))
            elif path == "/api/publishing/config":
                config = save_config(payload.get("config"))
                if config["schedule"]["enabled"]:
                    next_run = payload.get("nextRunAt") or load_schedule().get("nextRunAt")
                    save_schedule(next_run or datetime.now(timezone.utc).isoformat())
                else:
                    save_schedule(None)
                if config["generation"]["enabled"]:
                    next_generation = load_generation_schedule().get("nextRunAt")
                    save_generation_schedule(next_generation or datetime.now(timezone.utc).isoformat())
                else:
                    save_generation_schedule(None)
            elif path == "/api/publishing/secrets":
                save_secrets(payload)
            elif path == "/api/tiktok/disconnect":
                disconnect_tiktok()
            elif path == "/api/analytics/sync":
                start_analytics_sync()
            elif path in {"/api/monitor/check", "/api/monitor/events"}:
                if not MONITOR_API_URL:
                    raise RuntimeError("El servicio de monitoreo no está configurado")
                status, result = monitor_request(path, method="POST", payload=payload)
                self.send_json(result, status)
                return
            elif path == "/api/publish-now":
                start_publish_job()
            elif path == "/api/publish-platform":
                start_platform_publish(payload["episodeId"], payload["platform"])
            elif path == "/api/backup":
                start_backup_job()
            elif path == "/api/context-snapshot":
                start_context_snapshot_job()
            elif path == "/api/music/import":
                start_music_import(payload)
            elif path == "/api/music/delete":
                if read_job()["status"] == "running":
                    raise RuntimeError("Espera a que termine la tarea activa")
                delete_track(payload["trackId"])
            elif path == "/api/music/original-starts":
                starts = payload.get("starts")
                if not isinstance(starts, list):
                    raise ValueError("Carga uno o varios momentos")
                set_original_starts(str(payload.get("filename", "")), list(map(str, starts)))
            elif path == "/api/action":
                episode_id = payload["episodeId"]
                action = payload["action"]
                if action == "approve":
                    queue_episode(episode_id)
                elif action == "unqueue":
                    if not any(item["episodeId"] == episode_id for item in queue_items()):
                        raise RuntimeError(f"{episode_id} no está en la cola")
                    remove_queue_item(episode_id)
                elif action == "reject":
                    reject_episode(episode_id)
                elif action == "hints":
                    pend_hints(episode_id)
                elif action == "clear-hints":
                    clear_hints(episode_id)
                elif action == "audio":
                    start_job(episode_id, force_audio=True, force_render=True)
                elif action == "video":
                    start_job(episode_id, force_render=True)
                else:
                    raise ValueError("Acción inválida")
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json({"ok": True})
        except MonitorApiError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_GATEWAY)
        except (KeyError, ValueError, RuntimeError) as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.CONFLICT)
        except Exception as error:
            append_log(LOG_DIR / "dashboard.log", f"{datetime.now(timezone.utc).isoformat()} Dashboard error: {error}")
            print(f"Dashboard error: {error}", file=sys.stderr, flush=True)
            self.send_json({"ok": False, "error": "No se pudo completar la operación"}, HTTPStatus.INTERNAL_SERVER_ERROR)


def main() -> None:
    port = int(os.getenv("DASHBOARD_PORT", "8787"))
    if not ANALYTICS_API_URL:
        write_exports()
        threading.Thread(target=analytics_scheduler, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Dashboard activo en el puerto {port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
