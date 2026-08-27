#!/usr/bin/env python3
"""Immutable identity and validation for generated template artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ID = "quiz-copy"
ARTIFACT_SCHEMA_VERSION = 1
RELEASE_VERSION_PATH = ROOT / ".release-version"
ACTIVE_VERSION_PATH = ROOT / "out/.active-template-version"


def _read_text(path: Path) -> str | None:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def release_version(root: Path = ROOT) -> str:
    configured = os.getenv("WHATAMICRAFT_TEMPLATE_VERSION") or _read_text(root / ".release-version")
    if configured:
        return configured
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "development"


def active_template_version(root: Path = ROOT) -> str:
    return _read_text(root / ACTIVE_VERSION_PATH.relative_to(ROOT)) or release_version(root)


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_job_dir(stem: str, root: Path = ROOT) -> Path:
    return root / "out/render-jobs" / stem


def render_props_path(stem: str, kind: str, root: Path = ROOT) -> Path:
    return render_job_dir(stem, root) / f"{kind}-props.json"


def artifact_path(video: Path) -> Path:
    return video.with_suffix(".artifact.json")


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def write_artifact(
    *,
    episode_id: str,
    video: Path,
    config: dict,
    thumbnail: Path,
    root: Path = ROOT,
) -> Path:
    if not video.is_file():
        raise RuntimeError(f"No se puede crear el manifest: falta {video.name}")
    if not thumbnail.is_file():
        raise RuntimeError(f"No se puede crear el manifest: falta {thumbnail.name}")
    props_path = render_props_path(video.stem, "video", root)
    if not props_path.is_file():
        raise RuntimeError(f"No se puede crear el manifest: falta {props_path}")
    artifact = {
        "schemaVersion": ARTIFACT_SCHEMA_VERSION,
        "templateId": TEMPLATE_ID,
        "templateVersion": release_version(root),
        "compositionId": "QuizCapasCopy",
        "episodeId": episode_id,
        "configSha256": canonical_sha256(config),
        "configPath": _relative(props_path, root),
        "videoPath": _relative(video, root),
        "videoSha256": file_sha256(video),
        "thumbnailPath": _relative(thumbnail, root),
        "thumbnailSha256": file_sha256(thumbnail),
    }
    destination = artifact_path(video)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination


def write_legacy_artifact(
    *,
    episode_id: str,
    video: Path,
    thumbnail: Path,
    root: Path = ROOT,
) -> Path:
    if not video.is_file() or not thumbnail.is_file():
        raise RuntimeError(f"No se puede registrar el legado de {episode_id}: falta video o miniatura")
    artifact = {
        "schemaVersion": ARTIFACT_SCHEMA_VERSION,
        "templateId": TEMPLATE_ID,
        "templateVersion": "legacy",
        "legacy": True,
        "episodeId": episode_id,
        "videoPath": _relative(video, root),
        "videoSha256": file_sha256(video),
        "thumbnailPath": _relative(thumbnail, root),
        "thumbnailSha256": file_sha256(thumbnail),
    }
    destination = artifact_path(video)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination


def read_artifact(video: Path) -> dict | None:
    path = artifact_path(video)
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Manifest inválido para {video.name}: {error}") from error
    return value if isinstance(value, dict) else None


def validate_artifact(
    video: Path,
    *,
    episode_id: str | None = None,
    require_active: bool = False,
    root: Path = ROOT,
) -> dict:
    artifact = read_artifact(video)
    if artifact is None:
        raise RuntimeError(f"Falta el manifest del video {video.name}; regeneralo con la plantilla activa")
    if artifact.get("schemaVersion") != ARTIFACT_SCHEMA_VERSION:
        raise RuntimeError(f"Manifest incompatible para {video.name}")
    if artifact.get("templateId") != TEMPLATE_ID:
        raise RuntimeError(f"Plantilla no autorizada para {video.name}")
    if episode_id and artifact.get("episodeId") != episode_id:
        raise RuntimeError(f"El manifest no corresponde al episodio {episode_id}")
    version = artifact.get("templateVersion")
    if not isinstance(version, str) or not version:
        raise RuntimeError(f"Manifest sin versión de plantilla para {video.name}")
    if artifact.get("legacy"):
        if version != "legacy":
            raise RuntimeError(f"Manifest legado inválido para {video.name}")
        thumbnail = root / str(artifact.get("thumbnailPath", ""))
        if not thumbnail.is_file() or artifact.get("thumbnailSha256") != file_sha256(thumbnail):
            raise RuntimeError(f"La miniatura no coincide con el manifest de {video.name}")
        if artifact.get("videoPath") != _relative(video, root) or artifact.get("videoSha256") != file_sha256(video):
            raise RuntimeError(f"El video cambió después del render: {video.name}")
        return artifact
    if require_active and version != active_template_version(root):
        raise RuntimeError(f"{video.name} usa {version}, pero la plantilla activa es {active_template_version(root)}")
    if artifact.get("videoPath") != _relative(video, root):
        raise RuntimeError(f"La ruta del video no coincide con su manifest: {video.name}")
    if artifact.get("videoSha256") != file_sha256(video):
        raise RuntimeError(f"El video cambió después del render: {video.name}")
    props = root / str(artifact.get("configPath", ""))
    if not props.is_file():
        raise RuntimeError(f"Faltan los props del render para {video.name}")
    try:
        props_value = json.loads(props.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Props inválidos para {video.name}: {error}") from error
    config = props_value.get("config") if isinstance(props_value, dict) else None
    if not isinstance(config, dict) or artifact.get("configSha256") != canonical_sha256(config):
        raise RuntimeError(f"La configuración no coincide con el manifest de {video.name}")
    thumbnail = root / str(artifact.get("thumbnailPath", ""))
    if not thumbnail.is_file() or artifact.get("thumbnailSha256") != file_sha256(thumbnail):
        raise RuntimeError(f"La miniatura no coincide con el manifest de {video.name}")
    return artifact


def activate_template_version(version: str, root: Path = ROOT) -> Path:
    if not version or version != release_version(root):
        raise RuntimeError("Solo se puede activar la versión de la release actualmente instalada")
    destination = root / ACTIVE_VERSION_PATH.relative_to(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(version + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination
