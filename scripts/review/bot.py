#!/usr/bin/env python3
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from job_status import read_job
from publishing.common import json_request, sha256
from publishing.settings import apply_runtime, load_generation_schedule, load_schedule
from review.storage import clear_hints, pend_hints, pending_hints_items, publishing_state
from review.storage import queue_episode, queue_items, reject_episode, remove_queue_item
from review.telegram import answer_callback, get_updates, send_for_review, send_message
from video_formats import all_episodes, video_path

ROOT = Path(__file__).resolve().parents[2]
OFFSET_PATH = ROOT / "out/telegram-offset.txt"
LOG_PATH = ROOT / "out/logs/bot.log"
ALERT_STATE_PATH = ROOT / "out/telegram-alert-state.json"
DASHBOARD_URL = os.getenv("DASHBOARD_INTERNAL_URL", "http://dashboard:8787").rstrip("/")
ERROR_RE = re.compile(
    r"(traceback|exception|error|failed|fall[oó]|interrumpid|no se pudo|"
    r"faltan assets|browser crashed|exit\s*[:=]\s*(?!0)\d+)",
    re.IGNORECASE,
)
MONITORED_LOGS = (
    ROOT / "out/logs/generator.log",
    ROOT / "out/logs/publisher.log",
    ROOT / "out/logs/publisher-worker.log",
    ROOT / "out/logs/dashboard.log",
)
MONITOR_STARTED = time.time()\nTELEGRAM_RETRY_INITIAL_SECONDS = 5\nTELEGRAM_RETRY_MAX_SECONDS = 60


def log(text: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now(timezone.utc).isoformat()} {text}"
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8", errors="replace") as file:
        file.write(line + "\n")


def authorized(chat_id: int | str) -> bool:
    expected = os.getenv("TELEGRAM_REVIEW_CHAT_ID")
    return bool(expected and str(chat_id) == expected)


def tell(chat_id: int | str, text: str, keyboard: list | None = None) -> None:
    text = text or "—"
    pieces = [text[index:index + 3500] for index in range(0, len(text), 3500)] or ["—"]
    for index, piece in enumerate(pieces):
        send_message(chat_id, piece, keyboard if index == len(pieces) - 1 else None)


def dashboard_post(path: str, payload: dict | None = None) -> dict:
    result, _ = json_request(f"{DASHBOARD_URL}{path}", method="POST", payload=payload or {})
    if result.get("ok") is False:
        raise RuntimeError(result.get("error") or "El dashboard rechazó la operación")
    return result


def dashboard_action(episode_id: str, action: str) -> None:
    dashboard_post("/api/action", {"episodeId": episode_id, "action": action})


def episode_map() -> dict[str, dict]:
    return {episode["id"]: episode for episode in all_episodes()}


def production_status() -> str:
    job = read_job()
    queue = [item for item in queue_items() if item.get("status") == "pending"]
    lines = [
        "📊 ESTADO DE PRODUCCIÓN",
        f"Trabajo: {job.get('status', 'idle')} · {job.get('label') or 'sin tarea'}",
    ]
    if job.get("status") == "running":
        progress = next(
            (line for line in reversed(job.get("lines", [])) if re.search(r"Rendered \d+/\d+|Bundling \d+%", line)),
            None,
        )
        if progress:
            lines.append(f"Progreso: {progress}")
        lines.append(f"Iniciado: {job.get('startedAt') or '—'}")
    elif job.get("status") == "failed":
        lines.append(f"Último error: {job.get('lines', ['—'])[-1]}")
    lines.extend(
        [
            f"Próxima generación: {load_generation_schedule().get('nextRunAt') or 'sin programar'}",
            f"Próxima publicación: {load_schedule().get('nextRunAt') or 'sin programar'}",
            f"Cola de publicación: {len(queue)}",
            f"Pistas para revisar: {len(pending_hints_items())}",
        ]
    )
    return "\n".join(lines)


def is_currently_published(published: dict, episode_id: str, video: Path) -> bool:
    record = published.get(episode_id, {})
    return bool(record.get("platforms")) and record.get("sha256") == sha256(video)


