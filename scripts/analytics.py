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
QUALITY_FIELDS = {
    "youtube": ("views", "likes", "comments", "averageWatchSeconds", "completionRate"),
    "tiktok": ("views", "likes", "comments", "shares"),
    "instagram": ("views", "reach", "likes", "comments", "shares", "saves", "averageWatchSeconds"),
    "facebook": ("views", "likes", "comments", "completionRate"),
}
TREND_SIGNAL_KINDS = {"audio", "hashtag", "topic", "format"}


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


def validate_trend_signals(payload: object) -> list[dict]:
    values = payload.get("signals") if isinstance(payload, dict) else payload
    if not isinstance(values, list) or len(values) > 100:
        raise ValueError("Las señales deben ser una lista de hasta 100 elementos")
    normalized = []
    for item in values:
        if not isinstance(item, dict):
            raise ValueError("Cada señal debe ser un objeto")
        platform = str(item.get("platform", "")).lower()
        kind = str(item.get("kind", "")).lower()
        value = str(item.get("value", "")).strip()
        source = str(item.get("source", "")).strip()
        if platform not in PLATFORMS or kind not in TREND_SIGNAL_KINDS or not value or len(value) > 120 or not source or len(source) > 120:
            raise ValueError("Señal inválida: plataforma, tipo, valor y fuente son obligatorios")
        captured_at = str(item.get("capturedAt") or datetime.now(timezone.utc).isoformat())
        expires_at = item.get("expiresAt")
        try:
            datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
            if expires_at:
                datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("Las fechas de las señales deben estar en ISO-8601") from error
        score = item.get("score")
        if score is not None:
            try:
                score = round(float(score), 2)
            except (TypeError, ValueError) as error:
                raise ValueError("El score de una señal debe ser numérico") from error
            if score < 0:
                raise ValueError("El score de una señal no puede ser negativo")
        normalized.append({
            "platform": platform, "kind": kind, "value": value, "source": source,
            "score": score, "capturedAt": captured_at, "expiresAt": str(expires_at) if expires_at else None,
            "notes": str(item.get("notes", ""))[:240],
        })
    return normalized


def import_trend_signals(payload: object) -> list[dict]:
    signals = validate_trend_signals(payload)
    state_db.save_flag("analytics_trend_signals", signals)
    return signals


def _active_trend_signals() -> list[dict]:
    values = state_db.load_flag("analytics_trend_signals", [])
    now = datetime.now(timezone.utc)
    return [
        item for item in values
        if not item.get("expiresAt") or datetime.fromisoformat(item["expiresAt"].replace("Z", "+00:00")) > now
    ]


def _published(platform: str, state: dict) -> list[tuple[str, dict, dict]]:
    rows = []
    for episode_id, record in state.items():
        payload = record.get("platforms", {}).get(platform)
        if payload and payload.get("id"):
            rows.append((episode_id, record, payload))
    return rows


def _build_series(snapshots: list[dict]) -> list[dict]:
    latest_by_video = {}
    for snapshot in snapshots:
        captured = datetime.fromisoformat(snapshot["capturedAt"]).astimezone(timezone.utc)
        bucket = captured.replace(minute=0, second=0, microsecond=0).isoformat()
        key = (snapshot["platform"], bucket, snapshot["episodeId"])
        current = latest_by_video.get(key)
        if current is None or captured > datetime.fromisoformat(current["capturedAt"]).astimezone(timezone.utc):
            latest_by_video[key] = snapshot
    buckets = {}
    for snapshot in latest_by_video.values():
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


def _creative_metadata(episode: dict | None, published_at: str | None, published_payload: dict | None = None) -> dict:
    published_payload = published_payload or {}
    if not episode:
        return {
            "targetKind": "unknown", "templateVersion": "unknown", "musicSource": "unknown",
            "durationSeconds": None, "publishHourUtc": None,
            "publishedTitle": published_payload.get("publishedTitle"),
            "publishedCaption": published_payload.get("publishedCaption"),
            "publishedHashtags": published_payload.get("publishedHashtags", []),
        }
    format_id = format_id_for(episode)
    artifact = read_artifact(video_path(episode))
    music_source = "unknown"
    if artifact and artifact.get("configPath"):
        try:
            config = json.loads((ROOT / str(artifact["configPath"])).read_text(encoding="utf-8"))
            music_source = str(config.get("config", {}).get("music", {}).get("sourceName") or "unknown")
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    publish_hour = None
    if published_at:
        publish_hour = datetime.fromisoformat(published_at).astimezone(timezone.utc).hour
    return {
        "targetKind": episode.get("target", {}).get("kind", "unknown").replace("_", " ").title(),
        "templateVersion": artifact.get("templateVersion", "unknown") if artifact else "unknown",
        "musicSource": music_source,
        "durationSeconds": FORMAT_DEFINITIONS.get(format_id, {}).get("durationSeconds"),
        "publishHourUtc": publish_hour,
        "publishedTitle": published_payload.get("publishedTitle"),
        "publishedCaption": published_payload.get("publishedCaption"),
        "publishedHashtags": published_payload.get("publishedHashtags", []),
    }


