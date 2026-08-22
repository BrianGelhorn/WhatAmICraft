import json
import os
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import state_db
from publishing.common import json_request
from publishing.settings import apply_runtime, credential_status, load_config, stored_secrets
from publishing.tiktok import _access_token as tiktok_access_token
from publishing.youtube import _access_token as youtube_access_token
from review.storage import publishing_state, save_published_platform, save_video_metrics, video_metric_snapshots, video_metrics
from template_artifacts import read_artifact
from video_formats import FORMAT_DEFINITIONS, all_episodes, format_id_for, format_label, video_path

ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "out/analytics"
PLATFORMS = ("youtube", "tiktok", "instagram", "facebook")


def _chunks(items: list, size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def _query(url: str, values: dict) -> str:
    return f"{url}?{urllib.parse.urlencode(values)}"


def _epoch(value: str | None) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()) if value else 0


def _safe_error(error: Exception) -> str:
    message = str(error)
    for secret in stored_secrets().values():
        if secret and len(secret) > 6:
            message = message.replace(str(secret), "***")
    lower = message.lower()
    if "invalid_grant" in lower or "token has been expired" in lower:
        return "La conexión venció; hay que volver a conectar la cuenta"
    if "insufficient" in lower or "permission" in lower or "oauth" in lower and "scope" in lower:
        return "La cuenta está conectada, pero falta autorizar el acceso a estadísticas"
    if "http 429" in lower or "rate limit" in lower:
        return "La plataforma limitó temporalmente las consultas; se reintentará en la próxima actualización"
    if "urlopen error" in lower or "connection" in lower or "conexión" in lower:
        return "No se pudo contactar a la plataforma"
    return message[:240]


def _published(platform: str, state: dict) -> list[tuple[str, dict, dict]]:
    rows = []
    for episode_id, record in state.items():
        payload = record.get("platforms", {}).get(platform)
        if payload and payload.get("id"):
            rows.append((episode_id, record, payload))
    return rows


def _build_series(snapshots: list[dict]) -> list[dict]:
    buckets = {}
    for snapshot in snapshots:
        captured = datetime.fromisoformat(snapshot["capturedAt"]).astimezone(timezone.utc)
        bucket = captured.replace(minute=0, second=0, microsecond=0).isoformat()
        key = (snapshot["platform"], bucket)
        point = buckets.setdefault(key, {
            "platform": snapshot["platform"], "capturedAt": bucket,
            "videos": 0, "views": 0, "engagements": 0, "reach": 0,
        })
        point["videos"] += 1
        point["views"] += int(snapshot.get("views") or 0)
        point["engagements"] += sum(int(snapshot.get(name) or 0) for name in ("likes", "comments", "shares", "saves"))
        point["reach"] += int(snapshot.get("reach") or 0)
    for point in buckets.values():
        point["engagementRateByViews"] = round(point["engagements"] / point["views"] * 100, 2) if point["views"] else None
    return sorted(buckets.values(), key=lambda point: (point["capturedAt"], point["platform"]))


def _creative_metadata(episode: dict | None, published_at: str | None) -> dict:
    if not episode:
        return {"targetKind": "unknown", "templateVersion": "unknown", "durationSeconds": None, "publishHourUtc": None}
    format_id = format_id_for(episode)
    artifact = read_artifact(video_path(episode))
    publish_hour = None
    if published_at:
        publish_hour = datetime.fromisoformat(published_at).astimezone(timezone.utc).hour
    return {
        "targetKind": episode.get("target", {}).get("kind", "unknown").replace("_", " ").title(),
        "templateVersion": artifact.get("templateVersion", "unknown") if artifact else "unknown",
        "durationSeconds": FORMAT_DEFINITIONS.get(format_id, {}).get("durationSeconds"),
        "publishHourUtc": publish_hour,
    }


