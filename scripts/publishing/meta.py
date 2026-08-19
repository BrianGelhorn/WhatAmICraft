import os
import time
import urllib.parse

from .common import PublishRequest, env_bool, json_request, public_thumbnail_url, public_video_url, request, secret


def _graph(path: str) -> str:
    version = os.getenv("META_GRAPH_VERSION", "v26.0")
    return f"https://graph.facebook.com/{version}/{path.lstrip('/')}"


def _instagram_graph(path: str) -> str:
    version = os.getenv("INSTAGRAM_GRAPH_VERSION", "v26.0")
    return f"https://graph.instagram.com/{version}/{path.lstrip('/')}"


def publish_instagram(item: PublishRequest) -> dict:
    token = secret("INSTAGRAM_ACCESS_TOKEN")
    user_id = secret("INSTAGRAM_USER_ID")
    video_url = public_video_url(item.video)
    form = {
        "access_token": token,
        "media_type": "REELS",
        "video_url": video_url,
        "caption": item.description,
        "share_to_feed": str(env_bool("INSTAGRAM_SHARE_TO_FEED", True)).lower(),
    }
    if item.thumbnail and item.thumbnail.exists():
        form["cover_url"] = public_thumbnail_url(item.thumbnail)
    created, _ = json_request(
        _instagram_graph(f"{user_id}/media"),
        method="POST",
        form=form,
    )
    container_id = created["id"]
    deadline = time.monotonic() + int(os.getenv("META_PROCESS_TIMEOUT", "600"))
    while time.monotonic() < deadline:
        query = urllib.parse.urlencode({"fields": "status_code", "access_token": token})
        status, _ = json_request(f"{_instagram_graph(container_id)}?{query}")
        if status.get("status_code") == "FINISHED":
            break
        if status.get("status_code") in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Instagram no pudo procesar el reel: {status}")
        time.sleep(5)
    else:
        raise RuntimeError("Instagram no terminó de procesar el reel a tiempo")

    published, _ = json_request(
        _instagram_graph(f"{user_id}/media_publish"),
        method="POST",
        form={"access_token": token, "creation_id": container_id},
    )
    media_id = published["id"]
    return {"id": media_id, "containerId": container_id}


def publish_facebook(item: PublishRequest) -> dict:
    token = secret("META_ACCESS_TOKEN")
    page_id = secret("FACEBOOK_PAGE_ID")
    started, _ = json_request(
        _graph(f"{page_id}/video_reels"),
        method="POST",
        form={"access_token": token, "upload_phase": "start"},
    )
    video_id = started["video_id"]
    size = item.video.stat().st_size
    request(
        started["upload_url"],
        method="POST",
        headers={
            "Authorization": f"OAuth {token}",
            "offset": "0",
            "file_size": str(size),
            "Content-Type": "application/octet-stream",
            "Content-Length": str(size),
        },
        data=item.video.read_bytes(),
    )
    json_request(
        _graph(f"{page_id}/video_reels"),
        method="POST",
        form={
            "access_token": token,
            "upload_phase": "finish",
            "video_id": video_id,
            "title": item.title,
            "description": item.description,
            "video_state": os.getenv("FACEBOOK_VIDEO_STATE", "PUBLISHED"),
        },
    )
    return {"id": video_id, "url": f"https://www.facebook.com/reel/{video_id}"}