def available_text() -> tuple[str, list]:
    episodes = episode_map()
    queue = {item["episodeId"]: item for item in queue_items()}
    published = publishing_state().get("videos", {})
    missing = []
    ready = []
    for episode_id, episode in episodes.items():
        has_video = video_path(episode, ROOT).exists()
        item = (episode_id, episode["target"]["display_name"], episode["target"]["kind"])
        if not has_video:
            missing.append(item)
        elif not is_currently_published(published, episode_id, video_path(episode, ROOT)) and queue.get(episode_id, {}).get("status") != "pending":
            ready.append(item)
    lines = ["🎬 VIDEOS DISPONIBLES PARA GENERAR"]
    lines.extend(f"• {episode_id} · {target} · {kind}" for episode_id, target, kind in missing)
    if not missing:
        lines.append("No hay videos pendientes de generar.")
    if ready:
        lines.append("\n✅ Videos generados sin publicar:")
        lines.extend(f"• {episode_id} · {target}" for episode_id, target, _ in ready)
    keyboard = [[{"text": f"▶️ Generar {episode_id}", "callback_data": f"generate:{episode_id}"}] for episode_id, *_ in missing[:20]]
    return "\n".join(lines), keyboard


def approval_items() -> list[dict]:
    episodes = episode_map()
    queue = {item["episodeId"]: item for item in queue_items()}
    published = publishing_state().get("videos", {})
    sent = read_alert_state().get("sentForReview", {})
    items = []
    for episode_id, episode in episodes.items():
        video = video_path(episode, ROOT)
        if (
            not video.is_file()
            or queue.get(episode_id, {}).get("status") == "pending"
            or is_currently_published(published, episode_id, video)
        ):
            continue
        fingerprint = sha256(video)
        items.append({
            "id": episode_id,
            "target": episode["target"]["display_name"],
            "video": video,
            "sent": sent.get(episode_id) == fingerprint,
        })
    return items


def approvals_text() -> tuple[str, list]:
    items = approval_items()
    lines = ["✅ VIDEOS POR APROBAR"]
    if not items:
        return "\n".join(lines + ["No hay videos nuevos pendientes de aprobación."]), menu_keyboard()
    keyboard = []
    for item in items[:20]:
        sent_label = "📨 Ya enviado" if item["sent"] else "📹 Enviar video"
        row = [{"text": f"✅ Aprobar {item['id']}", "callback_data": f"accept:{item['id']}"}]
        if not item["sent"]:
            row.append({"text": sent_label, "callback_data": f"sendvideo:{item['id']}"})
        keyboard.append(row)
        lines.append(f"• {item['id']} · {item['target']} · {sent_label}")
    return "\n".join(lines), keyboard


def send_review_video(episode_id: str) -> bool:
    item = next((item for item in approval_items() if item["id"] == episode_id), None)
    if not item:
        raise RuntimeError(f"{episode_id} no está disponible para aprobación")
    if item["sent"]:
        return False
    send_for_review(episode_id, item["target"], item["video"])
    state = read_alert_state()
    state.setdefault("sentForReview", {})[episode_id] = sha256(item["video"])
    write_alert_state(state)
    return True


def queue_text() -> tuple[str, list]:
    items = queue_items()
    if not items:
        return "📤 COLA DE PUBLICACIÓN\nEstá vacía.", []
    lines = ["📤 COLA DE PUBLICACIÓN"]
    keyboard = []
    for item in items:
        episode_id = item.get("episodeId", "?")
        lines.append(f"• {episode_id} · {item.get('status', '—')} · {item.get('updatedAt', '')}")
        if item.get("status") == "pending":
            keyboard.append([{"text": f"✖️ Sacar {episode_id}", "callback_data": f"unqueue:{episode_id}"}])
    return "\n".join(lines), keyboard


def published_text() -> str:
    episodes = episode_map()
    rows = []
    for episode_id, record in publishing_state().get("videos", {}).items():
        platforms = record.get("platforms", {})
        dates = [item.get("publishedAt", "") for item in platforms.values() if item.get("publishedAt")]
        target = episodes.get(episode_id, {}).get("target", {}).get("display_name", "—")
        links = [f"{name}: {item.get('url') or item.get('id')}" for name, item in platforms.items()]
        rows.append((max(dates, default=""), episode_id, target, links))
    rows.sort(reverse=True)
    lines = ["📚 HISTORIAL DE PUBLICACIONES"]
    if not rows:
        return "\n".join(lines + ["No hay publicaciones registradas."])
    for latest, episode_id, target, links in rows[:15]:
        lines.append(f"• {episode_id} · {target} · {latest or 'fecha no registrada'}")
        lines.extend(f"  {link}" for link in links)
    return "\n".join(lines)