def _build_cohorts(items: list[dict]) -> list[dict]:
    dimensions = ("formatLabel", "targetKind", "templateVersion", "musicSource", "publishHourUtc")
    baselines = {}
    for platform in PLATFORMS:
        measured = [item for item in items if item["platform"] == platform and item.get("views") is not None]
        hours = [item["lifetimeViewsPerHour"] for item in measured if item.get("lifetimeViewsPerHour") is not None]
        baselines[platform] = {
            "viewsPerVideo": round(sum(item["views"] for item in measured) / len(measured), 2) if measured else None,
            "viewsPerHour": round(sum(hours) / len(hours), 2) if hours else None,
        }
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
        baseline = baselines[group["platform"]]
        group["baselineViewsPerVideo"] = baseline["viewsPerVideo"]
        group["viewsPerVideoLiftPct"] = round((group["viewsPerVideo"] / baseline["viewsPerVideo"] - 1) * 100, 2) if group["viewsPerVideo"] is not None and baseline["viewsPerVideo"] else None
        group["baselineViewsPerHour"] = baseline["viewsPerHour"]
        group["viewsPerHourLiftPct"] = round((group["lifetimeViewsPerHour"] / baseline["viewsPerHour"] - 1) * 100, 2) if group["lifetimeViewsPerHour"] is not None and baseline["viewsPerHour"] else None
        group["sampleConfidence"] = "high" if measured >= 8 else "medium" if measured >= 3 else "low"
        group["sampleWarning"] = None if measured >= 3 else "Muestra pequeña: usar como hipótesis, no como conclusión."
        result.append(group)
    return sorted(result, key=lambda group: (group["dimension"], group["platform"], -(group["viewsPerVideo"] or 0)))


def _build_quality(items: list[dict]) -> list[dict]:
    quality = []
    for platform in PLATFORMS:
        rows = [item for item in items if item["platform"] == platform]
        expected = QUALITY_FIELDS[platform]
        availability = {
            field: sum(item.get(field) is not None for item in rows)
            for field in expected
        }
        slots = len(rows) * len(expected)
        available_slots = sum(availability.values())
        views = [item["views"] for item in rows if item.get("views") is not None]
        reach = [item["reach"] for item in rows if item.get("reach") is not None]
        watch = [item["averageWatchSeconds"] for item in rows if item.get("averageWatchSeconds") is not None]
        completion = [item["completionRate"] for item in rows if item.get("completionRate") is not None]
        total_views = sum(views)
        total_reach = sum(reach)
        warnings = []
        coverage_percent = round(available_slots / slots * 100, 1) if slots else 0
        if rows and not views:
            warnings.append("No hay vistas medibles")
        if rows and coverage_percent < 60:
            warnings.append("Cobertura de métricas baja")
        quality.append({
            "platform": platform,
            "videos": len(rows),
            "measuredVideos": len(views),
            "views": total_views,
            "reach": total_reach if reach else None,
            "reachPerView": round(total_reach / total_views, 2) if total_views and reach else None,
            "averageWatchSeconds": round(sum(watch) / len(watch), 2) if watch else None,
            "completionRate": round(sum(completion) / len(completion), 2) if completion else None,
            "metricCoverage": {
                field: round(count / len(rows) * 100, 1) if rows else 0
                for field, count in availability.items()
            },
            "coveragePercent": coverage_percent,
            "warnings": warnings,
        })
    return quality


