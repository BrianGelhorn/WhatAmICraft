import base64
import json
import os
import shutil
import threading
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_LOCK = ROOT / "out/production.lock"


def load_env_local() -> None:
    path = ROOT / ".env.local"
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _api_key() -> str | None:
    secret = Path("/run/secrets/elevenlabs_api_key")
    return os.getenv("ELEVENLABS_API_KEY") or (secret.read_text(encoding="utf-8").strip() if secret.exists() else None)


def _voice_id() -> str:
    return os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def speech_with_timestamps(text: str, destination: Path, model: str, speed: float) -> dict:
    key = _api_key()
    if not key:
        raise RuntimeError("Falta ELEVENLABS_API_KEY")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{_voice_id()}/with-timestamps?output_format=mp3_44100_128"
    body = json.dumps({"text": text, "model_id": model, "voice_settings": {"speed": speed}}).encode()
    request = urllib.request.Request(
        url,
        data=body,
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.load(response)
    alignment = result.get("normalized_alignment") or result.get("alignment")
    if not alignment or not alignment.get("character_end_times_seconds"):
        raise RuntimeError("ElevenLabs no devolvió timestamps")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(base64.b64decode(result["audio_base64"]))
    return alignment


@contextmanager
def production_lock():
    # ponytail: active renders heartbeat every 30s; reclaim dead locks after 3 minutes.
    stale_seconds = int(os.getenv("PRODUCTION_LOCK_STALE_SECONDS", "180"))
    try:
        PRODUCTION_LOCK.mkdir(parents=True)
    except FileExistsError:
        age = time.time() - PRODUCTION_LOCK.stat().st_mtime
        if age <= stale_seconds:
            raise RuntimeError(f"Ya hay otra generación de video en curso ({int(age // 60)} min)")
        shutil.rmtree(PRODUCTION_LOCK)
        PRODUCTION_LOCK.mkdir()

    stop = threading.Event()

    def heartbeat() -> None:
        while not stop.wait(30):
            try:
                os.utime(PRODUCTION_LOCK)
            except FileNotFoundError:
                return

    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=1)
        shutil.rmtree(PRODUCTION_LOCK, ignore_errors=True)