def _build_cohorts(items: list[dict]) -> list[dict]:
    dimensions = ("formatLabel", "targetKind", "templateVersion", "publishHourUtc")
    groups = {}
    for item in items:
        for dimension in dimensions:
            value = item.get(dimension)
            if value is None:
                value = "unknown"
            value = f"{value:02d}:00 UTC" if dimension == "publishHourUtc" and isinstance(value, int) else str(value)
            key = (dimension, item["platform"], value)
            group = groups.setdefault(key, {
                "dimension": dimension, "platform": item["platform"], "value": value,
                "videos": 0, "measuredVideos": 0, "views": 0, "engagements": 0,
                "lifetimeViewsPerHour": [], "engagementRateByViews": [],
                "averageWatchSeconds": [], "completionRate": [],
            })
            group["videos"] += 1
            if item.get("views") is not None:
                group["measuredVideos"] += 1
                group["views"] += item["views"]
            group["engagements"] += item.get("engagements", 0)
            for field in ("lifetimeViewsPerHour", "engagementRateByViews", "averageWatchSeconds", "completionRate"):
                if item.get(field) is not None:
                    group[field].append(item[field])
    result = []
    for group in groups.values():
        measured = group.pop("measuredVideos")
        views = group["views"]
        for field in ("lifetimeViewsPerHour", "engagementRateByViews", "averageWatchSeconds", "completionRate"):
            values = group[field]
            group[field] = round(sum(values) / len(values), 2) if values else None
        group["viewsPerVideo"] = round(views / measured, 2) if measured else None
        group["engagementRateByViews"] = round(group["engagements"] / views * 100, 2) if views else None
        group["measuredVideos"] = measured
        result.append(group)
    return sorted(result, key=lambda group: (group["dimension"], group["platform"], -(group["viewsPerVideo"] or 0)))


def _insight_values(response: dict) -> dict:
    result = {}
    for metric in response.get("data", []):
        value = metric.get("total_value", {}).get("value")
        if value is None and metric.get("values"):
            value = metric["values"][-1].get("value")
        if isinstance(value, (int, float)):
            result[metric["name"]] = value
    return result


def sync_youtube(state: dict) -> int:
    rows = _published("youtube", state)
    if not rows:
        return 0
    token = youtube_access_token()
    auth = {"Authorization": f"Bearer {token}"}
    by_id = {str(payload["id"]): (episode_id, payload) for episode_id, _, payload in rows}
    videos = []
    for ids in _chunks(list(by_id), 50):
        response, _ = json_request(_query(
            "https://www.googleapis.com/youtube/v3/videos",
            {"part": "snippet,statistics,contentDetails", "id": ",".join(ids)},
        ), headers=auth)
        videos.extend(response.get("items", []))
    for video in videos:
        episode_id, payload = by_id[str(video["id"])]
        stats, snippet = video.get("statistics", {}), video.get("snippet", {})
        analytics = {}
        analytics_error = None
        try:
            start = (datetime.fromisoformat(payload["publishedAt"]).date() if payload.get("publishedAt") else date.today() - timedelta(days=3650)).isoformat()
            report, _ = json_request(_query(
                "https://youtubeanalytics.googleapis.com/v2/reports",
                {
                    "ids": "channel==MINE",
                    "startDate": start,
                    "endDate": date.today().isoformat(),
                    "metrics": "views,engagedViews,likes,comments,shares,estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
                    "filters": f"video=={video['id']}",
                },
            ), headers=auth)
            headers = [column["name"] for column in report.get("columnHeaders", [])]
            analytics = dict(zip(headers, report.get("rows", [[None] * len(headers)])[0])) if report.get("rows") else {}
        except Exception as error:
            analytics_error = _safe_error(error)
        save_video_metrics(episode_id, "youtube", {
            "id": video["id"],
            "title": snippet.get("title", ""),
            "share_url": payload.get("url", f"https://www.youtube.com/shorts/{video['id']}"),
            "create_time": _epoch(snippet.get("publishedAt")),
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "shares": int(analytics.get("shares", 0) or 0),
            "watchTimeSeconds": float(analytics["estimatedMinutesWatched"]) * 60 if analytics.get("estimatedMinutesWatched") is not None else None,
            "averageWatchSeconds": analytics.get("averageViewDuration"),
            "completionRate": analytics.get("averageViewPercentage"),
            "raw": {
                "dataApi": video, "analyticsApi": analytics, "analyticsError": analytics_error,
                "availableMetrics": [
                    "views", "likes", "comments",
                    *(["shares"] if "shares" in analytics else []),
                    *(["watchTimeSeconds"] if "estimatedMinutesWatched" in analytics else []),
                    *(["averageWatchSeconds"] if "averageViewDuration" in analytics else []),
                    *(["completionRate"] if "averageViewPercentage" in analytics else []),
                ],
            },
        })
    return len(videos)


