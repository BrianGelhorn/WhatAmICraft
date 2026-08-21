#!/usr/bin/env python3
"""Checks thumbnail placement, vertical routing, and publisher selection."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import publish
import thumbnails
from video_formats import all_episodes, thumbnail_path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    episodes = all_episodes()
    assert episodes
    for answer_type in thumbnails.type_names():
        assert thumbnails.type_thumbnail_path(answer_type, "vertical").is_file()
    for episode in episodes:
        path = thumbnail_path(episode, "vertical")
        expected_type = episode["target"]["kind"].replace(" ", "_")
        assert path.parent.parent.name == expected_type
        assert path.name == f"{episode['id']}-{episode['target']['id']}.vertical.jpg"
        assert path.suffix == ".jpg"
        assert "horizontal" not in path.as_posix() and "square" not in path.as_posix()

    episode = next(item for item in episodes if item["id"] == "mc-03")
    config = thumbnails.copy_thumbnail_config(episode)
    thumbnails.validate_config(config)
    expected = ROOT / "out/thumbnails/item/default/mc-ci-wind-charge.vertical.jpg"
    calls: list[list[str]] = []
    original_run = thumbnails.subprocess.run
    original_write_config = thumbnails.write_config
    try:
        thumbnails.subprocess.run = lambda command, **_kwargs: calls.append(command)  # type: ignore[assignment]
        thumbnails.write_config = lambda _config: None
        thumbnails.render_thumbnails(config, "mc-ci-wind-charge")
        assert calls
        assert calls[0][calls[0].index("still") + 1] == "ThumbnailVertical"
        assert calls[0][calls[0].index("still") + 2] == str(expected)
        props_arg = next(argument for argument in calls[0] if argument.startswith("--props="))
        props = json.loads(props_arg[len("--props="):])
        assert props == {"variant": "silhouette"}
    finally:
        thumbnails.subprocess.run = original_run
        thumbnails.write_config = original_write_config
        expected.unlink(missing_ok=True)

    original_thumbnail_path = publish.thumbnail_path
    episode_thumbnail = thumbnail_path(episode, "vertical")
    episode_thumbnail.parent.mkdir(parents=True, exist_ok=True)
    episode_thumbnail.write_bytes(b"thumbnail-fixture")
    try:
        publish.thumbnail_path = lambda _episode, platform="vertical": thumbnail_path(episode, platform)
        request = publish.publish_request(
            episode,
            {"title": "Guess {kind}", "caption": "Guess it", "hashtags": ["minecraft"]},
        )
        assert request.thumbnail == thumbnail_path(episode, "vertical")
        assert request.thumbnail != thumbnail_path(episode, "square")
    finally:
        publish.thumbnail_path = original_thumbnail_path
        episode_thumbnail.unlink(missing_ok=True)

    invalid = deepcopy(config)
    invalid["thumbnail"]["platforms"]["vertical"] = "unknown"
    try:
        thumbnails.validate_config(invalid)
    except RuntimeError as error:
        assert "variante" in str(error)
    else:
        raise AssertionError("invalid thumbnail variant was accepted")

    print("ok: thumbnail type paths, vertical render routing, publisher selection, and validation")


if __name__ == "__main__":
    main()
