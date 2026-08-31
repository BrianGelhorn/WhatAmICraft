#!/usr/bin/env python3
"""Real artifacts/SQLite/publication flow across an operational deploy and retries."""

import argparse
import copy
import json
import tempfile
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import job_status
import publish
import publish_worker as worker
import state_db
import video_formats
from migrate_compatible_artifacts import migrate
from publishing import settings
from review import storage
from template_artifacts import render_props_path, write_artifact


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
        root = Path(temporary)
        stack.enter_context(patch.dict("os.environ", {"WHATAMICRAFT_TEMPLATE_VERSION": "release-b"}))
        for module in (storage, settings):
            old_root = module.ROOT
            for name, value in vars(module).copy().items():
                if isinstance(value, Path) and value.is_relative_to(old_root):
                    stack.enter_context(patch.object(module, name, root / value.relative_to(old_root)))
        paths = {lane: root / f"out/{lane}-job.json" for lane in job_status.JOB_PATHS}
        stack.enter_context(patch.object(job_status, "JOB_PATHS", paths))
        for module in (worker, publish):
            stack.enter_context(patch.object(module, "ROOT", root))
            stack.enter_context(patch.object(module, "OUTPUT_DIR", root / "out/episodes"))
        stack.enter_context(patch.object(worker, "LOG_DIR", root / "out/logs"))
        stack.enter_context(patch.object(worker, "PUBLISH_LOCK", root / "out/publishing.lock"))
        discard_manifest = worker.discard_invalid_audio_manifest
        stack.enter_context(patch.object(worker, "discard_invalid_audio_manifest", lambda episode_id: discard_manifest(episode_id, root)))
        episodes = [{"id": f"mc-{number}", "format": "clues", "target": {
            "id": f"target-{number}", "kind": "item", "display_name": f"Target {number}",
        }} for number in range(65, 73)]
        old, corrupt, unapproved, approved, rejected, missing, fresh, legacy = episodes
        for episode in episodes:
            if episode in (missing, fresh):
                continue
            video = video_formats.video_path(episode, root)
            video.parent.mkdir(parents=True, exist_ok=True)
            video.write_bytes(episode["id"].encode())
            thumbnail = root / f"out/thumbnails/{episode['id']}.jpg"
            thumbnail.parent.mkdir(parents=True, exist_ok=True)
            thumbnail.write_bytes(b"thumbnail")
            props = render_props_path(video.stem, "video", root)
            props.parent.mkdir(parents=True, exist_ok=True)
            props.write_text('{"config": {}}')
            manifest = write_artifact(episode_id=episode["id"], video=video, config={}, thumbnail=thumbnail, root=root)
            artifact = json.loads(manifest.read_text())
            artifact["templateVersion"] = "old-template" if episode == old else "release-a"
            if episode == legacy:
                artifact.update(templateVersion="legacy", legacy=True)
            manifest.write_text(json.dumps(artifact))
            if episode == corrupt:
                video.write_bytes(b"changed after approval")
        (root / "out/.active-template-version").write_text("release-b")
        for module in (worker, publish):
            stack.enter_context(patch.object(module, "episodes", lambda: episodes))
        stack.enter_context(patch.object(worker, "video_for", lambda episode: video_formats.video_path(episode, root)))
        stack.enter_context(patch.object(worker, "current_template_video_names", lambda: video_formats.current_template_video_names(root)))
        db = storage.state_db_path()
        # Approval existed before the deploy; candidates and rejections must stay untouched.
        for episode in (old, corrupt, approved, missing, legacy):
            state_db.upsert_queue_item(episode["id"], db_path=db)
        state_db.upsert_queue_item(rejected["id"], "failed", "Rejected by reviewer", db)
        instagram = {"id": "already-published", "publishedAt": "2026-08-30T07:36:21+00:00"}
        storage.save_published_platform(approved["id"], publish.sha256(worker.video_for(approved)), "instagram", instagram)
        assert not worker.inventory()["pending"]  # Reproduces the old deploy demotion.
        queued_at = {row["episodeId"]: row["queuedAt"] for row in storage.queue_items()}
        migrate(root / "out/episodes", "release-b", lambda version: version == "release-a")
        stock = worker.inventory()
        assert stock["pending"] == [approved["id"]], "restore only valid, previously approved current artifacts"
        assert old["id"] in stock["legacy"] and legacy["id"] in stock["legacy"]
        assert not set((approved["id"], old["id"], legacy["id"])).intersection(stock["missing"])
        assert {row["episodeId"]: row["queuedAt"] for row in storage.queue_items()} == queued_at
        assert storage.publishing_state()["videos"][approved["id"]]["platforms"]["instagram"] == instagram

        config = copy.deepcopy(settings.DEFAULT_CONFIG)
        config["schedule"].update(enabled=True)
        for name, platform in config["platforms"].items():
            platform["enabled"] = name in ("youtube", "instagram")
        for module in (worker, publish):
            stack.enter_context(patch.object(module, "load_config", lambda: config))
            stack.enter_context(patch.object(module, "apply_runtime", lambda _config: None))
        stack.enter_context(patch.object(worker, "alert_low_stock", lambda *_args: None))
        stack.enter_context(patch.object(publish, "ensure_thumbnail", lambda _episode: root / "out/thumbnails/mc-68.jpg"))
        calls = []

        def youtube(_item):
            calls.append("youtube")
            raise RuntimeError("invalid_grant: Token has been expired or revoked")

        stack.enter_context(patch.object(publish, "PUBLISHERS", {
            "youtube": youtube, "instagram": lambda _item: calls.append("instagram"),
        }))
        generated = []

        def run_logged(command, _log, label, lane):
            job_status.begin_job(label, "automatic", lane=lane)
            if lane == "publishing":
                assert "--queue" in command and "--force" not in command
                code = publish.run(argparse.Namespace(episode=None, queue=True, platform=None, limit=1, force=False, dry_run=False))
            else:
                generated.append(command[command.index("--episode") + 1])
                code = 0
            job_status.finish_job("completed" if code == 0 else "failed", code, lane=lane)
            return SimpleNamespace(returncode=code)

        stack.enter_context(patch.object(worker, "run_logged", run_logged))
        stack.enter_context(patch.object(worker.time, "sleep", side_effect=KeyboardInterrupt))

        def tick():
            try:
                worker.main()
            except KeyboardInterrupt:
                pass

        settings.save_schedule(settings.next_run_iso(-1))
        settings.save_generation_schedule(settings.next_run_iso(-1))
        tick()
        assert calls == ["youtube"], "partial retry must not duplicate Instagram"
        assert storage.pending_queue_ids() == [approved["id"]]
        assert "invalid_grant" in next(row for row in storage.queue_items() if row["episodeId"] == approved["id"])["error"]
        due = datetime.fromisoformat(settings.load_schedule()["nextRunAt"])
        assert datetime.now(timezone.utc) < due < datetime.now(timezone.utc) + timedelta(minutes=16)
        tick()  # A new worker invocation must generate during the persisted retry cooldown.
        assert generated, "15-minute retries must not starve generation behind the 90-minute guard"
        assert set(generated).issubset({missing["id"], fresh["id"]}), "never regenerate existing/legacy videos"

        # Failed manual jobs and successful scheduled publications keep the normal guard.
        for source, status in (("manual", "failed"), ("automatic", "completed")):
            job_status.begin_job("publish", source, lane="publishing")
            job_status.finish_job(status, 1 if status == "failed" else 0, lane="publishing")
            assert not worker.generation_window_open(config, settings.load_schedule())
        job_status.begin_job("publish", "automatic", lane="publishing")
        job_status.finish_job("failed", 1, lane="publishing")
        assert not worker.generation_window_open(config, {"nextRunAt": settings.next_run_iso(-1)})
        assert not worker.generation_window_open(config, {"nextRunAt": None})
        before = len(generated)
        worker.PUBLISH_LOCK.mkdir()
        settings.save_generation_schedule(settings.next_run_iso(-1))
        worker.maybe_generate(config, stock)
        assert len(generated) == before, "retry relaxation must not bypass an active publishing lock"
        worker.PUBLISH_LOCK.rmdir()

        publish.PUBLISHERS["youtube"] = lambda _item: {"id": "reconnected-youtube"}
        settings.save_schedule(settings.next_run_iso(-1))
        tick()
        assert not storage.pending_queue_ids(), "complete only after every enabled platform succeeds"
        assert storage.publishing_state()["videos"][approved["id"]]["platforms"]["instagram"] == instagram
        settings.save_schedule(settings.next_run_iso(15))
        assert not worker.generation_window_open(config, settings.load_schedule()), "successful publish restores normal guard"
        assert worker.generation_window_open(config, {"nextRunAt": settings.next_run_iso(120)})
    print("ok: deployment recovery preserves approvals, legacy exclusions, idempotency and generation during retries")


if __name__ == "__main__":
    main()