def sync_tiktok(state: dict) -> int:
    rows = sorted(_published("tiktok", state), key=lambda row: row[2].get("publishedAt", ""), reverse=True)
    if not rows:
        return 0
    auth = {"Authorization": f"Bearer {tiktok_access_token()}"}
    video_to_episode = {}
    for episode_id, record, payload in rows:
        video_id = payload.get("videoId")
        if not video_id:
            status, _ = json_request(
                "https://open.tiktokapis.com/v2/post/publish/status/fetch/",
                method="POST", headers=auth, payload={"publish_id": payload["id"]},
            )
            data = status.get("data", {})
            ids = data.get("publicaly_available_post_id") or data.get("publicly_available_post_id") or []
            if ids:
                video_id = str(ids[0])
                payload.update({"videoId": video_id, "status": data.get("status", payload.get("status"))})
                save_published_platform(episode_id, record["sha256"], "tiktok", payload)
        if video_id:
            video_to_episode[str(video_id)] = episode_id
    if not video_to_episode:
        raise RuntimeError("TikTok todavía no devolvió IDs públicos para los videos publicados")
    fields = "id,title,create_time,share_url,view_count,like_count,comment_count,share_count"
    count = 0
    for ids in _chunks(list(video_to_episode), 20):
        response, _ = json_request(
            f"https://open.tiktokapis.com/v2/video/query/?fields={fields}",
            method="POST", headers=auth, payload={"filters": {"video_ids": ids}},
        )
        for video in response.get("data", {}).get("videos", []):
            save_video_metrics(video_to_episode[str(video["id"])], "tiktok", {
                "id": video["id"], "title": video.get("title", ""), "share_url": video.get("share_url", ""),
                "create_time": video.get("create_time", 0), "views": video.get("view_count", 0),
                "likes": video.get("like_count", 0), "comments": video.get("comment_count", 0),
                "shares": video.get("share_count", 0),
                "raw": {"api": video, "availableMetrics": ["views", "likes", "comments", "shares"]},
            })
            count += 1
    return count


