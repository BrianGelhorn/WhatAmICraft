import os
import time

from .common import PublishRequest, env_bool, json_request, request, secret
from .settings import save_secrets, stored_secrets

API = "https://open.tiktokapis.com/v2/post/publish"


def _access_token() -> str:
    values = stored_secrets()
    token = values.get("TIKTOK_ACCESS_TOKEN")
    expires_at = int(values.get("TIKTOK_ACCESS_EXPIRES_AT") or 0)
    if token and (not expires_at or expires_at > time.time() + 300):
        return str(token)
    required = ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REFRESH_TOKEN")
    if not all(values.get(key) for key in required):
        return secret("TIKTOK_ACCESS_TOKEN")
    refreshed, _ = json_request(
        "https://open.tiktokapis.com/v2/oauth/token/",
        method="POST",
        form={
            "client_key": values["TIKTOK_CLIENT_KEY"],
            "client_secret": values["TIKTOK_CLIENT_SECRET"],
            "grant_type": "refresh_token",
            "refresh_token": values["TIKTOK_REFRESH_TOKEN"],
        },
    )
    save_secrets({
        "TIKTOK_ACCESS_TOKEN": refreshed["access_token"],
        "TIKTOK_REFRESH_TOKEN": refreshed["refresh_token"],
        "TIKTOK_ACCESS_EXPIRES_AT": str(int(time.time()) + int(refreshed["expires_in"])),
    })
    return refreshed["access_token"]


def _chunks(size: int) -> tuple[int, int]:
    if size <= 64 * 1024 * 1024:
        return size, 1
    chunk_size = 10 * 1024 * 1024
    return chunk_size, size // chunk_size


def publish(item: PublishRequest) -> dict:
    token = _access_token()
    auth = {"Authorization": f"Bearer {token}"}
    creator, _ = json_request(f"{API}/creator_info/query/", method="POST", headers=auth, payload={})
    privacy = os.getenv("TIKTOK_PRIVACY_LEVEL", "SELF_ONLY")
    allowed = creator["data"].get("privacy_level_options", [])
    if privacy not in allowed:
        raise RuntimeError(f"TikTok no permite {privacy}; opciones disponibles: {', '.join(allowed)}")

    size = item.video.stat().st_size
    chunk_size, chunk_count = _chunks(size)
    initialized, _ = json_request(
        f"{API}/video/init/",
        method="POST",
        headers=auth,
        payload={
            "post_info": {
                "title": item.description[:2200],
                "privacy_level": privacy,
                "disable_duet": env_bool("TIKTOK_DISABLE_DUET"),
                "disable_comment": env_bool("TIKTOK_DISABLE_COMMENT"),
                "disable_stitch": env_bool("TIKTOK_DISABLE_STITCH"),
                "is_aigc": env_bool("TIKTOK_IS_AIGC", True),
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": size,
                "chunk_size": chunk_size,
                "total_chunk_count": chunk_count,
            },
        },
    )
    upload_url = initialized["data"]["upload_url"]
    with item.video.open("rb") as source:
        start = 0
        for index in range(chunk_count):
            length = size - start if index == chunk_count - 1 else chunk_size
            body = source.read(length)
            request(
                upload_url,
                method="PUT",
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": str(len(body)),
                    "Content-Range": f"bytes {start}-{start + len(body) - 1}/{size}",
                },
                data=body,
            )
            start += len(body)
    publish_id = initialized["data"]["publish_id"]
    status, _ = json_request(
        f"{API}/status/fetch/",
        method="POST",
        headers=auth,
        payload={"publish_id": publish_id},
    )
    return {"id": publish_id, "status": status.get("data", {}).get("status", "PROCESSING")}
