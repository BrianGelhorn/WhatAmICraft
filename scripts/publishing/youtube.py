import json
import os

from .common import PublishRequest, json_request, request, secret


def _access_token() -> str:
    token, _ = json_request(
        "https://oauth2.googleapis.com/token",
        method="POST",
        form={
            "client_id": secret("YOUTUBE_CLIENT_ID"),
            "client_secret": secret("YOUTUBE_CLIENT_SECRET"),
            "refresh_token": secret("YOUTUBE_REFRESH_TOKEN"),
            "grant_type": "refresh_token",
        },
    )
    return token["access_token"]


def publish(item: PublishRequest) -> dict:
    access_token = _access_token()
    size = item.video.stat().st_size
    metadata = {
        "snippet": {
            "title": item.title[:100],
            "description": item.description[:5000],
            "tags": item.hashtags,
            "categoryId": os.getenv("YOUTUBE_CATEGORY_ID", "20"),
        },
        "status": {"privacyStatus": os.getenv("YOUTUBE_PRIVACY_STATUS", "private")},
    }
    _, headers = json_request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Upload-Content-Length": str(size),
            "X-Upload-Content-Type": "video/mp4",
        },
        payload=metadata,
    )
    upload_url = headers.get("Location")
    if not upload_url:
        raise RuntimeError("YouTube no devolvió la URL de carga")
    _, _, body = request(
        upload_url,
        method="PUT",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "video/mp4",
            "Content-Length": str(size),
        },
        data=item.video.read_bytes(),
    )
    result = json.loads(body)
    video_id = result["id"]
    payload = {"id": video_id, "url": f"https://www.youtube.com/shorts/{video_id}"}
    if item.thumbnail and item.thumbnail.exists():
        try:
            request(
                f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}",
                method="POST",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "image/jpeg",
                    "Content-Length": str(item.thumbnail.stat().st_size),
                },
                data=item.thumbnail.read_bytes(),
            )
            payload["thumbnail"] = item.thumbnail.name
        except Exception as error:
            raise RuntimeError(f"YouTube miniatura: {error}") from error
    return payload