def sync_instagram(state: dict) -> int:
    rows = _published("instagram", state)
    token = stored_secrets().get("INSTAGRAM_ACCESS_TOKEN") or os.getenv("INSTAGRAM_ACCESS_TOKEN")
    version = os.getenv("INSTAGRAM_GRAPH_VERSION", "v26.0")
    # ponytail: discover the account feed once per sync; keep synthetic IDs for manual uploads.
    media_items = []
    user_id = stored_secrets().get("INSTAGRAM_USER_ID")
    if user_id:
        try:
            url = _query(
                f"https://graph.instagram.com/{version}/{user_id}/media",
                {"fields": "id,media_type,media_product_type", "limit": 100, "access_token": token},
            )
            while url:
                page, _ = json_request(url)
                media_items.extend(
                    media for media in page.get("data", [])
                    if media.get("media_type") == "VIDEO" or media.get("media_product_type") == "REELS"
                )
                url = page.get("paging", {}).get("next")
        except Exception:
            media_items = []

    known = {str(payload["id"]): episode_id for episode_id, _, payload in rows}
    for media in media_items:
        media_id = str(media["id"])
        if media_id not in known:
            rows.append((f"instagram:{media_id}", {}, {"id": media_id}))
    if not rows:
        return 0

    valid_rows = []
    for row in rows:
        media_id = str(row[2]["id"])
        try:
            json_request(_query(
                f"https://graph.instagram.com/{version}/{media_id}",
                {"fields": "id", "access_token": token},
            ))
        except Exception:
            continue
        valid_rows.append(row)
    count = 0
    for episode_id, _, payload in valid_rows:
        media_id = str(payload["id"])
        media, _ = json_request(_query(
            f"https://graph.instagram.com/{version}/{media_id}",
            {"fields": "id,caption,permalink,timestamp", "access_token": token},
        ))
        insights, errors = {}, []
        for metrics in (
            "views,reach,likes,comments,shares,saved",
            "ig_reels_video_view_total_time,ig_reels_avg_watch_time",
        ):
            try:
                response, _ = json_request(_query(
                    f"https://graph.instagram.com/{version}/{media_id}/insights",
                    {"metric": metrics, "access_token": token},
                ))
                insights.update(_insight_values(response))
            except Exception as error:
                errors.append(_safe_error(error))
        if not insights:
            raise RuntimeError(errors[0] if errors else "Instagram no devolvio insights")
        save_video_metrics(episode_id, "instagram", {
            "id": media_id, "title": str(media.get("caption", ""))[:150], "share_url": media.get("permalink", ""),
            "create_time": _epoch(media.get("timestamp")), "views": insights.get("views", insights.get("ig_reels_aggregated_all_plays_count", 0)),
            "likes": insights.get("likes", 0), "comments": insights.get("comments", 0),
            "shares": insights.get("shares", 0), "saves": insights.get("saved"), "reach": insights.get("reach"),
            "watchTimeSeconds": insights.get("ig_reels_video_view_total_time", 0) / 1000 if insights.get("ig_reels_video_view_total_time") is not None else None,
            "averageWatchSeconds": insights.get("ig_reels_avg_watch_time", 0) / 1000 if insights.get("ig_reels_avg_watch_time") is not None else None,
            "raw": {
                "media": media, "insights": insights, "partialErrors": errors,
                "availableMetrics": [
                    name for name, source in {
                        "views": "views", "likes": "likes", "comments": "comments", "shares": "shares",
                        "saves": "saved", "reach": "reach",
                        "watchTimeSeconds": "ig_reels_video_view_total_time",
                        "averageWatchSeconds": "ig_reels_avg_watch_time",
                    }.items() if source in insights
                ],
            },
        })
        count += 1
    return count

def sync_facebook(state: dict) -> int:
    rows = _published("facebook", state)
    if not rows:
        return 0
    token = stored_secrets().get("META_ACCESS_TOKEN") or os.getenv("META_ACCESS_TOKEN")
    version = os.getenv("META_GRAPH_VERSION", "v26.0")
    count = 0
    for episode_id, _, payload in rows:
        video_id = str(payload["id"])
        video, _ = json_request(_query(
            f"https://graph.facebook.com/{version}/{video_id}",
            {"fields": "id,title,permalink_url,created_time,likes.limit(0).summary(true),comments.limit(0).summary(true)", "access_token": token},
        ))
        response, _ = json_request(_query(
            f"https://graph.facebook.com/{version}/{video_id}/video_insights",
            {"access_token": token},
        ))
        insights = _insight_values(response)
        view_metric = next((name for name in ("total_video_views", "media_views", "post_video_views") if name in insights), None)
        views = insights.get(view_metric, 0)
        complete = next((insights[name] for name in ("total_video_complete_views", "post_video_complete_views") if name in insights), None)
        available = ["likes", "comments"]
        if view_metric:
            available.append("views")
        if complete is not None:
            available.append("completionRate")
        save_video_metrics(episode_id, "facebook", {
            "id": video_id, "title": video.get("title", ""), "share_url": video.get("permalink_url", payload.get("url", "")),
            "create_time": _epoch(video.get("created_time")), "views": views,
            "likes": video.get("likes", {}).get("summary", {}).get("total_count", 0),
            "comments": video.get("comments", {}).get("summary", {}).get("total_count", 0), "shares": 0,
            "completionRate": complete / views * 100 if complete is not None and views else None,
            "raw": {"video": video, "insights": insights, "availableMetrics": available},
        })
        count += 1
    return count