def recent_errors() -> str:
    paths = [path for path in MONITORED_LOGS if path.exists()]
    if (ROOT / "out/logs/jobs").exists():
        paths.extend(sorted((ROOT / "out/logs/jobs").glob("*.log")))
    excerpts = []
    for path in sorted(paths, key=lambda item: item.stat().st_mtime, reverse=True):
        text = path.read_text(encoding="utf-8", errors="replace")
        matches = [line for line in text.splitlines() if ERROR_RE.search(line)]
        if matches:
            excerpts.append(f"--- {path.relative_to(ROOT)}\n" + "\n".join(matches[-12:]))
        if len(excerpts) >= 3:
            break
    return "⚠️ ÚLTIMOS ERRORES\n" + ("\n".join(excerpts) if excerpts else "No encontré errores recientes.")


def menu_keyboard() -> list:
    return [
        [{"text": "📊 Estado", "callback_data": "status"}, {"text": "🎬 Disponibles", "callback_data": "available"}],
        [{"text": "✅ Por aprobar", "callback_data": "approvals"}, {"text": "📚 Publicados", "callback_data": "published"}],
        [{"text": "📤 Cola", "callback_data": "queue"}, {"text": "⏹ Cancelar", "callback_data": "canceljob"}],
        [{"text": "▶️ Generar", "callback_data": "available"}, {"text": "🚀 Publicar próximo", "callback_data": "publishnow"}],
        [{"text": "⚠️ Errores", "callback_data": "errors"}],
    ]


def help_text() -> str:
    return """🤖 CONTROL DEL PROYECTO

/estado · producción, cola, horarios y tarea activa
/disponibles · videos pendientes de generar
/por_aprobar · videos generados pendientes de aprobación
/generar mc-11 · iniciar un video manualmente
/publicados · historial de publicaciones
/cola · cola de publicación
/publicar · publicar el próximo aprobado
/cancelar · cancelar la tarea activa
/aprobar mc-11 · poner un video generado en la cola
/sacar mc-11 · sacar un video de la cola
/regenerar mc-11 audio|video · regenerar
/pistas mc-11 · marcar pistas para revisar
/limpiar_pistas mc-11 · quitar esa marca
/errores · últimos errores
/menu · botones de control"""


def start_generation(chat_id: int | str, episode_id: str) -> None:
    if episode_id not in episode_map():
        raise RuntimeError(f"No existe {episode_id}")
    dashboard_action(episode_id, "audio")
    tell(chat_id, f"⏳ Inicié la generación completa de {episode_id}.\nTe aviso cuando termine o si aparece un error.")


