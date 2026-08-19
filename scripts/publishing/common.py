import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PublishRequest:
    episode_id: str
    video: Path
    thumbnail: Path | None
    title: str
    caption: str
    hashtags: list[str]

    @property
    def description(self) -> str:
        tags = " ".join(f"#{tag.lstrip('#')}" for tag in self.hashtags)
        return f"{self.caption}\n\n{tags}".strip()


def secret(name: str) -> str:
    value = os.getenv(name)
    secret_path = Path("/run/secrets") / name.lower()
    if not value and secret_path.exists():
        value = secret_path.read_text(encoding="utf-8").strip()
    if not value:
        raise RuntimeError(f"Falta la variable {name}")
    return value


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


def request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    timeout: int = 300,
) -> tuple[int, object, bytes]:
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, data=data, headers=headers or {}, method=method),
            timeout=timeout,
        ) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:2000]
        raise RuntimeError(f"La API respondió HTTP {error.code}: {detail}") from error


def json_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict | None = None,
    form: dict | None = None,
) -> tuple[dict, object]:
    request_headers = dict(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json; charset=UTF-8"
    elif form is not None:
        data = urllib.parse.urlencode(form).encode("utf-8")
        request_headers["Content-Type"] = "application/x-www-form-urlencoded"
    _, response_headers, body = request(url, method=method, headers=request_headers, data=data)
    result = json.loads(body or b"{}")
    api_error = result.get("error") if isinstance(result, dict) else None
    if isinstance(api_error, dict) and api_error.get("code") not in (None, "ok"):
        raise RuntimeError(f"La API rechazó la operación: {api_error}")
    if isinstance(api_error, str):
        raise RuntimeError(f"La API rechazó la operación: {api_error}")
    return result, response_headers


def public_video_url(video: Path) -> str:
    base = secret("PUBLIC_VIDEO_BASE_URL").rstrip("/")
    return f"{base}/videos/{urllib.parse.quote(video.name)}"


def public_thumbnail_url(thumbnail: Path) -> str:
    base = secret("PUBLIC_VIDEO_BASE_URL").rstrip("/")
    root = (Path(__file__).resolve().parents[2] / "out/thumbnails").resolve()
    relative = thumbnail.resolve().relative_to(root)
    return f"{base}/thumbnails/{urllib.parse.quote(relative.as_posix(), safe='/')}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
