#!/usr/bin/env python3
"""Regression checks for isolated render props, manifests, and promotion."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from migrate_compatible_artifacts import migrate
from template_artifacts import (
    activate_template_version,
    artifact_path,
    render_props_path,
    validate_artifact,
    write_artifact,
    write_legacy_artifact,
    release_version,
)
from video_formats import current_template_video_names

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    fixture = ROOT / "out/test-template-artifacts"
    shutil.rmtree(fixture, ignore_errors=True)
    try:
        video = fixture / "out/episodes/mc-01-test.mp4"
        thumbnail = fixture / "out/thumbnails/item/default/mc-01-test.vertical.jpg"
        config = {"answer": {"id": "test"}, "timeline": {"contentStartFrame": 30}}
        video.parent.mkdir(parents=True)
        thumbnail.parent.mkdir(parents=True)
        video.write_bytes(b"video-release-a")
        thumbnail.write_bytes(b"thumbnail-release-a")
        props = render_props_path(video.stem, "video", fixture)
        props.parent.mkdir(parents=True, exist_ok=True)
        props.write_text(json.dumps({"config": config}), encoding="utf-8")

        previous = os.environ.get("WHATAMICRAFT_TEMPLATE_VERSION")
        os.environ.pop("WHATAMICRAFT_TEMPLATE_VERSION", None)
        (fixture / "out/.release-version").parent.mkdir(parents=True, exist_ok=True)
        (fixture / "out/.release-version").write_text("release-file", encoding="utf-8")
        assert release_version(fixture) == "release-file"
        os.environ["WHATAMICRAFT_TEMPLATE_VERSION"] = "release-a"
        try:
            manifest = write_artifact(
                episode_id="mc-01",
                video=video,
                config=config,
                thumbnail=thumbnail,
                root=fixture,
            )
            assert manifest == artifact_path(video)
            assert validate_artifact(video, episode_id="mc-01", root=fixture)["templateVersion"] == "release-a"
            activate_template_version("release-a", fixture)
            assert current_template_video_names(fixture) == {video.name}

            legacy_video = fixture / "out/episodes/mc-02-legacy.mp4"
            legacy_thumbnail = fixture / "out/thumbnails/item/default/mc-02-legacy.vertical.jpg"
            legacy_video.write_bytes(b"legacy-video")
            legacy_thumbnail.write_bytes(b"legacy-thumbnail")
            write_legacy_artifact(
                episode_id="mc-02",
                video=legacy_video,
                thumbnail=legacy_thumbnail,
                root=fixture,
            )
            assert validate_artifact(legacy_video, episode_id="mc-02", root=fixture)["legacy"] is True
            assert current_template_video_names(fixture) == {video.name}

            assert migrate(video.parent, "release-b", lambda version: version == "release-a") == 1
            os.environ["WHATAMICRAFT_TEMPLATE_VERSION"] = "release-b"
            activate_template_version("release-b", fixture)
            assert current_template_video_names(fixture) == {video.name}
            assert validate_artifact(legacy_video, root=fixture)["templateVersion"] == "legacy"

            video.write_bytes(b"video-mutated")
            try:
                validate_artifact(video, episode_id="mc-01", root=fixture)
            except RuntimeError as error:
                assert "cambió" in str(error)
            else:
                raise AssertionError("modified video was accepted")
        finally:
            if previous is None:
                os.environ.pop("WHATAMICRAFT_TEMPLATE_VERSION", None)
            else:
                os.environ["WHATAMICRAFT_TEMPLATE_VERSION"] = previous
    finally:
        shutil.rmtree(fixture, ignore_errors=True)

    print("ok: template artifacts are isolated, hashed, and promoted explicitly")


if __name__ == "__main__":
    main()
