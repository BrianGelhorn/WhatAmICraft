import json
import os
import uuid
from pathlib import Path

from publishing.common import request


def configured() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_REVIEW_CHAT_ID"))


def _api(method: str, fields: dict, video: Path | None = None) -> dict:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN")
    headers: dict[str, str]
    if video:
        boundary = f"----MinecraftQuiz{uuid.uuid4().hex}"
        parts = []
        for name, value in fields.items():
            encoded = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list, bool)) else str(value)
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{encoded}\r\n".encode()
            )
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"video\"; filename=\"{video.name}\"\r\n"
            "Content-Type: video/mp4\r\n\r\n".encode()
        )
        body = b"".join(parts) + video.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    else:
        body = json.dumps(fields, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json; charset=UTF-8"}
    _, _, raw = request(
        f"https://api.telegram.org/bot{token}/{method}",
        method="POST",
        headers=headers,
        data=body,
        timeout=900 if video else 70,
    )
    result = json.loads(raw)
    if not result.get("ok"):
        raise RuntimeError(f"Telegram rechazó la operación: {result}")
    return result["result"]


def send_message(chat_id: str | int, text: str, keyboard: list | None = None) -> dict:
    fields = {"chat_id": chat_id, "text": text}
    if keyboard:
        fields["reply_markup"] = {"inline_keyboard": keyboard}
    return _api("sendMessage", fields)


def answer_callback(callback_id: str, text: str = "") -> None:
    _api("answerCallbackQuery", {"callback_query_id": callback_id, "text": text})


def get_updates(offset: int) -> list[dict]:
    return _api("getUpdates", {"offset": offset, "timeout": 50, "allowed_updates": ["message", "callback_query"]})


def send_for_review(episode_id: str, target: str, video: Path) -> dict:
    chat_id = os.getenv("TELEGRAM_REVIEW_CHAT_ID")
    if not chat_id:
        raise RuntimeError("Falta TELEGRAM_REVIEW_CHAT_ID")
    return _api(
        "sendVideo",
        {
            "chat_id": chat_id,
            "caption": f"{episode_id} · {target}\n¿Aprobamos este video?",
            "supports_streaming": True,
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {"text": "✅ Aceptar", "callback_data": f"accept:{episode_id}"},
                        {"text": "🔄 Regenerar", "callback_data": f"regen:{episode_id}"},
                    ],
                    [{"text": "🗑 Rechazar", "callback_data": f"reject:{episode_id}"}],
                ]
            },
        },
        video,
    )