def _build_trends(series: list[dict]) -> list[dict]:
    trends = []
    for platform in PLATFORMS:
        points = [point for point in series if point["platform"] == platform]
        if len(points) < 2:
            trends.append({"platform": platform, "trend": "unknown", "viewsPerHour": None, "viewsSincePrevious": None})
            continue
        previous, latest = points[-2], points[-1]
        hours = (datetime.fromisoformat(latest["capturedAt"]) - datetime.fromisoformat(previous["capturedAt"])).total_seconds() / 3600
        delta = latest["views"] - previous["views"]
        trends.append({
            "platform": platform,
            "trend": "up" if delta > 0 else "down" if delta < 0 else "flat",
            "viewsPerHour": round(delta / hours, 2) if hours > 0 else None,
            "viewsSincePrevious": delta,
            "latestViews": latest["views"],
            "capturedAt": latest["capturedAt"],
        })
    return trends


def _build_alerts(items: list[dict], quality: list[dict], trends: list[dict], statuses: dict) -> list[dict]:
    alerts = []
    now = datetime.now(timezone.utc)
    for platform, status in statuses.items():
        if status.get("error"):
            alerts.append({"severity": "high", "platform": platform, "type": "sync", "message": status["error"]})
        synced_at = status.get("syncedAt")
        if status.get("configured") and synced_at:
            age_hours = (now - datetime.fromisoformat(synced_at)).total_seconds() / 3600
            if age_hours > 24:
                alerts.append({"severity": "medium", "platform": platform, "type": "stale", "message": f"La última sincronización tiene {round(age_hours)} h."})
    for row in quality:
        for warning in row["warnings"]:
            if row["videos"]:
                alerts.append({"severity": "medium", "platform": row["platform"], "type": "coverage", "message": warning})
    for item in items:
        if item.get("viewsSincePrevious") is not None and item["viewsSincePrevious"] < 0:
            alerts.append({"severity": "medium", "platform": item["platform"], "type": "anomaly", "episodeId": item["episodeId"], "message": "Las vistas bajaron desde la captura anterior; revisar corrección de la plataforma."})
        if item.get("views", 0) >= 100 and item.get("engagementRateByViews") is not None and item["engagementRateByViews"] < 1:
            alerts.append({"severity": "low", "platform": item["platform"], "type": "engagement", "episodeId": item["episodeId"], "message": "Alcance aceptable, pero interacción inferior al 1%."})
    return alerts


def _build_recommendations(cohorts: list[dict], trends: list[dict]) -> list[dict]:
    recommendations = []
    for dimension in ("formatLabel", "targetKind", "templateVersion", "publishHourUtc"):
        platforms = sorted({cohort["platform"] for cohort in cohorts if cohort["dimension"] == dimension})
        for platform in platforms:
            candidates = [
                cohort for cohort in cohorts
                if cohort["dimension"] == dimension and cohort["platform"] == platform
                and cohort["measuredVideos"] >= 2 and cohort["value"] != "unknown"
            ]
            if not candidates:
                continue
            best = max(candidates, key=lambda cohort: (cohort["lifetimeViewsPerHour"] or 0, cohort["viewsPerVideo"] or 0))
            evidence = best["lifetimeViewsPerHour"] or best["viewsPerVideo"]
            unit = "vistas/h" if best["lifetimeViewsPerHour"] is not None else "vistas/video"
            action = {
                "formatLabel": f"Repetir el formato {best['value']}",
                "targetKind": f"Priorizar targets de tipo {best['value']}",
                "templateVersion": f"Mantener la plantilla {best['value']} mientras siga superando al resto",
                "musicSource": f"Repetir el audio {best['value']} en nuevos videos",
                "publishHourUtc": f"Probar más publicaciones cerca de las {best['value']}",
            }[dimension]
            recommendations.append({
                "priority": "high", "platform": platform, "dimension": dimension,
                "value": best["value"], "action": action,
                "reason": f"{round(evidence, 2)} {unit} con {best['measuredVideos']} videos medidos; confianza {best['sampleConfidence']}.",
                "sampleConfidence": best["sampleConfidence"],
                "liftPct": best["viewsPerHourLiftPct"] if best["lifetimeViewsPerHour"] is not None else best["viewsPerVideoLiftPct"],
            })
    rising = [trend for trend in trends if trend.get("trend") == "up" and trend.get("viewsPerHour")]
    if rising:
        best = max(rising, key=lambda trend: trend["viewsPerHour"])
        recommendations.append({
            "priority": "medium", "platform": best["platform"], "dimension": "trend",
            "value": best["platform"], "action": f"Mantener la cadencia en {best['platform']} y medir el próximo lote.",
            "reason": f"La última ventana creció a {best['viewsPerHour']} vistas/h.",
            "sampleConfidence": "medium",
            "liftPct": None,
        })
    result = []
    for recommendation in recommendations:
        recommendation["id"] = f"{recommendation['platform']}:{recommendation['dimension']}:{recommendation['value']}"
        result.append(state_db.save_analytics_recommendation(recommendation))
    return result