def handle_callback(callback: dict) -> None:
    callback_id = callback["id"]
    chat_id = callback["message"]["chat"]["id"]
    if not authorized(chat_id):
        answer_callback(callback_id, "No autorizado")
        return
    action, _, value = callback.get("data", "").partition(":")
    try:
        answer_callback(callback_id)
        if action == "status":
            tell(chat_id, production_status(), menu_keyboard())
        elif action == "available":
            text, keyboard = available_text()
            tell(chat_id, text, keyboard)
        elif action == "approvals":
            text, keyboard = approvals_text()
            tell(chat_id, text, keyboard)
        elif action == "published":
            tell(chat_id, published_text(), menu_keyboard())
        elif action == "queue":
            text, keyboard = queue_text()
            tell(chat_id, text, keyboard)
        elif action == "errors":
            tell(chat_id, recent_errors(), menu_keyboard())
        elif action == "canceljob":
            dashboard_post("/api/job/cancel")
            tell(chat_id, "⏹ Cancelación solicitada.", menu_keyboard())
        elif action == "publishnow":
            dashboard_post("/api/publish-now")
            tell(chat_id, "🚀 Inicié la publicación del próximo video aprobado.", menu_keyboard())
        elif action == "generate":
            start_generation(chat_id, value)
        elif action == "accept":
            if not any(item["id"] == value for item in approval_items()):
                raise RuntimeError(f"{value} ya no está pendiente de aprobación")
            queue_episode(value)
            tell(chat_id, f"✅ {value} quedó en la cola de publicación.", menu_keyboard())
        elif action == "sendvideo":
            if send_review_video(value):
                tell(chat_id, f"📹 Envié {value} a Telegram para aprobarlo.", approvals_text()[1])
            else:
                tell(chat_id, f"📨 {value} ya había sido enviado a Telegram.", approvals_text()[1])
        elif action == "unqueue":
            remove_queue_item(value)
            tell(chat_id, f"✅ {value} salió de la cola.", menu_keyboard())
        elif action == "reject":
            tell(chat_id, f"¿Eliminar definitivamente {value}, incluyendo JSON, audio y video?", [[
                {"text": "Sí, eliminar", "callback_data": f"delete:{value}"},
                {"text": "Cancelar", "callback_data": "cancel"},
            ]])
        elif action == "delete":
            reject_episode(value)
            tell(chat_id, f"🗑 {value} fue eliminado completamente.", menu_keyboard())
        elif action == "regen":
            tell(chat_id, f"¿Qué querés regenerar en {value}?", [
                [{"text": "💡 Pistas", "callback_data": f"hints:{value}"}],
                [{"text": "🔊 Audio + video", "callback_data": f"audio:{value}"}],
                [{"text": "🎬 Solo video", "callback_data": f"video:{value}"}],
                [{"text": "Cancelar", "callback_data": "cancel"}],
            ])
        elif action == "hints":
            pend_hints(value)
            tell(chat_id, f"💡 {value} quedó marcado para revisar pistas.", menu_keyboard())
        elif action in {"audio", "video"}:
            dashboard_action(value, action)
            tell(chat_id, f"⏳ Regeneración {action} iniciada para {value}.")
        elif action == "cancel":
            tell(chat_id, "Operación cancelada.", menu_keyboard())
        else:
            raise RuntimeError("Acción desconocida")
    except Exception as error:
        log(f"error callback {action}:{value}: {error}")
        tell(chat_id, f"❌ Error: {error}\nUsá /errores para ver el log.", menu_keyboard())


def handle_message(message: dict) -> None:
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()
    parts = text.split()
    command = parts[0].split("@", 1)[0].lower() if parts else ""
    args = parts[1:]
    if not authorized(chat_id):
        if command == "/start":
            tell(chat_id, f"Chat ID: {chat_id}\nEste chat no está autorizado.")
        return
    try:
        if command in {"/start", "/menu"}:
            tell(chat_id, "🤖 Bot de control activo.", menu_keyboard())
        elif command in {"/ayuda", "/help"}:
            tell(chat_id, help_text(), menu_keyboard())
        elif command in {"/estado", "/produccion", "/status"}:
            tell(chat_id, production_status(), menu_keyboard())
        elif command in {"/disponibles", "/generables"}:
            text, keyboard = available_text()
            tell(chat_id, text, keyboard)
        elif command in {"/por_aprobar", "/aprobar_videos"}:
            text, keyboard = approvals_text()
            tell(chat_id, text, keyboard)
        elif command in {"/publicados", "/historial"}:
            tell(chat_id, published_text(), menu_keyboard())
        elif command == "/cola":
            text, keyboard = queue_text()
            tell(chat_id, text, keyboard)
        elif command in {"/generar", "/iniciar"}:
            if not args:
                text, keyboard = available_text()
                tell(chat_id, text, keyboard)
            else:
                start_generation(chat_id, args[0])
        elif command == "/cancelar":
            dashboard_post("/api/job/cancel")
            tell(chat_id, "⏹ Cancelación solicitada.", menu_keyboard())
        elif command == "/publicar":
            dashboard_post("/api/publish-now")
            tell(chat_id, "🚀 Inicié la publicación del próximo video aprobado.", menu_keyboard())
        elif command == "/aprobar":
            if not args:
                raise RuntimeError("Uso: /aprobar mc-11")
            if not any(item["id"] == args[0] for item in approval_items()):
                raise RuntimeError(f"{args[0]} no está pendiente de aprobación")
            queue_episode(args[0])
            tell(chat_id, f"✅ {args[0]} quedó en la cola de publicación.", menu_keyboard())
        elif command in {"/sacar", "/desaprobar"}:
            if not args:
                raise RuntimeError("Uso: /sacar mc-11")
            remove_queue_item(args[0])
            tell(chat_id, f"✅ {args[0]} salió de la cola.", menu_keyboard())
        elif command == "/pistas":
            if not args:
                raise RuntimeError("Uso: /pistas mc-11")
            pend_hints(args[0])
            tell(chat_id, f"💡 {args[0]} quedó marcado para revisar pistas.", menu_keyboard())
        elif command in {"/limpiar_pistas", "/pistas_ok"}:
            if not args:
                raise RuntimeError("Uso: /limpiar_pistas mc-11")
            clear_hints(args[0])
            tell(chat_id, f"✅ Se quitó la marca de pistas de {args[0]}.", menu_keyboard())
        elif command == "/regenerar":
            if len(args) < 2 or args[1].lower() not in {"audio", "video"}:
                raise RuntimeError("Uso: /regenerar mc-11 audio|video")
            dashboard_action(args[0], args[1].lower())
            tell(chat_id, f"⏳ Regeneración {args[1]} iniciada para {args[0]}.")
        elif command in {"/errores", "/logs"}:
            tell(chat_id, recent_errors(), menu_keyboard())
        else:
            tell(chat_id, "No reconozco ese comando.\n\n" + help_text(), menu_keyboard())
    except Exception as error:
        log(f"error message {text}: {error}")
        tell(chat_id, f"❌ {error}\nUsá /errores para ver el log.", menu_keyboard())


