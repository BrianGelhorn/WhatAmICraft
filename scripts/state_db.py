import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "out/app-state.sqlite3"


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        result = super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return result


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    db_path = db_path or DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=30, factory=ClosingConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=30000")
    return connection


def _read_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def init(db_path: Path | None = None) -> None:
    with _connect(db_path) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS queue (
                episode_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                queued_at TEXT,
                updated_at TEXT,
                error TEXT
            );
            CREATE TABLE IF NOT EXISTS pending_hints (
                episode_id TEXT PRIMARY KEY,
                requested_at TEXT NOT NULL,
                episode_json TEXT NOT NULL,
                localized_copy_json TEXT
            );
            CREATE TABLE IF NOT EXISTS published_videos (
                episode_id TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS published_platforms (
                episode_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                published_at TEXT,
                PRIMARY KEY (episode_id, platform)
            );
            CREATE TABLE IF NOT EXISTS video_metrics (
                episode_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                video_id TEXT NOT NULL,
                title TEXT NOT NULL,
                share_url TEXT NOT NULL,
                create_time INTEGER NOT NULL,
                view_count INTEGER NOT NULL CHECK (view_count >= 0),
                like_count INTEGER NOT NULL CHECK (like_count >= 0),
                comment_count INTEGER NOT NULL CHECK (comment_count >= 0),
                share_count INTEGER NOT NULL CHECK (share_count >= 0),
                save_count INTEGER,
                reach_count INTEGER,
                watch_time_seconds REAL,
                average_watch_seconds REAL,
                completion_rate REAL,
                raw_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL,
                PRIMARY KEY (episode_id, platform)
            );
            CREATE TABLE IF NOT EXISTS video_metric_snapshots (
                episode_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                video_id TEXT NOT NULL,
                view_count INTEGER NOT NULL,
                like_count INTEGER NOT NULL,
                comment_count INTEGER NOT NULL,
                share_count INTEGER NOT NULL,
                save_count INTEGER,
                reach_count INTEGER,
                watch_time_seconds REAL,
                average_watch_seconds REAL,
                completion_rate REAL,
                captured_at TEXT NOT NULL,
                PRIMARY KEY (episode_id, platform, captured_at)
            );
            CREATE TABLE IF NOT EXISTS schedules (
                name TEXT PRIMARY KEY,
                next_run_at TEXT
            );
            CREATE TABLE IF NOT EXISTS flags (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS analytics_recommendations (
                recommendation_id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        existing = {row["name"] for row in db.execute("PRAGMA table_info(video_metrics)")}
        for name, kind in {
            "save_count": "INTEGER",
            "reach_count": "INTEGER",
            "watch_time_seconds": "REAL",
            "average_watch_seconds": "REAL",
            "completion_rate": "REAL",
            "raw_json": "TEXT NOT NULL DEFAULT '{}'",
        }.items():
            if name not in existing:
                db.execute(f"ALTER TABLE video_metrics ADD COLUMN {name} {kind}")


def migrate_json_state(
    *,
    db_path: Path | None = None,
    queue_path: Path,
    publishing_state_path: Path,
    pending_hints_path: Path,
    publishing_schedule_path: Path,
    generation_schedule_path: Path,
    stock_alert_path: Path,
) -> None:
    init(db_path)
    with _connect(db_path) as db:
        if db.execute("SELECT 1 FROM meta WHERE key = 'json_state_migrated'").fetchone():
            return

        for item in _read_json(queue_path, {"items": []}).get("items", []):
            db.execute(
                """
                INSERT OR REPLACE INTO queue (episode_id, status, queued_at, updated_at, error)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    item["episodeId"],
                    item.get("status", "pending"),
                    item.get("queuedAt"),
                    item.get("updatedAt"),
                    item.get("error"),
                ),
            )

        for episode_id, record in _read_json(publishing_state_path, {"videos": {}}).get("videos", {}).items():
            if not record.get("sha256"):
                continue
            db.execute(
                "INSERT OR REPLACE INTO published_videos (episode_id, sha256) VALUES (?, ?)",
                (episode_id, record["sha256"]),
            )
            for platform, payload in record.get("platforms", {}).items():
                payload = dict(payload or {})
                db.execute(
                    """
                    INSERT OR REPLACE INTO published_platforms
                    (episode_id, platform, payload_json, published_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        episode_id,
                        platform,
                        json.dumps(payload, ensure_ascii=False),
                        payload.get("publishedAt"),
                    ),
                )

        for item in _read_json(pending_hints_path, {"items": []}).get("items", []):
            db.execute(
                """
                INSERT OR REPLACE INTO pending_hints
                (episode_id, requested_at, episode_json, localized_copy_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    item["episodeId"],
                    item.get("requestedAt") or datetime.now(timezone.utc).isoformat(),
                    json.dumps(item.get("episode", {}), ensure_ascii=False),
                    json.dumps(item.get("localizedCopy"), ensure_ascii=False),
                ),
            )

        db.execute(
            "INSERT OR REPLACE INTO schedules (name, next_run_at) VALUES (?, ?)",
            ("publishing", _read_json(publishing_schedule_path, {"nextRunAt": None}).get("nextRunAt")),
        )
        db.execute(
            "INSERT OR REPLACE INTO schedules (name, next_run_at) VALUES (?, ?)",
            ("generation", _read_json(generation_schedule_path, {"nextRunAt": None}).get("nextRunAt")),
        )
        db.execute(
            "INSERT OR REPLACE INTO flags (key, value_json) VALUES (?, ?)",
            ("stock_alert", json.dumps(_read_json(stock_alert_path, {"low": False}), ensure_ascii=False)),
        )
        db.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('json_state_migrated', ?)", (datetime.now(timezone.utc).isoformat(),))


def queue_items(db_path: Path | None = None) -> list[dict]:
    init(db_path)
    with _connect(db_path) as db:
        rows = db.execute("SELECT * FROM queue ORDER BY queued_at, episode_id").fetchall()
    return [
        {
            "episodeId": row["episode_id"],
            "status": row["status"],
            "queuedAt": row["queued_at"],
            "updatedAt": row["updated_at"],
            **({"error": row["error"]} if row["error"] else {}),
        }
        for row in rows
    ]


def upsert_queue_item(episode_id: str, status: str = "pending", error: str | None = None, db_path: Path | None = None) -> None:
    init(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as db:
        current = db.execute("SELECT queued_at FROM queue WHERE episode_id = ?", (episode_id,)).fetchone()
        db.execute(
            """
            INSERT INTO queue (episode_id, status, queued_at, updated_at, error)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(episode_id) DO UPDATE SET
                status = excluded.status,
                updated_at = excluded.updated_at,
                error = excluded.error
            """,
            (episode_id, status, current["queued_at"] if current else now, now, error),
        )


def pending_queue_ids(db_path: Path | None = None) -> list[str]:
    return [item["episodeId"] for item in queue_items(db_path) if item["status"] == "pending"]


def set_queue_status(episode_id: str, status: str, error: str | None = None, db_path: Path | None = None) -> None:
    init(db_path)
    with _connect(db_path) as db:
        db.execute(
            """
            UPDATE queue
            SET status = ?, updated_at = ?, error = ?
            WHERE episode_id = ?
            """,
            (status, datetime.now(timezone.utc).isoformat(), error[:1000] if error else None, episode_id),
        )


def remove_queue_item(episode_id: str, db_path: Path | None = None) -> None:
    init(db_path)
    with _connect(db_path) as db:
        db.execute("DELETE FROM queue WHERE episode_id = ?", (episode_id,))


def pending_hints_items(db_path: Path | None = None) -> list[dict]:
    init(db_path)
    with _connect(db_path) as db:
        rows = db.execute("SELECT * FROM pending_hints ORDER BY requested_at, episode_id").fetchall()
    return [
        {
            "episodeId": row["episode_id"],
            "requestedAt": row["requested_at"],
            "episode": json.loads(row["episode_json"]),
            "localizedCopy": json.loads(row["localized_copy_json"]) if row["localized_copy_json"] else None,
        }
        for row in rows
    ]


def upsert_pending_hint(episode_id: str, episode: dict, localized_copy: dict | None, db_path: Path | None = None) -> None:
    init(db_path)
    with _connect(db_path) as db:
        db.execute(
            """
            INSERT OR REPLACE INTO pending_hints
            (episode_id, requested_at, episode_json, localized_copy_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                episode_id,
                datetime.now(timezone.utc).isoformat(),
                json.dumps(episode, ensure_ascii=False),
                json.dumps(localized_copy, ensure_ascii=False),
            ),
        )


def remove_pending_hint(episode_id: str, db_path: Path | None = None) -> None:
    init(db_path)
    with _connect(db_path) as db:
        db.execute("DELETE FROM pending_hints WHERE episode_id = ?", (episode_id,))


def publishing_state(db_path: Path | None = None) -> dict:
    init(db_path)
    with _connect(db_path) as db:
        videos = {
            row["episode_id"]: {"sha256": row["sha256"], "platforms": {}}
            for row in db.execute("SELECT * FROM published_videos").fetchall()
        }
        rows = db.execute("SELECT * FROM published_platforms").fetchall()
    for row in rows:
        record = videos.setdefault(row["episode_id"], {"sha256": "", "platforms": {}})
        payload = json.loads(row["payload_json"])
        if row["published_at"] and "publishedAt" not in payload:
            payload["publishedAt"] = row["published_at"]
        record["platforms"][row["platform"]] = payload
    return {"videos": videos}


def set_published_platform(episode_id: str, fingerprint: str, platform: str, payload: dict, db_path: Path | None = None) -> None:
    init(db_path)
    payload = dict(payload)
    published_at = payload.get("publishedAt")
    with _connect(db_path) as db:
        current = db.execute("SELECT sha256 FROM published_videos WHERE episode_id = ?", (episode_id,)).fetchone()
        if current and current["sha256"] != fingerprint:
            db.execute("DELETE FROM published_platforms WHERE episode_id = ?", (episode_id,))
        db.execute(
            "INSERT OR REPLACE INTO published_videos (episode_id, sha256) VALUES (?, ?)",
            (episode_id, fingerprint),
        )
        db.execute(
            """
            INSERT OR REPLACE INTO published_platforms
            (episode_id, platform, payload_json, published_at)
            VALUES (?, ?, ?, ?)
            """,
            (episode_id, platform, json.dumps(payload, ensure_ascii=False), published_at),
        )


def set_video_metrics(episode_id: str, platform: str, video: dict, db_path: Path | None = None) -> None:
    def metric(name: str, legacy: str, *, integer: bool = True):
        value = video.get(name, video.get(legacy))
        if value is None:
            return None
        return int(value) if integer else float(value)

    values = [metric(name, legacy) or 0 for name, legacy in (
        ("views", "view_count"), ("likes", "like_count"),
        ("comments", "comment_count"), ("shares", "share_count"),
    )]
    optional = [
        metric("saves", "save_count"),
        metric("reach", "reach_count"),
        metric("watchTimeSeconds", "watch_time_seconds", integer=False),
        metric("averageWatchSeconds", "average_watch_seconds", integer=False),
        metric("completionRate", "completion_rate", integer=False),
    ]
    if any(value is not None and value < 0 for value in [*values, *optional]):
        raise ValueError("Las metricas no pueden ser negativas")
    init(db_path)
    captured_at = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as db:
        previous = db.execute(
            "SELECT MAX(captured_at) FROM video_metric_snapshots WHERE episode_id = ? AND platform = ?",
            (episode_id, platform),
        ).fetchone()[0]
        if previous and captured_at <= previous:
            captured_at = (datetime.fromisoformat(previous) + timedelta(microseconds=1)).isoformat()
        db.execute(
            """
            INSERT INTO video_metrics
            (episode_id, platform, video_id, title, share_url, create_time,
             view_count, like_count, comment_count, share_count, save_count, reach_count,
             watch_time_seconds, average_watch_seconds, completion_rate, raw_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(episode_id, platform) DO UPDATE SET
                video_id = excluded.video_id,
                title = excluded.title,
                share_url = excluded.share_url,
                create_time = excluded.create_time,
                view_count = excluded.view_count,
                like_count = excluded.like_count,
                comment_count = excluded.comment_count,
                share_count = excluded.share_count,
                save_count = excluded.save_count,
                reach_count = excluded.reach_count,
                watch_time_seconds = excluded.watch_time_seconds,
                average_watch_seconds = excluded.average_watch_seconds,
                completion_rate = excluded.completion_rate,
                raw_json = excluded.raw_json,
                updated_at = excluded.updated_at
            """,
            (
                episode_id,
                platform,
                str(video["id"]),
                str(video.get("title", "")),
                str(video.get("share_url", "")),
                int(video.get("create_time", 0)),
                *values,
                *optional,
                json.dumps(video.get("raw", {}), ensure_ascii=False),
                captured_at,
            ),
        )
        db.execute(
            """
            INSERT INTO video_metric_snapshots
            (episode_id, platform, video_id, view_count, like_count, comment_count,
             share_count, save_count, reach_count, watch_time_seconds,
             average_watch_seconds, completion_rate, captured_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (episode_id, platform, str(video["id"]), *values, *optional, captured_at),
        )


def video_metrics(db_path: Path | None = None) -> list[dict]:
    init(db_path)
    with _connect(db_path) as db:
        rows = db.execute("SELECT * FROM video_metrics ORDER BY view_count DESC, episode_id").fetchall()
    return [
        {
            "episodeId": row["episode_id"],
            "platform": row["platform"],
            "videoId": row["video_id"],
            "title": row["title"],
            "shareUrl": row["share_url"],
            "createTime": row["create_time"],
            "views": row["view_count"],
            "likes": row["like_count"],
            "comments": row["comment_count"],
            "shares": row["share_count"],
            "saves": row["save_count"],
            "reach": row["reach_count"],
            "watchTimeSeconds": row["watch_time_seconds"],
            "averageWatchSeconds": row["average_watch_seconds"],
            "completionRate": row["completion_rate"],
            "raw": json.loads(row["raw_json"] or "{}"),
            "updatedAt": row["updated_at"],
        }
        for row in rows
    ]


def video_metric_snapshots(db_path: Path | None = None) -> list[dict]:
    init(db_path)
    with _connect(db_path) as db:
        rows = db.execute("SELECT * FROM video_metric_snapshots ORDER BY captured_at DESC LIMIT 1000").fetchall()
    return [
        {
            "episodeId": row["episode_id"], "platform": row["platform"], "videoId": row["video_id"],
            "views": row["view_count"], "likes": row["like_count"], "comments": row["comment_count"],
            "shares": row["share_count"], "saves": row["save_count"], "reach": row["reach_count"],
            "watchTimeSeconds": row["watch_time_seconds"], "averageWatchSeconds": row["average_watch_seconds"],
            "completionRate": row["completion_rate"], "capturedAt": row["captured_at"],
        }
        for row in rows
    ]


def remove_published(episode_id: str, db_path: Path | None = None) -> None:
    init(db_path)
    with _connect(db_path) as db:
        db.execute("DELETE FROM published_platforms WHERE episode_id = ?", (episode_id,))
        db.execute("DELETE FROM published_videos WHERE episode_id = ?", (episode_id,))
        db.execute("DELETE FROM video_metrics WHERE episode_id = ?", (episode_id,))
        db.execute("DELETE FROM video_metric_snapshots WHERE episode_id = ?", (episode_id,))


def load_schedule(name: str, db_path: Path | None = None) -> dict:
    init(db_path)
    with _connect(db_path) as db:
        row = db.execute("SELECT next_run_at FROM schedules WHERE name = ?", (name,)).fetchone()
    return {"nextRunAt": row["next_run_at"] if row else None}


def save_schedule(name: str, next_run_at: str | None, db_path: Path | None = None) -> None:
    init(db_path)
    with _connect(db_path) as db:
        db.execute(
            "INSERT OR REPLACE INTO schedules (name, next_run_at) VALUES (?, ?)",
            (name, next_run_at),
        )


def load_flag(key: str, default, db_path: Path | None = None):
    init(db_path)
    with _connect(db_path) as db:
        row = db.execute("SELECT value_json FROM flags WHERE key = ?", (key,)).fetchone()
    return json.loads(row["value_json"]) if row else default


def save_flag(key: str, value, db_path: Path | None = None) -> None:
    init(db_path)
    with _connect(db_path) as db:
        db.execute(
            "INSERT OR REPLACE INTO flags (key, value_json) VALUES (?, ?)",
            (key, json.dumps(value, ensure_ascii=False)),
        )


def save_analytics_recommendation(recommendation: dict, db_path: Path | None = None) -> dict:
    recommendation_id = str(recommendation["id"])
    now = datetime.now(timezone.utc).isoformat()
    init(db_path)
    with _connect(db_path) as db:
        current = db.execute(
            "SELECT status, created_at FROM analytics_recommendations WHERE recommendation_id = ?",
            (recommendation_id,),
        ).fetchone()
        status = current["status"] if current else "proposed"
        created_at = current["created_at"] if current else now
        db.execute(
            """
            INSERT OR REPLACE INTO analytics_recommendations
            (recommendation_id, payload_json, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (recommendation_id, json.dumps(recommendation, ensure_ascii=False), status, created_at, now),
        )
    return {**recommendation, "status": status, "createdAt": created_at, "updatedAt": now}


def set_analytics_recommendation_status(recommendation_id: str, status: str, db_path: Path | None = None) -> dict:
    if status not in {"proposed", "applied", "dismissed"}:
        raise ValueError("Estado de recomendación inválido")
    init(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as db:
        row = db.execute(
            "SELECT payload_json, created_at FROM analytics_recommendations WHERE recommendation_id = ?",
            (recommendation_id,),
        ).fetchone()
        if not row:
            raise ValueError("Recomendación no encontrada")
        db.execute(
            "UPDATE analytics_recommendations SET status = ?, updated_at = ? WHERE recommendation_id = ?",
            (status, now, recommendation_id),
        )
    return {**json.loads(row["payload_json"]), "status": status, "createdAt": row["created_at"], "updatedAt": now}


def export_legacy_json(
    *,
    db_path: Path | None = None,
    queue_path: Path,
    publishing_state_path: Path,
    pending_hints_path: Path,
    publishing_schedule_path: Path,
    generation_schedule_path: Path,
    stock_alert_path: Path,
) -> None:
    _write_json(queue_path, {"items": queue_items(db_path)})
    _write_json(publishing_state_path, publishing_state(db_path))
    _write_json(pending_hints_path, {"items": pending_hints_items(db_path)})
    _write_json(publishing_schedule_path, load_schedule("publishing", db_path))
    _write_json(generation_schedule_path, load_schedule("generation", db_path))
    _write_json(stock_alert_path, load_flag("stock_alert", {"low": False}, db_path))
