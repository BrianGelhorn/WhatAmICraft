from __future__ import annotations

import copy
import json
import random
from pathlib import Path

try:
    from .template_artifacts import active_template_version, read_artifact
    from .thumbnails import DEFAULT_DESIGN_VARIANT, type_slug
except ImportError:  # script entrypoints run with scripts/ on sys.path
    from template_artifacts import active_template_version, read_artifact
    from thumbnails import DEFAULT_DESIGN_VARIANT, type_slug

ROOT = Path(__file__).resolve().parents[1]
TARGET_KINDS = {
    item["id"]: item.get("kind", "")
    for item in json.loads((ROOT / "data/used-targets.json").read_text(encoding="utf-8")).get("targets", [])
}

FORMAT_DEFINITIONS = {
    "clues": {
        "label": "Quiz definitivo",
        "bank": ROOT / "data/quiz-copy-episodes.json",
        "durationSeconds": 28,
    },
}

DEFAULT_FORMAT_SETTINGS = {"clues": {"enabled": True, "priority": 1}}


def format_id_for(episode: dict) -> str:
    return episode.get("format", "clues")


def format_label(format_id: str) -> str:
    return FORMAT_DEFINITIONS.get(format_id, {}).get("label", format_id)


def with_target_kind(episode: dict) -> dict:
    item = copy.deepcopy(episode)
    kind = TARGET_KINDS.get(item.get("answer", {}).get("id"))
    if kind and kind != "unknown":
        item["answer"]["guessType"] = kind.replace("_", " ").title()
    return item


def normalize_episode(episode: dict, format_id: str = "clues") -> dict:
    item = with_target_kind(episode)
    answer = item["answer"]
    item["target"] = {
        "id": answer["id"],
        "display_name": answer["displayName"],
        "kind": answer["guessType"].lower(),
    }
    item["unique_answer"] = item.get("uniqueAnswer", True)
    item["needs_review"] = item.get("needsReview", False)
    item.setdefault("format", format_id)
    return item


def read_episodes(format_id: str) -> list[dict]:
    definition = FORMAT_DEFINITIONS[format_id]
    if not definition["bank"].exists():
        return []
    raw = json.loads(definition["bank"].read_text(encoding="utf-8"))
    return [normalize_episode(episode, format_id) for episode in raw.get("episodes", [])]


def all_episodes() -> list[dict]:
    return [episode for format_id in FORMAT_DEFINITIONS for episode in read_episodes(format_id)]


def ready_episodes(format_id: str | None = None) -> list[dict]:
    source = read_episodes(format_id) if format_id else all_episodes()
    return [episode for episode in source if episode.get("unique_answer", True) and not episode.get("needs_review")]


def video_stem(episode: dict) -> str:
    return f"{episode['id']}-{episode['target']['id']}"


def video_path(episode: dict, root: Path = ROOT) -> Path:
    return root / "out/episodes" / f"{video_stem(episode)}.mp4"


def current_template_video_names(root: Path = ROOT) -> set[str]:
    active = active_template_version(root)
    names = set()
    episodes = root / "out/episodes"
    if not episodes.is_dir():
        return names
    for manifest in episodes.glob("*.artifact.json"):
        video = episodes / f"{manifest.name.removesuffix('.artifact.json')}.mp4"
        artifact = read_artifact(video)
        if artifact and artifact.get("templateVersion") == active:
            names.add(video.name)
    return names


def thumbnail_path(
    episode: dict,
    platform: str = "vertical",
    root: Path = ROOT,
    design_variant: str = DEFAULT_DESIGN_VARIANT,
) -> Path:
    return (
        root
        / "out/thumbnails"
        / type_slug(episode["target"]["kind"])
        / design_variant
        / f"{video_stem(episode)}.{platform}.jpg"
    )


def choose_weighted_format(settings: dict) -> str:
    enabled = [
        format_id
        for format_id in FORMAT_DEFINITIONS
        if settings.get(format_id, {}).get("enabled", True)
    ]
    if not enabled:
        raise ValueError("Activá al menos un formato")
    return random.choices(
        enabled,
        weights=[max(1, int(settings.get(format_id, {}).get("priority", 1))) for format_id in enabled],
        k=1,
    )[0]


def priority_targets(settings: dict, total: int, format_ids=None) -> dict[str, int]:
    enabled = [
        format_id for format_id in (FORMAT_DEFINITIONS if format_ids is None else format_ids)
        if settings.get(format_id, {}).get("enabled", True)
    ]
    if not enabled or total <= 0:
        return {format_id: 0 for format_id in enabled}
    weights = {format_id: max(1, int(settings.get(format_id, {}).get("priority", 1))) for format_id in enabled}
    weight_total = sum(weights.values())
    quotas = {format_id: total * weights[format_id] / weight_total for format_id in enabled}
    targets = {format_id: int(quotas[format_id]) for format_id in enabled}
    order = {format_id: index for index, format_id in enumerate(enabled)}
    for format_id in sorted(
        enabled,
        key=lambda item: (quotas[item] - targets[item], weights[item], -order[item]),
        reverse=True,
    )[:total - sum(targets.values())]:
        targets[format_id] += 1
    return targets
