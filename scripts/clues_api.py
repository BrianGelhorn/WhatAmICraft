#!/usr/bin/env python3
"""Local clue catalog API used by the isolated service stack."""

from __future__ import annotations

import json
import os
import re
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from mystery_prefabs import load_prefab_catalog


ROOT = Path(__file__).resolve().parents[1]
TARGET_ID = re.compile(r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$")


class CatalogError(ValueError):
    pass


class UsageConflict(CatalogError):
    pass


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as error:
        raise CatalogError(f"JSON inválido: {path.name}") from error


class ClueCatalog:
    def __init__(
        self,
        root: Path = ROOT,
        source_dirs: list[Path] | None = None,
        upload_dir: Path | None = None,
        used_targets_path: Path | None = None,
        prefab_catalog_path: Path | None = None,
    ):
        self.root = root
        self.source_dirs = source_dirs or [root / "data/new-clues-20260815"]
        self.upload_dir = upload_dir or root / "data/clues/inbox"
        self.used_targets_path = used_targets_path or root / "data/used-targets.json"
        self.prefab_catalog_path = prefab_catalog_path or root / "data/mystery-v2-visual-prefabs.json"
        self._write_lock = threading.Lock()

    def _files(self) -> list[Path]:
        paths = []
        for directory in [*self.source_dirs, self.upload_dir]:
            if directory.exists():
                paths.extend(sorted(path for path in directory.glob("*.json") if path.name != "manifest.json"))
        return paths

    def _load_episode(self, path: Path) -> dict:
        value = read_json(path, None)
        episode = value.get("episode") if isinstance(value, dict) else None
        if not isinstance(episode, dict):
            raise CatalogError(f"La carga {path.name} no contiene episode")
        target = episode.get("target")
        target_id = target.get("id") if isinstance(target, dict) else None
        if not isinstance(target_id, str) or not TARGET_ID.fullmatch(target_id):
            raise CatalogError(f"ID de objetivo inválido en {path.name}")
        self.validate_upload(value)
        return episode

    def _used(self) -> dict[str, dict]:
        value = read_json(self.used_targets_path, {"targets": []})
        result = {
            target_id: {"id": target_id, "sources": [], "episode_ids": [], "video_files": []}
            for target_id in value.get("target_ids", [])
            if isinstance(target_id, str)
        }
        result.update({
            item["id"]: item
            for item in value.get("targets", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        })
        return result

    def records(self) -> list[dict]:
        used = self._used()
        result = {}
        for path in self._files():
            episode = self._load_episode(path)
            target_id = episode["target"]["id"]
            if target_id in result:
                raise CatalogError(f"Hay más de una carga para {target_id}")
            history = used.get(target_id)
            result[target_id] = {
                "id": target_id,
                "status": "used" if history else "unused",
                "used": bool(history),
                "sourceFile": str(path.relative_to(self.root)) if path.is_relative_to(self.root) else path.name,
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
        return [result[target_id] for target_id in sorted(result)]

    def list(self, status: str = "all") -> dict:
        if status not in {"all", "used", "unused"}:
            raise CatalogError("status debe ser all, used o unused")
        items = self.records()
        if status != "all":
            items = [item for item in items if item["status"] == status]
        all_items = self.records()
        return {
            "status": status,
            "items": items,
            "counts": {
                "all": len(all_items),
                "used": sum(item["used"] for item in all_items),
                "unused": sum(not item["used"] for item in all_items),
            },
        }

    def get(self, target_id: str) -> dict:
        if not TARGET_ID.fullmatch(target_id):
            raise CatalogError("ID de objetivo inválido")
        item = next((item for item in self.records() if item["id"] == target_id), None)
        if not item:
            raise FileNotFoundError(target_id)
        return item

    def prefabs(self) -> dict:
        return load_prefab_catalog(self.prefab_catalog_path)

    @staticmethod
    def validate_upload(value: dict) -> dict:
        episode = value.get("episode") if isinstance(value, dict) else None
        if not isinstance(episode, dict):
            raise CatalogError("La carga debe contener episode")
        target = episode.get("target")
        if not isinstance(target, dict) or not TARGET_ID.fullmatch(str(target.get("id", ""))):
            raise CatalogError("episode.target.id inválido")
        for field in ("display_name", "edition", "version", "kind", "family"):
            if not target.get(field):
                raise CatalogError(f"Falta episode.target.{field}")
        clues = episode.get("clues")
        if episode.get("clue_count") != 3 or not isinstance(clues, list) or len(clues) != 3:
            raise CatalogError("La carga debe tener exactamente 3 pistas")
        if episode.get("unique_answer") is not True or episode.get("needs_review") is not False:
            raise CatalogError("Solo se pueden cargar pistas únicas y sin revisión pendiente")
        if not episode.get("clue_count_reason"):
            raise CatalogError("Falta clue_count_reason")
        candidates = episode.get("candidates")
        if not isinstance(candidates, list) or len(candidates) < 2 or len(candidates) != len(set(candidates)) or target["id"] not in candidates:
            raise CatalogError("El objetivo debe estar dentro de candidates")
        facts = episode.get("facts")
        if not isinstance(facts, list) or not facts or not all(isinstance(fact, dict) and fact.get("id") for fact in facts):
            raise CatalogError("La carga debe incluir facts válidos")
        fact_by_id = {fact["id"]: fact for fact in facts}
        if len(fact_by_id) != len(facts):
            raise CatalogError("Los facts no pueden repetir ID")
        fact_matches = {}
        for fact in facts:
            if any(not fact.get(field) for field in ("scope", "source_type", "source", "relation", "semantic_key")):
                raise CatalogError(f"El fact {fact['id']} está incompleto")
            if not isinstance(fact.get("verified"), bool) or fact.get("source_type") == "inference" and fact["verified"]:
                raise CatalogError(f"El fact {fact['id']} tiene verified inválido")
            matches = fact.get("matches_candidates")
            if not isinstance(matches, list) or not set(matches).issubset(candidates) or target["id"] not in matches:
                raise CatalogError(f"El fact {fact['id']} tiene candidatos inválidos")
            fact_matches[fact["id"]] = set(matches)
        if any(len(matches) < 2 for matches in fact_matches.values()):
            raise CatalogError("Cada fact debe mantener al menos dos candidatos")
        remaining = set(candidates)
        remaining_counts = []
        for index, clue in enumerate(clues, 1):
            if not isinstance(clue, dict) or not isinstance(clue.get("text"), str) or not clue["text"].strip():
                raise CatalogError(f"La pista {index} no tiene texto")
            if len(clue["text"]) > 90:
                raise CatalogError(f"La pista {index} supera 90 caracteres")
            fact_ids = clue.get("fact_ids")
            if clue.get("referent") != "target" or not isinstance(fact_ids, list) or not fact_ids or not set(fact_ids).issubset(fact_by_id):
                raise CatalogError(f"La pista {index} referencia facts inválidos")
            matches = set.intersection(*(fact_matches[fact_id] for fact_id in fact_ids))
            if set(clue.get("matches_candidates", [])) != matches or len(matches) < 2 or target["id"] not in matches:
                raise CatalogError(f"La pista {index} no coincide con la intersección de sus facts")
            remaining.intersection_update(matches)
            remaining_counts.append(len(remaining))
        if episode.get("remaining_after_each_clue") != remaining_counts or any(
            remaining_counts[index] >= remaining_counts[index - 1] for index in range(1, len(remaining_counts))
        ):
            raise CatalogError("remaining_after_each_clue no coincide con la intersección progresiva")
        if remaining != {target["id"]}:
            raise CatalogError("Las pistas no dejan un único objetivo")
        if not isinstance(episode.get("sources"), list) or not episode["sources"]:
            raise CatalogError("La carga debe incluir sources")
        if not all(isinstance(source, dict) and source.get("title") and source.get("url") for source in episode["sources"]):
            raise CatalogError("Cada source debe tener title y url")
        return value

    def upload(self, value: dict) -> dict:
        value = self.validate_upload(value)
        target_id = value["episode"]["target"]["id"]
        with self._write_lock:
            if target_id in self._used() or any(item["id"] == target_id for item in self.records()):
                raise FileExistsError(target_id)
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            destination = self.upload_dir / f"{target_id}.json"
            temporary = destination.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temporary.replace(destination)
        return self.get(target_id)

    def update_usage(
        self,
        target_id: str,
        status: str,
        episode_id: str | None = None,
        video_file: str | None = None,
    ) -> dict:
        if not TARGET_ID.fullmatch(target_id):
            raise CatalogError("ID de objetivo inválido")
        if status not in {"used", "unused"}:
            raise CatalogError("status debe ser used o unused")
        for name, value, maximum in (("episodeId", episode_id, 120), ("videoFile", video_file, 255)):
            if value is not None and (not isinstance(value, str) or not value.strip() or len(value) > maximum or any(char in value for char in "\\/")):
                raise CatalogError(f"{name} inválido")
        current = self.get(target_id)
        with self._write_lock:
            document = read_json(self.used_targets_path, {"target_ids": [], "targets": []})
            if not isinstance(document, dict):
                raise CatalogError("used-targets.json inválido")
            target_ids = list(dict.fromkeys(item for item in document.get("target_ids", []) if isinstance(item, str)))
            targets = [item for item in document.get("targets", []) if isinstance(item, dict) and isinstance(item.get("id"), str)]
            existing = next((item for item in targets if item["id"] == target_id), None)
            is_used = target_id in target_ids or existing is not None

            if status == "unused":
                sources = existing.get("sources", []) if existing else []
                if is_used and sources != ["clues_api"]:
                    raise UsageConflict("No se puede quitar un uso registrado fuera de esta API")
                target_ids = [item for item in target_ids if item != target_id]
                targets = [item for item in targets if item["id"] != target_id]
            elif not is_used:
                target = current["target"]
                record = {
                    "id": target_id,
                    "display_name": target.get("display_name"),
                    "kind": target.get("kind"),
                    "sources": ["clues_api"],
                    "episode_ids": [],
                    "video_files": [],
                }
                targets.append(record)
                target_ids.append(target_id)
                existing = record
            elif existing and existing.get("sources") == ["clues_api"]:
                existing.setdefault("episode_ids", [])
                existing.setdefault("video_files", [])

            if status == "used" and existing and existing.get("sources") == ["clues_api"]:
                if episode_id and episode_id not in existing["episode_ids"]:
                    existing["episode_ids"].append(episode_id)
                if video_file and video_file not in existing["video_files"]:
                    existing["video_files"].append(video_file)
            document["target_ids"] = sorted(target_ids)
            document["targets"] = sorted(targets, key=lambda item: item["id"])
            self.used_targets_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.used_targets_path.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temporary.replace(self.used_targets_path)
        return self.get(target_id)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return

    @property
    def catalog(self) -> ClueCatalog:
        return self.server.catalog  # type: ignore[attr-defined]

    def send_json(self, value: dict, status: int = 200) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/health":
                self.send_json({"ok": True, "service": "clues-api", "counts": self.catalog.list()["counts"]})
            elif parsed.path == "/api/clues":
                query = parse_qs(parsed.query)
                status = query.get("status", ["all"])[0]
                result = self.catalog.list(status)
                offset = max(0, int(query.get("offset", ["0"])[0]))
                limit = min(100, max(1, int(query.get("limit", ["100"])[0])))
                result["items"] = result["items"][offset:offset + limit]
                self.send_json(result)
            elif parsed.path == "/api/clue-prefabs":
                self.send_json(self.catalog.prefabs())
            elif parsed.path.startswith("/api/clues/"):
                self.send_json(self.catalog.get(unquote(parsed.path.removeprefix("/api/clues/"))))
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except FileNotFoundError:
            self.send_json({"ok": False, "error": "Pista no encontrada"}, HTTPStatus.NOT_FOUND)
        except (CatalogError, ValueError) as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except Exception:
            self.send_json({"ok": False, "error": "No se pudo consultar el catálogo"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/clues":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 2 * 1024 * 1024:
                raise CatalogError("Carga vacía o demasiado grande")
            value = json.loads(self.rfile.read(size))
            self.send_json(self.catalog.upload(value), HTTPStatus.CREATED)
        except FileExistsError:
            self.send_json({"ok": False, "error": "El objetivo ya existe en el catálogo"}, HTTPStatus.CONFLICT)
        except (CatalogError, json.JSONDecodeError) as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except Exception:
            self.send_json({"ok": False, "error": "No se pudo cargar la pista"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/clues/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 16 * 1024:
                raise CatalogError("Carga vacía o demasiado grande")
            value = json.loads(self.rfile.read(size))
            if not isinstance(value, dict):
                raise CatalogError("El cuerpo debe ser un objeto JSON")
            result = self.catalog.update_usage(
                unquote(parsed.path.removeprefix("/api/clues/")),
                value.get("status"),
                value.get("episodeId"),
                value.get("videoFile"),
            )
            self.send_json(result)
        except FileNotFoundError:
            self.send_json({"ok": False, "error": "Pista no encontrada"}, HTTPStatus.NOT_FOUND)
        except UsageConflict as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.CONFLICT)
        except (CatalogError, json.JSONDecodeError) as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except Exception:
            self.send_json({"ok": False, "error": "No se pudo actualizar el uso de la pista"}, HTTPStatus.INTERNAL_SERVER_ERROR)


def make_server(host: str, port: int, catalog: ClueCatalog) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), Handler)
    server.catalog = catalog  # type: ignore[attr-defined]
    return server


def main() -> None:
    root = Path(os.getenv("CLUES_ROOT", str(ROOT)))
    source = Path(os.getenv("CLUES_SOURCE_DIR", str(root / "data/new-clues-20260815")))
    upload = Path(os.getenv("CLUES_UPLOAD_DIR", str(root / "data/clues/inbox")))
    used = Path(os.getenv("CLUES_USED_TARGETS_PATH", str(root / "data/used-targets.json")))
    prefab_catalog = Path(os.getenv("CLUES_PREFAB_CATALOG_PATH", str(root / "data/mystery-v2-visual-prefabs.json")))
    server = make_server(os.getenv("CLUES_HOST", "0.0.0.0"), int(os.getenv("CLUES_PORT", "8790")), ClueCatalog(root, [source], upload, used, prefab_catalog))
    print(f"Clues API activo en el puerto {server.server_port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
