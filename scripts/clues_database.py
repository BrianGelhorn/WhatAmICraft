"""SQLite persistence for the clues catalog.

The JSON files are accepted only by the one-time bootstrap migration. After
that migration, the database is the catalog source of truth.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS targets (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    edition TEXT NOT NULL,
    version TEXT NOT NULL,
    kind TEXT NOT NULL,
    family TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    episode_json TEXT NOT NULL,
    source_file TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS target_candidates (
    target_id TEXT NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    candidate_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY (target_id, candidate_id),
    UNIQUE (target_id, position)
);

CREATE TABLE IF NOT EXISTS facts (
    target_id TEXT NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    id TEXT NOT NULL,
    type TEXT,
    value TEXT,
    scope TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source TEXT NOT NULL,
    verified INTEGER NOT NULL,
    relation TEXT NOT NULL,
    semantic_key TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    PRIMARY KEY (target_id, id)
);

CREATE TABLE IF NOT EXISTS fact_candidates (
    target_id TEXT NOT NULL,
    fact_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    PRIMARY KEY (target_id, fact_id, candidate_id),
    FOREIGN KEY (target_id, fact_id) REFERENCES facts(target_id, id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS clues (
    target_id TEXT NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    clue_order INTEGER NOT NULL,
    text TEXT NOT NULL,
    referent TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    PRIMARY KEY (target_id, clue_order)
);

CREATE TABLE IF NOT EXISTS clue_facts (
    target_id TEXT NOT NULL,
    clue_order INTEGER NOT NULL,
    fact_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY (target_id, clue_order, fact_id),
    UNIQUE (target_id, clue_order, position),
    FOREIGN KEY (target_id, clue_order) REFERENCES clues(target_id, clue_order) ON DELETE CASCADE,
    FOREIGN KEY (target_id, fact_id) REFERENCES facts(target_id, id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS clue_candidates (
    target_id TEXT NOT NULL,
    clue_order INTEGER NOT NULL,
    candidate_id TEXT NOT NULL,
    PRIMARY KEY (target_id, clue_order, candidate_id),
    FOREIGN KEY (target_id, clue_order) REFERENCES clues(target_id, clue_order) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS clue_sources (
    target_id TEXT NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    PRIMARY KEY (target_id, position)
);

CREATE TABLE IF NOT EXISTS target_usage (
    target_id TEXT PRIMARY KEY,
    sources_json TEXT NOT NULL,
    episode_ids_json TEXT NOT NULL,
    video_files_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_target_usage_source
    ON target_usage (target_id);
CREATE INDEX IF NOT EXISTS idx_clue_candidates_target
    ON clue_candidates (target_id, clue_order);
"""


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _decode(value: str, default: object) -> object:
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CluesDatabase:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.executescript(SCHEMA)
        try:
            yield connection
        finally:
            connection.close()

    def _insert_payload(self, connection: sqlite3.Connection, value: dict, source_file: str) -> None:
        episode = value["episode"]
        target = episode["target"]
        target_id = target["id"]
        timestamp = _now()
        connection.execute(
            """
            INSERT INTO targets
                (id, display_name, edition, version, kind, family, metadata_json,
                 episode_json, source_file, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                target_id,
                target["display_name"],
                target["edition"],
                target["version"],
                target["kind"],
                target["family"],
                _json({key: item for key, item in target.items() if key not in {"id", "display_name", "edition", "version", "kind", "family"}}),
                _json(episode),
                source_file,
                timestamp,
                timestamp,
            ),
        )
        for position, candidate_id in enumerate(episode["candidates"]):
            connection.execute(
                "INSERT INTO target_candidates (target_id, candidate_id, position) VALUES (?, ?, ?)",
                (target_id, candidate_id, position),
            )
        for fact in episode["facts"]:
            fact_id = fact["id"]
            connection.execute(
                """
                INSERT INTO facts
                    (target_id, id, type, value, scope, source_type, source, verified,
                     relation, semantic_key, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    target_id,
                    fact_id,
                    fact.get("type"),
                    fact.get("value"),
                    fact["scope"],
                    fact["source_type"],
                    fact["source"],
                    int(fact["verified"]),
                    fact["relation"],
                    fact["semantic_key"],
                    _json({key: item for key, item in fact.items() if key not in {
                        "id", "type", "value", "scope", "source_type", "source",
                        "verified", "relation", "semantic_key", "matches_candidates",
                    }}),
                ),
            )
            connection.executemany(
                "INSERT INTO fact_candidates (target_id, fact_id, candidate_id) VALUES (?, ?, ?)",
                [(target_id, fact_id, candidate_id) for candidate_id in fact["matches_candidates"]],
            )
        for clue in episode["clues"]:
            clue_order = clue["order"]
            connection.execute(
                "INSERT INTO clues (target_id, clue_order, text, referent, metadata_json) VALUES (?, ?, ?, ?, ?)",
                (
                    target_id,
                    clue_order,
                    clue["text"],
                    clue["referent"],
                    _json({key: item for key, item in clue.items() if key not in {
                        "order", "text", "referent", "fact_ids", "matches_candidates",
                    }}),
                ),
            )
            connection.executemany(
                "INSERT INTO clue_facts (target_id, clue_order, fact_id, position) VALUES (?, ?, ?, ?)",
                [(target_id, clue_order, fact_id, position) for position, fact_id in enumerate(clue["fact_ids"])],
            )
            connection.executemany(
                "INSERT INTO clue_candidates (target_id, clue_order, candidate_id) VALUES (?, ?, ?)",
                [(target_id, clue_order, candidate_id) for candidate_id in clue["matches_candidates"]],
            )
        connection.executemany(
            "INSERT INTO clue_sources (target_id, position, title, url) VALUES (?, ?, ?, ?)",
            [(target_id, position, source["title"], source["url"]) for position, source in enumerate(episode["sources"])],
        )

    def initialize(self, migration_files: list[tuple[Path, str]], used_targets_path: Path, validator) -> None:
        with self._connection() as connection:
            if connection.execute("SELECT 1 FROM schema_migrations WHERE version = 1").fetchone():
                return
            if not migration_files:
                raise ValueError("No se encontraron archivos de pistas para la migración inicial")
            connection.execute("BEGIN IMMEDIATE")
            try:
                for path, source_file in migration_files:
                    value = json.loads(path.read_text(encoding="utf-8"))
                    validator(value)
                    self._insert_payload(connection, value, source_file)
                used = {"target_ids": [], "targets": []}
                if used_targets_path.exists():
                    used = json.loads(used_targets_path.read_text(encoding="utf-8"))
                usage_by_id = {
                    item["id"]: item
                    for item in used.get("targets", [])
                    if isinstance(item, dict) and isinstance(item.get("id"), str)
                }
                for target_id in used.get("target_ids", []):
                    if isinstance(target_id, str):
                        usage_by_id.setdefault(target_id, {"id": target_id})
                for target_id, item in usage_by_id.items():
                    connection.execute(
                        """
                        INSERT INTO target_usage
                            (target_id, sources_json, episode_ids_json, video_files_json, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            target_id,
                            _json(list(dict.fromkeys(item.get("sources", ["legacy"]))),),
                            _json(list(dict.fromkeys(item.get("episode_ids", [])))),
                            _json(list(dict.fromkeys(item.get("video_files", [])))),
                            _now(),
                        ),
                    )
                connection.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (1, ?)",
                    (_now(),),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def has_target(self, target_id: str) -> bool:
        with self._connection() as connection:
            return bool(connection.execute(
                "SELECT 1 FROM targets WHERE id = ? UNION SELECT 1 FROM target_usage WHERE target_id = ?",
                (target_id, target_id),
            ).fetchone())

    def insert(self, value: dict) -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._insert_payload(connection, value, "clues_api")
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def usage(self, target_id: str) -> dict | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT target_id, sources_json, episode_ids_json, video_files_json FROM target_usage WHERE target_id = ?",
                (target_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row["target_id"],
            "sources": _decode(row["sources_json"], []),
            "episode_ids": _decode(row["episode_ids_json"], []),
            "video_files": _decode(row["video_files_json"], []),
        }

    def set_usage(self, target_id: str, usage: dict | None) -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                if usage is None:
                    connection.execute("DELETE FROM target_usage WHERE target_id = ?", (target_id,))
                else:
                    connection.execute(
                        """
                        INSERT INTO target_usage
                            (target_id, sources_json, episode_ids_json, video_files_json, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(target_id) DO UPDATE SET
                            sources_json = excluded.sources_json,
                            episode_ids_json = excluded.episode_ids_json,
                            video_files_json = excluded.video_files_json,
                            updated_at = excluded.updated_at
                        """,
                        (
                            target_id,
                            _json(usage.get("sources", [])),
                            _json(usage.get("episode_ids", [])),
                            _json(usage.get("video_files", [])),
                            _now(),
                        ),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def records(self) -> list[dict]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, episode_json, source_file FROM targets ORDER BY id"
            ).fetchall()
            usage_rows = {
                row["target_id"]: {
                    "id": row["target_id"],
                    "sources": _decode(row["sources_json"], []),
                    "episode_ids": _decode(row["episode_ids_json"], []),
                    "video_files": _decode(row["video_files_json"], []),
                }
                for row in connection.execute(
                    "SELECT target_id, sources_json, episode_ids_json, video_files_json FROM target_usage"
                )
            }
        result = []
        for row in rows:
            episode = json.loads(row["episode_json"])
            target_id = row["id"]
            history = usage_rows.get(target_id)
            result.append({
                "id": target_id,
                "status": "used" if history else "unused",
                "used": bool(history),
                "sourceFile": row["source_file"],
                "usage": history or {"sources": [], "episode_ids": [], "video_files": []},
                "target": episode["target"],
                "candidates": episode.get("candidates", []),
                "clues": episode.get("clues", []),
                "facts": episode.get("facts", []),
                "sources": episode.get("sources", []),
                "remainingAfterEachClue": episode.get("remaining_after_each_clue", []),
                "uniqueAnswer": episode.get("unique_answer") is True,
                "needsReview": episode.get("needs_review") is True,
                "episode": episode,
            })
        return result

    def get(self, target_id: str) -> dict:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT episode_json, source_file FROM targets WHERE id = ?",
                (target_id,),
            ).fetchone()
        if not row:
            raise FileNotFoundError(target_id)
        episode = json.loads(row["episode_json"])
        history = self.usage(target_id)
        return {
            "id": target_id,
            "status": "used" if history else "unused",
            "used": bool(history),
            "sourceFile": row["source_file"],
            "usage": history or {"sources": [], "episode_ids": [], "video_files": []},
            "target": episode["target"],
            "candidates": episode.get("candidates", []),
            "clues": episode.get("clues", []),
            "facts": episode.get("facts", []),
            "sources": episode.get("sources", []),
            "remainingAfterEachClue": episode.get("remaining_after_each_clue", []),
            "uniqueAnswer": episode.get("unique_answer") is True,
            "needsReview": episode.get("needs_review") is True,
            "episode": episode,
        }

    def counts(self) -> dict:
        with self._connection() as connection:
            total = connection.execute("SELECT COUNT(*) FROM targets").fetchone()[0]
            used = connection.execute(
                "SELECT COUNT(*) FROM targets WHERE id IN (SELECT target_id FROM target_usage)"
            ).fetchone()[0]
        return {"all": total, "used": used, "unused": total - used}
