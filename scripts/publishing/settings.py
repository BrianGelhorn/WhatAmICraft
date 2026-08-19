import copy
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import state_db
from video_formats import DEFAULT_FORMAT_SETTINGS, FORMAT_DEFINITIONS

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "data/publishing.json"
SECRETS_PATH = ROOT / "data/publishing-secrets.json"
SCHEDULE_PATH = ROOT / "out/publishing-schedule.json"
GENERATION_SCHEDULE_PATH = ROOT / "out/generation-schedule.json"
STATE_DB_PATH = ROOT / "out/app-state.sqlite3"
QUEUE_PATH = ROOT / "out/publishing-queue.json"
PUBLISHING_STATE_PATH = ROOT / "out/publishing-state.json"
HINTS_PENDING_PATH = ROOT / "data/pending-hint-regenerations.json"
STOCK_ALERT_PATH = ROOT / "out/stock-alert-state.json"

DEFAULT_CONFIG = {
    "title": "Can you guess this Minecraft {kind}?",
    "caption": "Can you guess it in less than 2 hints? Comment your answer before the reveal!",
    "hashtags": ["minecraft", "minecraftquiz", "gaming", "shorts"],
    "platforms": {
        "youtube": {"enabled": True, "privacyStatus": "private", "categoryId": "20"},
        "tiktok": {
            "enabled": True,
            "privacyLevel": "SELF_ONLY",
            "isAigc": True,
            "disableDuet": False,
            "disableComment": False,
            "disableStitch": False,
        },
        "instagram": {"enabled": True, "shareToFeed": True, "publicVideoBaseUrl": ""},
        "facebook": {"enabled": True, "videoState": "PUBLISHED"},
    },
    "schedule": {"enabled": False, "intervalMinutes": 1440},
    "generation": {
        "enabled": True,
        "intervalMinutes": 180,
        "targetStock": 8,
        "lowStockThreshold": 5,
        "publishGuardMinutes": 90,
        "formats": copy.deepcopy(DEFAULT_FORMAT_SETTINGS),
    },
}

SECRET_KEYS = {
    "YOUTUBE_CLIENT_ID",
    "YOUTUBE_CLIENT_SECRET",
    "YOUTUBE_REFRESH_TOKEN",
    "TIKTOK_ACCESS_TOKEN",
    "TIKTOK_REFRESH_TOKEN",
    "TIKTOK_ACCESS_EXPIRES_AT",
    "TIKTOK_CLIENT_KEY",
    "TIKTOK_CLIENT_SECRET",
    "TIKTOK_OPEN_ID",
    "TIKTOK_DISPLAY_NAME",
    "TIKTOK_AVATAR_URL",
    "INSTAGRAM_ACCESS_TOKEN",
    "META_ACCESS_TOKEN",
    "INSTAGRAM_USER_ID",
    "FACEBOOK_PAGE_ID",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_REVIEW_CHAT_ID",
}

REQUIREMENTS = {
    "youtube": {"YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"},
    "tiktok": {"TIKTOK_ACCESS_TOKEN"},
    "instagram": {"INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_USER_ID"},
    "facebook": {"META_ACCESS_TOKEN", "FACEBOOK_PAGE_ID"},
}