def build_snapshot() -> dict:
    episodes = all_episodes()
    by_id = {episode["id"]: episode for episode in episodes}
    published = publishing_state()["videos"]
    histories = {}
    for row in video_metric_snapshots():
        histories.setdefault((row["episodeId"], row["platform"]), []).append(row)
    items = []
    now = datetime.now(timezone.utc)
    for metric in video_metrics():
        episode = by_id.get(metric["episodeId"])
        platform_payload = published.get(metric["episodeId"], {}).get("platforms", {}).get(metric["platform"], {})
        published_at = platform_payload.get("publishedAt")
        age_hours = max((now - datetime.fromisoformat(published_at)).total_seconds() / 3600, 1 / 60) if published_at else None
        history = histories.get((metric["episodeId"], metric["platform"]), [])
        previous = history[1] if len(history) > 1 else None
        delta_hours = (datetime.fromisoformat(history[0]["capturedAt"]) - datetime.fromisoformat(previous["capturedAt"])).total_seconds() / 3600 if previous else None
        defaults = {
            "youtube": {"views", "likes", "comments"},
            "tiktok": {"views", "likes", "comments", "shares"},
            "instagram": {"views", "likes", "comments", "shares", "saves", "reach"},
            "facebook": {"views", "likes", "comments"},
        }
        available = set(metric["raw"].get("availableMetrics", defaults.get(metric["platform"], set())))
        visible = {name: metric[name] if name in available else None for name in (
            "views", "likes", "comments", "shares", "saves", "reach",
            "watchTimeSeconds", "averageWatchSeconds", "completionRate",
        )}
        engagements = sum(visible[name] or 0 for name in ("likes", "comments", "shares", "saves"))
        item = {
            **{key: value for key, value in metric.items() if key != "raw"},
            **visible,
            "availableMetrics": sorted(available),
            "target": episode["target"].get("display_name", episode["target"]["id"].replace("_", " ").title()) if episode else metric["episodeId"],
            "format": format_id_for(episode) if episode else None,
            "formatLabel": format_label(format_id_for(episode)) if episode else "—",
            "publishedAt": published_at,
            "engagements": engagements,
            "engagementRateByViews": round(engagements / visible["views"] * 100, 2) if visible["views"] else None,
            "lifetimeViewsPerHour": round(visible["views"] / age_hours, 2) if visible["views"] is not None and age_hours else None,
            "viewsSincePrevious": visible["views"] - previous["views"] if visible["views"] is not None and previous else None,
            "viewsPerHourSincePrevious": round((visible["views"] - previous["views"]) / delta_hours, 2) if visible["views"] is not None and previous and delta_hours and delta_hours > 0 else None,
        }
        item.update(_creative_metadata(episode, published_at))
        items.append(item)
    platform_summaries = []
    statuses = state_db.load_flag("analytics_sync_status", {})
    for platform in PLATFORMS:
        rows = [item for item in items if item["platform"] == platform]
        views = sum(item["views"] or 0 for item in rows)
        engagements = sum(item["engagements"] for item in rows)
        platform_summaries.append({
            "platform": platform, "videos": len(rows), "views": views, "engagements": engagements,
            "engagementRateByViews": round(engagements / views * 100, 2) if views else None,
            **statuses.get(platform, {}),
        })
    total_views = sum(item["views"] or 0 for item in items)
    total_engagements = sum(item["engagements"] for item in items)
    observations = []
    measured = [item for item in items if item["views"] is not None]
    if measured:
        top = max(measured, key=lambda item: item["views"])
        observations.append(f"Mayor alcance acumulado: {top['episodeId']} en {top['platform']} con {top['views']} vistas.")
        eligible = [item for item in measured if item["views"] >= 100 and item["engagementRateByViews"] is not None]
        if eligible:
            best = max(eligible, key=lambda item: item["engagementRateByViews"])
            observations.append(f"Mejor interacción con al menos 100 vistas: {best['episodeId']} en {best['platform']} ({best['engagementRateByViews']}%).")
        watchable = [item for item in measured if item["views"] >= 100 and item["averageWatchSeconds"] is not None]
        if watchable:
            best = max(watchable, key=lambda item: item["averageWatchSeconds"])
            observations.append(f"Mayor tiempo medio visto: {best['episodeId']} en {best['platform']} ({best['averageWatchSeconds']} s).")
        growing = [item for item in measured if (item["viewsPerHourSincePrevious"] or 0) > 0]
        if growing:
            best = max(growing, key=lambda item: item["viewsPerHourSincePrevious"])
            observations.append(f"Mayor crecimiento desde la captura anterior: {best['episodeId']} en {best['platform']} ({best['viewsPerHourSincePrevious']} vistas/h).")
    for platform in platform_summaries:
        if platform.get("error"):
            observations.append(f"{platform['platform']}: sincronización pendiente ({platform['error']}).")
    return {
        "schemaVersion": 1,
        "generatedAt": now.isoformat(),
        "summary": {
            "videos": len(items), "views": total_views, "engagements": total_engagements,
            "engagementRateByViews": round(total_engagements / total_views * 100, 2) if total_views else None,
        },
        "platforms": platform_summaries,
        "series": _build_series(video_metric_snapshots()),
        "cohorts": _build_cohorts(items),
        "videos": sorted(items, key=lambda item: item["views"] or 0, reverse=True),
        "observations": observations,
        "definitions": {
            "engagements": "likes + comments + shares + saves when the platform exposes saves",
            "engagementRateByViews": "engagements / views * 100",
            "viewsPerHourSincePrevious": "new views divided by hours between the latest two syncs",
        },
        "limitations": [
            "A view is defined differently by each platform; compare direction and relative performance, not absolute equivalence.",
            "TikTok Display API does not expose retention or average watch time.",
            "Unavailable metrics are null, never estimated as zero.",
        ],
        "suggestedGptTask": "Analyze platform health, winners, weak points and concrete next experiments. Separate facts from hypotheses and cite episode IDs.",
    }