def read_alert_state() -> dict:
    try:
        return json.loads(ALERT_STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"initialized": False, "offsets": {}, "lastJob": None, "lastJobs": {}, "sentForReview": {}}


def write_alert_state(state: dict) -> None:
    ALERT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = ALERT_STATE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(ALERT_STATE_PATH)


def log_tail(path: Path, limit: int = 3000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[-limit:]
    except OSError as error:
        return f"No se pudo leer el log: {error}"


def notify_generation_done(job: dict, state: dict) -> None:
    label = job.get("label") or "generación"
    episode_match = re.search(r"\bmc-\d+\b", label)
    items = approval_items()
    target_ids = [episode_match.group(0)] if episode_match else [item["id"] for item in items if not item["sent"]]
    sent_ids = []
    for episode_id in target_ids:
        try:
            if send_review_video(episode_id):
                sent_ids.append(episode_id)
        except Exception as error:
            log(f"error enviando {episode_id} a aprobación: {error}")
    text, keyboard = approvals_text()
    prefix = f"✅ Terminó {label}."
    if sent_ids:
        prefix += "\n📹 Envié a Telegram: " + ", ".join(sent_ids)
    elif episode_match:
        prefix += f"\n📨 {episode_match.group(0)} ya estaba enviado o no quedó disponible."
    tell(os.environ["TELEGRAM_REVIEW_CHAT_ID"], prefix + "\n\n" + text, keyboard)


def monitor_errors() -> None:
    state = read_alert_state()
    paths = [path for path in MONITORED_LOGS if path.exists()]
    if (ROOT / "out/logs/jobs").exists():
        paths.extend(sorted((ROOT / "out/logs/jobs").glob("*.log")))
    jobs = {lane: read_job(lane) for lane in ("main", "generation", "publishing")}
    if not state.get("initialized"):
        state["offsets"] = {str(path): path.stat().st_size for path in paths}
        state["lastJob"] = None
        state["lastJobs"] = {
            lane: f"{job.get('status')}|{job.get('label')}|{job.get('startedAt')}"
            for lane, job in jobs.items()
        }
        state.setdefault("sentForReview", {})
        state["initialized"] = True
        write_alert_state(state)
        return
    for path in paths:
        key = str(path)
        size = path.stat().st_size
        offsets = state.setdefault("offsets", {})
        offset = min(int(offsets.get(key, 0)), size)
        if key not in offsets and path.stat().st_mtime < MONITOR_STARTED:
            offset = size
        offsets[key] = size
        new_text = path.read_text(encoding="utf-8", errors="replace")[offset:]
        if not new_text:
            continue
        matches = [line for line in new_text.splitlines() if ERROR_RE.search(line)]
        if matches:
            tell(
                os.environ["TELEGRAM_REVIEW_CHAT_ID"],
                f"⚠️ ERROR DETECTADO\nArchivo: {path.relative_to(ROOT)}\n\n" + "\n".join(matches[-20:]),
            )
    last_jobs = state.setdefault("lastJobs", {})
    for lane, job in jobs.items():
        job_key = f"{job.get('status')}|{job.get('label')}|{job.get('startedAt')}"
        if job.get("status") in {"completed", "cancelled", "failed"} and job_key != last_jobs.get(lane):
            if job.get("status") == "failed":
                job_log = str(job.get("log") or "").replace("/app/", str(ROOT) + "/")
                path = Path(job_log) if job_log else ROOT / "out/logs/generator.log"
                message = f"❌ Tarea fallida: {job.get('label') or 'sin nombre'}\n\n{log_tail(path)}"
            elif job.get("status") == "cancelled":
                message = f"⏹ Tarea cancelada: {job.get('label') or 'sin nombre'}"
            else:
                message = f"✅ Tarea terminada: {job.get('label') or 'sin nombre'}"
                if lane == "generation":
                    notify_generation_done(job, state)
                    last_jobs[lane] = job_key
                    continue
            tell(os.environ["TELEGRAM_REVIEW_CHAT_ID"], message)
            last_jobs[lane] = job_key
        elif job.get("status") == "running" and job_key != last_jobs.get(lane):
            tell(os.environ["TELEGRAM_REVIEW_CHAT_ID"], f"⏳ Tarea iniciada: {job.get('label') or 'sin nombre'}")
            last_jobs[lane] = job_key
    state["lastJob"] = last_jobs.get("main")
    write_alert_state(state)


def next_retry_delay(delay: float) -> float:
    return min(delay * 2, TELEGRAM_RETRY_MAX_SECONDS)


def notify_telegram_failure(error: Exception, state: dict[str, bool]) -> None:
    log(f"Bot: {error}")
    if state.get("outage"):
        return
    state["outage"] = True
    try:
        if os.getenv("TELEGRAM_REVIEW_CHAT_ID"):
            tell(os.environ["TELEGRAM_REVIEW_CHAT_ID"], f"⚠️ Error del bot:\n{error}")
    except Exception:
        pass


def notify_telegram_recovery(state: dict[str, bool]) -> None:
    if not state.get("outage"):
        return
    state["outage"] = False
    try:
        if os.getenv("TELEGRAM_REVIEW_CHAT_ID"):
            tell(os.environ["TELEGRAM_REVIEW_CHAT_ID"], "✅ Conexión con Telegram restaurada.")
    except Exception as error:
        log(f"Bot: no se pudo notificar la recuperación: {error}")


def main() -> None:
    apply_runtime()
    offset = int(OFFSET_PATH.read_text().strip()) if OFFSET_PATH.exists() else 0
    log("Bot de control iniciado")
    retry_delay = float(TELEGRAM_RETRY_INITIAL_SECONDS)
    telegram_state = {"outage": False}
    while True:
        try:
            updates = get_updates(offset)
        except Exception as error:
            notify_telegram_failure(error, telegram_state)
            time.sleep(retry_delay)
            retry_delay = next_retry_delay(retry_delay)
            continue

        notify_telegram_recovery(telegram_state)
        retry_delay = float(TELEGRAM_RETRY_INITIAL_SECONDS)
        try:
            for update in updates:
                offset = update["update_id"] + 1
                OFFSET_PATH.parent.mkdir(parents=True, exist_ok=True)
                OFFSET_PATH.write_text(str(offset), encoding="utf-8")
                if "callback_query" in update:
                    handle_callback(update["callback_query"])
                elif "message" in update:
                    handle_message(update["message"])
            monitor_errors()
        except Exception as error:
            log(f"Bot: {error}")
            try:
                if os.getenv("TELEGRAM_REVIEW_CHAT_ID"):
                    tell(os.environ["TELEGRAM_REVIEW_CHAT_ID"], f"⚠️ Error del bot:\n{error}")
            except Exception:
                pass
            time.sleep(5)


if __name__ == "__main__":
    main()