def _experiment_value(item: dict, dimension: str) -> str:
    value = item.get(dimension)
    return f"{value:02d}:00 UTC" if dimension == "publishHourUtc" and isinstance(value, int) else str(value or "unknown")


def _experiment_group(items: list[dict]) -> dict:
    views = [item["views"] for item in items if item.get("views") is not None]
    engagements = sum(item.get("engagements", 0) for item in items)
    total_views = sum(views)
    return {
        "videos": len(items), "measuredVideos": len(views), "views": total_views,
        "viewsPerVideo": round(total_views / len(views), 2) if views else None,
        "engagementRateByViews": round(engagements / total_views * 100, 2) if total_views else None,
    }


def _build_experiments(items: list[dict]) -> list[dict]:
    experiments = []
    for experiment in state_db.analytics_experiments():
        candidates = [item for item in items if item["platform"] == experiment["platform"] and item.get("views") is not None]
        variant = [item for item in candidates if _experiment_value(item, experiment["dimension"]) == experiment["variantValue"]]
        control = [item for item in candidates if _experiment_value(item, experiment["dimension"]) != experiment["variantValue"]]
        variant_result, control_result = _experiment_group(variant), _experiment_group(control)
        lift = round((variant_result["viewsPerVideo"] / control_result["viewsPerVideo"] - 1) * 100, 2) if variant_result["viewsPerVideo"] and control_result["viewsPerVideo"] else None
        experiments.append({
            **experiment,
            "assignmentMode": "observational",
            "control": control_result,
            "variant": variant_result,
            "liftPct": lift,
            "sampleStatus": "ready" if variant_result["measuredVideos"] >= experiment["minimumVideos"] and control_result["measuredVideos"] >= experiment["minimumVideos"] else "waiting",
        })
    return experiments


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
        item.update(_creative_metadata(episode, published_at, platform_payload))
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
    series = _build_series(video_metric_snapshots())
    quality = _build_quality(items)
    trends = _build_trends(series)
    alerts = _build_alerts(items, quality, trends, statuses)
    cohorts = _build_cohorts(items)
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
        "series": series,
        "cohorts": cohorts,
        "quality": quality,
        "trends": trends,
        "trendSignals": _active_trend_signals(),
        "experiments": _build_experiments(items),
        "alerts": alerts,
        "recommendations": _build_recommendations(cohorts, trends),
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
            "Recommendations require at least two measured videos per cohort and do not replace external trend research.",
            "Experiments compare observed variant and baseline cohorts; they are not randomized unless the content plan assigns both groups deliberately.",
        ],
        "suggestedGptTask": "Analyze platform health, trends, cohort winners, data quality, alerts and concrete next experiments. Separate facts from hypotheses and cite episode IDs.",
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
    lines.extend(["", "## Trends", ""])
    lines.extend(
        f"- {row['platform']}: {row['trend']}" + (f", {row['viewsPerHour']} views/hour" if row.get("viewsPerHour") is not None else "")
        for row in snapshot["trends"]
    )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(
        f"- {row['platform']}: {row['action']} — {row['reason']}"
        for row in snapshot["recommendations"] or [{"platform": "all", "action": "Insufficient data", "reason": "Measure at least two videos per cohort."}]
    )
    lines.extend(["", "## Alerts", ""])
    lines.extend(
        f"- {row['severity']} · {row['platform']}: {row['message']}"
        for row in snapshot["alerts"] or [{"severity": "ok", "platform": "all", "message": "No active alerts."}]
    )
    lines.extend(["", "## Data quality", ""])
    lines.extend(
        f"- {row['platform']}: {row['coveragePercent']}% coverage, {row['measuredVideos']}/{row['videos']} videos measured"
        for row in snapshot["quality"]
    )
    lines.extend(["", "## Cohorts", ""])
    lines.extend(
        f"- {row['platform']} · {row['dimension']}={row['value']}: {row['viewsPerVideo'] or 'N/A'} views/video, lift {row['viewsPerVideoLiftPct'] if row['viewsPerVideoLiftPct'] is not None else 'N/A'}%, {row['measuredVideos']} measured, confidence {row['sampleConfidence']}"
        for row in snapshot["cohorts"]
    )
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
