from pathlib import Path
from types import SimpleNamespace

import music_library as library
from music_library import CLIP_DURATION_SECONDS, parse_start, validate_starts, validate_youtube_url, youtube_video_id
import produce_quiz_copy as producer


assert validate_youtube_url("https://youtu.be/abc123") == "https://youtu.be/abc123"
assert youtube_video_id("https://www.youtube.com/watch?v=WZaSMbDzYyY") == "WZaSMbDzYyY"
assert youtube_video_id("https://youtu.be/WZaSMbDzYyY") == "WZaSMbDzYyY"
assert youtube_video_id("https://www.youtube.com/shorts/WZaSMbDzYyY") == "WZaSMbDzYyY"
assert parse_start("1:15") == 75
assert parse_start("1:02:03.5") == 3723.5
assert validate_starts(["0:32", "1:15", "0:32"]) == [32, 75]
assert CLIP_DURATION_SECONDS == 120

fragment_calls = []
original_fragment = library._fragment
library._fragment = lambda source, destination, start, duration: fragment_calls.append(duration)
test_track = {"id": "test", "clips": []}
library._add_clips(test_track, Path("."), [32], ["clues"], 180)
library._fragment = original_fragment
assert fragment_calls == [120] and test_track["clips"][0]["durationSeconds"] == 120

downloaded_test = library.ROOT / "out/download.webm"
converted_test = library.ROOT / "out/source.m4a"
downloaded_test.unlink(missing_ok=True)
converted_test.unlink(missing_ok=True)
download_commands = []
download_attempts = 0
original_run, original_ffmpeg_dir = library._run, library._ffmpeg_dir
try:
    def fake_download_run(command, **kwargs):
        global download_attempts
        download_commands.append(command)
        if command[0] == "yt-dlp":
            download_attempts += 1
            if download_attempts == 1:
                raise RuntimeError("HTTP Error 403")
            downloaded_test.write_bytes(b"audio")
        else:
            Path(command[-1]).write_bytes(b"audio")
        return SimpleNamespace(stdout='{"id":"abc123","duration":180}')
    library._run = fake_download_run
    library._ffmpeg_dir = lambda: Path("ffmpeg-bin")
    library._download("https://youtu.be/abc123", library.ROOT / "out")
    assert all(option in download_commands[0] for option in ("--js-runtimes", "prefer-legacy-http-handler", "youtube:player_client=android_vr"))
    assert download_commands[0][download_commands[0].index("-f") + 1] == "bestaudio[ext=m4a]"
    assert download_commands[1][download_commands[1].index("-f") + 1] == "139"
    assert "-x" not in download_commands[0]
    assert download_commands[2][-3:-1] == ["-f", "mp4"]
    assert converted_test.exists() and not downloaded_test.exists()
finally:
    library._run, library._ffmpeg_dir = original_run, original_ffmpeg_dir
    downloaded_test.unlink(missing_ok=True)
    converted_test.unlink(missing_ok=True)

test_library_path = library.ROOT / "out/test-music-library.json"
test_library_path.unlink(missing_ok=True)
test_library_path.with_suffix(".json.tmp").unlink(missing_ok=True)
original_library_path, original_run = library.LIBRARY_PATH, library._run
try:
    library.LIBRARY_PATH = test_library_path
    library._run = lambda *args, **kwargs: SimpleNamespace(stdout="185.0\n")
    assert library.set_original_starts("Cat.ogg", ["0:12", "0:34"]) == [12, 34]
    assert library.original_starts("Cat.ogg") == [12, 34]
finally:
    library.LIBRARY_PATH, library._run = original_library_path, original_run
    test_library_path.unlink(missing_ok=True)
    test_library_path.with_suffix(".json.tmp").unlink(missing_ok=True)

for invalid in ("https://example.com/watch?v=abc", "http://youtube.com/watch?v=abc"):
    try:
        validate_youtube_url(invalid)
        raise AssertionError("accepted an invalid URL")
    except ValueError:
        pass

producer.ready_clips_for_template = lambda _: [{
    "publicSrc": "audio/music/Cat.ogg", "title": "Cat", "url": "https://youtu.be/abc123", "startSeconds": 32,
}]
producer.normalize_audio = lambda *args: "audio/quiz-copy/music-cache/test.m4a"
producer.random.SystemRandom = lambda: type("FirstChoice", (), {"choice": lambda self, values: values[0]})()
music = producer.prepare_music({
    "folder": "public/audio/music", "targetLufs": -16, "truePeakDb": -1.5, "loudnessRange": 11,
    "volume": .16, "duckedVolume": .07, "fadeInFrames": 24, "fadeOutFrames": 36, "duckFadeFrames": 6,
}, True)
assert music["sourceName"] == "Cat @ 32s" and music["from"] == 0 and music["trackCount"] == 8

normalization = {}
producer.ready_clips_for_template = lambda _: []
producer.original_starts = lambda _: [12, 34]
producer.normalize_audio = lambda source, cache, settings, dry_run: normalization.update(settings) or "audio/quiz-copy/music-cache/test.m4a"
music = producer.prepare_music({
    "folder": "public/audio/music", "targetLufs": -16, "truePeakDb": -1.5, "loudnessRange": 11,
    "volume": .16, "duckedVolume": .07, "fadeInFrames": 24, "fadeOutFrames": 36, "duckFadeFrames": 6,
}, True)
assert music["sourceName"] == "Cat.ogg @ 12s" and music["trackCount"] == 14
assert normalization["trimStartSeconds"] == 12 and normalization["trimDurationSeconds"] == 120

print("ok: music library timestamps and URL guards")
