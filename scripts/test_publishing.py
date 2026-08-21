import shutil
import hashlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from publish_worker import generation_window_open, is_due
import publish as publish_script
from publishing.common import PublishRequest
from publishing.meta import _graph, _instagram_graph
from publishing.tiktok import _chunks
from review import storage
from dashboard.app import _pkce_challenge


def main() -> None:
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    assert "./out/thumbnails:/mnt/out/thumbnails:ro" in compose
    verifier = "a" * 43
    assert _pkce_challenge(verifier) == hashlib.sha256(verifier.encode("ascii")).hexdigest()
    assert _graph("me").startswith("https://graph.facebook.com/")
    assert _instagram_graph("me").startswith("https://graph.instagram.com/")
    small = 4 * 1024 * 1024
    assert _chunks(small) == (small, 1)
    chunk, count = _chunks(65 * 1024 * 1024)
    assert 5 * 1024 * 1024 <= chunk <= 64 * 1024 * 1024
    assert count == 6
    item = PublishRequest("mc-01", Path("video.mp4"), None, "Title", "Caption", ["minecraft", "shorts"])
    assert item.description == "Caption\n\n#minecraft #shorts"
    original_output_dir = publish_script.OUTPUT_DIR
    publish_script.OUTPUT_DIR = Path(__file__).resolve().parents[1] / "out/test-publish-selection/episodes"
    try:
        publish_script.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        episode = {"id": "mc-01", "target": {"id": "test"}}
        video = publish_script.video_for(episode)
        video.write_bytes(b"video")
        state = {
            "videos": {
                "mc-01": {
                    "sha256": publish_script.sha256(video),
                    "platforms": {"youtube": {}, "instagram": {}},
                }
            }
        }
        assert publish_script.already_published(episode, ["youtube", "instagram"], state)
        assert not publish_script.already_published(episode, ["youtube", "instagram", "tiktok"], state)
        video.write_bytes(b"changed")
        assert not publish_script.already_published(episode, ["youtube", "instagram"], state)
    finally:
        publish_script.OUTPUT_DIR = original_output_dir
        shutil.rmtree(Path(__file__).resolve().parents[1] / "out/test-publish-selection", ignore_errors=True)
    now = datetime(2026, 8, 5, tzinfo=timezone.utc)
    config = {"schedule": {"enabled": True}}
    assert is_due(config, {"nextRunAt": None}, now)
    assert not is_due({"schedule": {"enabled": False}}, {"nextRunAt": None}, now)
    assert not is_due(config, {"nextRunAt": (now + timedelta(minutes=1)).isoformat()}, now)
    assert is_due(config, {"nextRunAt": (now - timedelta(minutes=1)).isoformat()}, now)
    guarded = {"schedule": {"enabled": True}, "generation": {"publishGuardMinutes": 90}}
    assert generation_window_open(guarded, {"nextRunAt": (now + timedelta(minutes=91)).isoformat()}, now)
    assert not generation_window_open(guarded, {"nextRunAt": (now + timedelta(minutes=90)).isoformat()}, now)
    fixture = Path(__file__).resolve().parents[1] / "out/test-review-fixture"
    if fixture.exists():
        shutil.rmtree(fixture)
    try:
        (fixture / "data").mkdir(parents=True)
        (fixture / "out/episodes").mkdir(parents=True)
        (fixture / "public/audio/quiz-copy/mc-01").mkdir(parents=True)
        storage.ROOT = fixture
        storage.BANK_PATH = fixture / "data/quiz-copy-episodes.json"
        storage.HINTS_PENDING_PATH = fixture / "data/pending-hint-regenerations.json"
        storage.QUEUE_PATH = fixture / "out/publishing-queue.json"
        storage.PUBLISHING_STATE_PATH = fixture / "out/publishing-state.json"
        storage.write_json(
            storage.BANK_PATH,
            {
                "episodes": [
                    {
                        "id": "mc-01",
                        "needsReview": False,
                        "uniqueAnswer": True,
                        "answer": {"id": "test", "displayName": "Test", "guessType": "Item"},
                        "clues": [{"text": "One"}, {"text": "Two"}, {"text": "Three"}],
                    }
                ]
            },
        )
        (fixture / "out/episodes/mc-01-test.mp4").write_bytes(b"video")
        (fixture / "public/audio/quiz-copy/mc-01/clue.mp3").write_bytes(b"audio")
        storage.queue_episode("mc-01")
        assert storage.pending_queue_ids() == ["mc-01"]
        storage.set_queue_status("mc-01", "completed")
        assert storage.pending_queue_ids() == []
        storage.pend_hints("mc-01")
        assert storage.read_json(storage.BANK_PATH)["episodes"][0]["needsReview"] is True
        assert storage.pending_hints_items()[0]["episodeId"] == "mc-01"
        storage.reject_episode("mc-01")
        assert storage.read_json(storage.BANK_PATH)["episodes"] == []
        assert not list((fixture / "out/episodes").glob("mc-01-*.mp4"))
        assert not (fixture / "public/audio/quiz-copy/mc-01").exists()
    finally:
        if fixture.exists():
            shutil.rmtree(fixture)
    print("publishing: ok")


if __name__ == "__main__":
    main()