def write_exports(snapshot: dict | None = None) -> dict:
    snapshot = snapshot or build_snapshot()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = EXPORT_DIR / "gpt-analytics.json"
    markdown_path = EXPORT_DIR / "gpt-analytics.md"
    json_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Minecraft Quiz Analytics", "", f"Updated: {snapshot['generatedAt']}", "",
        f"Videos measured: {snapshot['summary']['videos']}", f"Views: {snapshot['summary']['views']}",
        f"Engagements: {snapshot['summary']['engagements']}", "", "## Platform status", "",
    ]
    lines.extend(f"- {row['platform']}: {row['videos']} videos, {row['views']} views" + (f" — {row['error']}" if row.get("error") else "") for row in snapshot["platforms"])
    lines.extend(["", "## Observations", ""])
    lines.extend(f"- {item}" for item in snapshot["observations"] or ["Not enough data yet."])
    lines.extend(["", "## Videos", "", "| Platform | Episode | Views | Engagement rate | Views/hour |", "|---|---|---:|---:|---:|"])
    lines.extend(
        f"| {row['platform']} | {row['episodeId']} | {row['views'] if row['views'] is not None else 'N/A'} | "
        f"{str(row['engagementRateByViews']) + '%' if row['engagementRateByViews'] is not None else 'N/A'} | "
        f"{row['viewsPerHourSincePrevious'] if row['viewsPerHourSincePrevious'] is not None else 'N/A'} |"
        for row in snapshot["videos"]
    )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in snapshot["limitations"])
    lines.extend(["", "## GPT instruction", "", snapshot["suggestedGptTask"], ""])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return snapshot


def sync_all() -> dict:
    apply_runtime(load_config())
    configured = credential_status(load_config())
    state = publishing_state()["videos"]
    statuses = {}
    synced_at = datetime.now(timezone.utc).isoformat()
    for platform, sync in {
        "youtube": sync_youtube, "tiktok": sync_tiktok,
        "instagram": sync_instagram, "facebook": sync_facebook,
    }.items():
        if not configured.get(platform):
            statuses[platform] = {"configured": False, "error": "Faltan credenciales", "synced": 0, "syncedAt": synced_at}
            continue
        try:
            count = sync(state)
            statuses[platform] = {"configured": True, "synced": count, "error": None, "syncedAt": synced_at}
        except Exception as error:
            statuses[platform] = {"configured": True, "synced": 0, "error": _safe_error(error), "syncedAt": synced_at}
    state_db.save_flag("analytics_sync_status", statuses)
    return {"status": statuses, "analytics": write_exports()}