def _read(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else copy.deepcopy(default)


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def _ensure_state_db() -> None:
    state_db.migrate_json_state(
        db_path=STATE_DB_PATH,
        queue_path=QUEUE_PATH,
        publishing_state_path=PUBLISHING_STATE_PATH,
        pending_hints_path=HINTS_PENDING_PATH,
        publishing_schedule_path=SCHEDULE_PATH,
        generation_schedule_path=GENERATION_SCHEDULE_PATH,
        stock_alert_path=STOCK_ALERT_PATH,
    )


def load_config() -> dict:
    raw = _read(CONFIG_PATH, {})
    config = copy.deepcopy(DEFAULT_CONFIG)
    for key in ("title", "caption", "hashtags"):
        if key in raw:
            config[key] = raw[key]
    config["schedule"].update(raw.get("schedule", {}))
    config["generation"].update(raw.get("generation", {}))
    for format_id, defaults in DEFAULT_FORMAT_SETTINGS.items():
        config["generation"]["formats"].setdefault(format_id, copy.deepcopy(defaults))
        config["generation"]["formats"][format_id] = {
            **defaults,
            **config["generation"]["formats"][format_id],
        }
    for name in config["platforms"]:
        config["platforms"][name].update(raw.get("platforms", {}).get(name, {}))
        config["platforms"][name]["title"] = config["platforms"][name].get("title") or config["title"]
        config["platforms"][name]["caption"] = config["platforms"][name].get("caption") or config["caption"]
    if not config["platforms"]["instagram"]["publicVideoBaseUrl"] and os.getenv("PUBLIC_VIDEO_BASE_URL"):
        config["platforms"]["instagram"]["publicVideoBaseUrl"] = os.environ["PUBLIC_VIDEO_BASE_URL"].rstrip("/")
    return config


def validate_config(value: dict) -> dict:
    if not isinstance(value, dict):
        raise ValueError("Configuración inválida")
    config = load_config()
    title, caption = value.get("title"), value.get("caption")
    hashtags = value.get("hashtags")
    if not isinstance(title, str) or not title.strip() or len(title) > 100:
        raise ValueError("El título debe tener entre 1 y 100 caracteres")
    if not isinstance(caption, str) or not caption.strip() or len(caption) > 2200:
        raise ValueError("El texto debe tener entre 1 y 2200 caracteres")
    if not isinstance(hashtags, list) or not 1 <= len(hashtags) <= 30 or not all(isinstance(x, str) and x.strip() for x in hashtags):
        raise ValueError("Ingresá entre 1 y 30 hashtags")
    config.update({"title": title.strip(), "caption": caption.strip(), "hashtags": [x.strip().lstrip("#") for x in hashtags]})
    try:
        config["title"].format(kind="Weapon", episode_id="mc-01")
        config["caption"].format(kind="Weapon", episode_id="mc-01")
    except (KeyError, ValueError) as error:
        raise ValueError("El texto contiene una variable desconocida") from error

    incoming = value.get("platforms", {})
    if not isinstance(incoming, dict):
        raise ValueError("Plataformas inválidas")
    for name in config["platforms"]:
        platform = incoming.get(name, {})
        if not isinstance(platform, dict) or not isinstance(platform.get("enabled"), bool):
            raise ValueError(f"Configuración inválida para {name}")
        config["platforms"][name].update(platform)
        for field, maximum in (("title", 100), ("caption", 2200)):
            text = config["platforms"][name].get(field) or config[field]
            if not isinstance(text, str) or not text.strip() or len(text) > maximum:
                raise ValueError(f"El {field} de {name} debe tener entre 1 y {maximum} caracteres")
            try:
                text.format(kind="Weapon", episode_id="mc-01")
            except (KeyError, ValueError) as error:
                raise ValueError(f"El {field} de {name} contiene una variable desconocida") from error
            config["platforms"][name][field] = text.strip()

    boolean_options = [
        config["platforms"]["tiktok"][key]
        for key in ("isAigc", "disableDuet", "disableComment", "disableStitch")
    ] + [config["platforms"]["instagram"]["shareToFeed"]]
    if not all(isinstance(value, bool) for value in boolean_options):
        raise ValueError("Las opciones de publicación deben ser verdadero o falso")

    if config["platforms"]["youtube"]["privacyStatus"] not in {"private", "unlisted", "public"}:
        raise ValueError("Privacidad de YouTube inválida")
    if not str(config["platforms"]["youtube"]["categoryId"]).isdigit():
        raise ValueError("La categoría de YouTube debe ser numérica")
    if config["platforms"]["tiktok"]["privacyLevel"] not in {
        "SELF_ONLY", "FOLLOWER_OF_CREATOR", "MUTUAL_FOLLOW_FRIENDS", "PUBLIC_TO_EVERYONE"
    }:
        raise ValueError("Privacidad de TikTok inválida")
    if config["platforms"]["facebook"]["videoState"] not in {"PUBLISHED", "DRAFT"}:
        raise ValueError("Estado de Facebook inválido")
    public_url = str(config["platforms"]["instagram"].get("publicVideoBaseUrl", "")).strip()
    parsed_url = urlparse(public_url)
    if public_url and (parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc):
        raise ValueError("La URL pública debe comenzar con http:// o https://")
    config["platforms"]["instagram"]["publicVideoBaseUrl"] = public_url.rstrip("/")

    schedule = value.get("schedule", {})
    if not isinstance(schedule, dict) or not isinstance(schedule.get("enabled"), bool):
        raise ValueError("Programación inválida")
    try:
        interval = int(schedule.get("intervalMinutes"))
    except (TypeError, ValueError) as error:
        raise ValueError("La periodicidad debe ser numérica") from error
    if not 60 <= interval <= 10080:
        raise ValueError("La periodicidad debe estar entre 1 hora y 7 días")
    config["schedule"] = {"enabled": schedule["enabled"], "intervalMinutes": interval}
    if config["schedule"]["enabled"] and not any(x["enabled"] for x in config["platforms"].values()):
        raise ValueError("Activá al menos una plataforma")
    generation = value.get("generation", config["generation"])
    if not isinstance(generation, dict) or not isinstance(generation.get("enabled"), bool):
        raise ValueError("Generacion automatica invalida")
    try:
        generation_interval = int(generation.get("intervalMinutes"))
        target_stock = int(generation.get("targetStock"))
        low_stock = int(generation.get("lowStockThreshold"))
        guard = int(generation.get("publishGuardMinutes", 90))
    except (TypeError, ValueError) as error:
        raise ValueError("Los valores de generacion deben ser numericos") from error
    if not 60 <= generation_interval <= 10080:
        raise ValueError("La generacion debe repetirse entre 1 hora y 7 dias")
    if not 1 <= target_stock <= 50:
        raise ValueError("El stock objetivo debe estar entre 1 y 50 videos")
    if not 0 <= low_stock <= target_stock:
        raise ValueError("La alerta debe estar entre 0 y el stock objetivo")
    if not 30 <= guard <= 360:
        raise ValueError("El margen antes de publicar debe estar entre 30 minutos y 6 horas")
    format_settings = generation.get("formats", {})
    if not isinstance(format_settings, dict):
        raise ValueError("La configuración de formatos es inválida")
    normalized_formats = {}
    for format_id in FORMAT_DEFINITIONS:
        value = format_settings.get(format_id, DEFAULT_FORMAT_SETTINGS[format_id])
        if not isinstance(value, dict) or not isinstance(value.get("enabled"), bool):
            raise ValueError(f"Configuración inválida para {format_id}")
        try:
            priority = int(value.get("priority"))
        except (TypeError, ValueError) as error:
            raise ValueError(f"La prioridad de {format_id} debe ser numérica") from error
        if not 1 <= priority <= 10:
            raise ValueError("Las prioridades deben estar entre 1 y 10")
        normalized_formats[format_id] = {"enabled": value["enabled"], "priority": priority}
    if not any(value["enabled"] for value in normalized_formats.values()):
        raise ValueError("Activá al menos un formato")
    config["generation"] = {
        "enabled": generation["enabled"],
        "intervalMinutes": generation_interval,
        "targetStock": target_stock,
        "lowStockThreshold": low_stock,
        "publishGuardMinutes": guard,
        "formats": normalized_formats,
    }
    return config


def save_config(value: dict) -> dict:
    config = validate_config(value)
    _write(CONFIG_PATH, config)
    return config


def save_secrets(values: dict) -> None:
    if not isinstance(values, dict):
        raise ValueError("Credenciales inválidas")
    secrets = _read(SECRETS_PATH, {})
    for key, raw in values.items():
        if key not in SECRET_KEYS:
            raise ValueError(f"Credencial no permitida: {key}")
        value = str(raw).strip()
        if value:
            if len(value) > 4096:
                raise ValueError(f"{key} es demasiado largo")
            secrets[key] = value
            os.environ[key] = value
    _write(SECRETS_PATH, secrets)
    try:
        SECRETS_PATH.chmod(0o600)
    except OSError:
        pass


def stored_secrets() -> dict:
    saved = _read(SECRETS_PATH, {})
    return {key: os.getenv(key) or saved.get(key) for key in SECRET_KEYS}


def delete_secrets(keys: set[str]) -> None:
    secrets = _read(SECRETS_PATH, {})
    for key in keys:
        secrets.pop(key, None)
        os.environ.pop(key, None)
    _write(SECRETS_PATH, secrets)


def tiktok_account() -> dict:
    values = stored_secrets()
    return {
        "connected": bool(values.get("TIKTOK_ACCESS_TOKEN")),
        "displayName": values.get("TIKTOK_DISPLAY_NAME") or "",
        "avatarUrl": values.get("TIKTOK_AVATAR_URL") or "",
    }


def apply_runtime(config: dict | None = None) -> None:
    config = config or load_config()
    for key, value in _read(SECRETS_PATH, {}).items():
        if key in SECRET_KEYS and value and not os.getenv(key):
            os.environ[key] = str(value)
    youtube = config["platforms"]["youtube"]
    tiktok = config["platforms"]["tiktok"]
    instagram = config["platforms"]["instagram"]
    facebook = config["platforms"]["facebook"]
    options = {
        "YOUTUBE_PRIVACY_STATUS": youtube["privacyStatus"],
        "YOUTUBE_CATEGORY_ID": youtube["categoryId"],
        "TIKTOK_PRIVACY_LEVEL": tiktok["privacyLevel"],
        "TIKTOK_IS_AIGC": tiktok["isAigc"],
        "TIKTOK_DISABLE_DUET": tiktok["disableDuet"],
        "TIKTOK_DISABLE_COMMENT": tiktok["disableComment"],
        "TIKTOK_DISABLE_STITCH": tiktok["disableStitch"],
        "INSTAGRAM_SHARE_TO_FEED": instagram["shareToFeed"],
        "PUBLIC_VIDEO_BASE_URL": instagram["publicVideoBaseUrl"],
        "FACEBOOK_VIDEO_STATE": facebook["videoState"],
    }
    os.environ.update({
        key: str(value).lower() if isinstance(value, bool) else str(value)
        for key, value in options.items()
        if value != ""
    })


def credential_status(config: dict | None = None) -> dict:
    config = config or load_config()
    values = stored_secrets()
    result = {name: all(values.get(key) for key in keys) for name, keys in REQUIREMENTS.items()}
    result["instagram"] = result["instagram"] and bool(
        config["platforms"]["instagram"]["publicVideoBaseUrl"] or os.getenv("PUBLIC_VIDEO_BASE_URL")
    )
    return result


def enabled_platforms(config: dict) -> list[str]:
    return [name for name, value in config["platforms"].items() if value["enabled"]]


def load_schedule() -> dict:
    _ensure_state_db()
    return state_db.load_schedule("publishing", STATE_DB_PATH)


def save_schedule(next_run_at: str | None) -> None:
    if next_run_at:
        datetime.fromisoformat(next_run_at.replace("Z", "+00:00"))
    _ensure_state_db()
    state_db.save_schedule("publishing", next_run_at, STATE_DB_PATH)


def load_generation_schedule() -> dict:
    _ensure_state_db()
    return state_db.load_schedule("generation", STATE_DB_PATH)


def save_generation_schedule(next_run_at: str | None) -> None:
    if next_run_at:
        datetime.fromisoformat(next_run_at.replace("Z", "+00:00"))
    _ensure_state_db()
    state_db.save_schedule("generation", next_run_at, STATE_DB_PATH)


def next_run_iso(interval_minutes: int, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return (now + timedelta(minutes=interval_minutes)).astimezone(timezone.utc).isoformat()
