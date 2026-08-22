#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import analytics  # noqa: E402
import state_db  # noqa: E402


now = datetime(2026, 8, 22, 12, 30, tzinfo=timezone.utc)
analytics.all_episodes = lambda: [{
    "id": "mc-99", "format": "clues",
    "target": {"id": "stone", "display_name": "Stone"},
}]
analytics.publishing_state = lambda: {"videos": {"mc-99": {"platforms": {"tiktok": {
    "publishedAt": (now - timedelta(hours=2)).isoformat(),
}}}}}
analytics.video_path = lambda episode: Path("missing.mp4")
analytics.video_metrics = lambda: [{
    "episodeId": "mc-99", "platform": "tiktok", "videoId": "123", "title": "Pilot",
    "shareUrl": "https://example.test", "createTime": 0, "views": 100, "likes": 10,
    "comments": 2, "shares": 1, "saves": None, "reach": None,
    "watchTimeSeconds": None, "averageWatchSeconds": None, "completionRate": None,
    "raw": {"availableMetrics": ["views", "likes", "comments", "shares"]},
    "updatedAt": now.isoformat(),
}]
analytics.video_metric_snapshots = lambda: [
    {"episodeId": "mc-99", "platform": "tiktok", "views": 100, "likes": 10, "comments": 2, "shares": 1, "capturedAt": (now + timedelta(minutes=15)).isoformat()},
    {"episodeId": "mc-99", "platform": "tiktok", "views": 90, "likes": 9, "comments": 2, "shares": 1, "capturedAt": now.isoformat()},
    {"episodeId": "mc-99", "platform": "tiktok", "views": 80, "likes": 8, "comments": 1, "shares": 1, "capturedAt": (now - timedelta(hours=1)).isoformat()},
]
analytics.state_db.load_flag = lambda key, default: {"tiktok": {"configured": True, "synced": 1, "error": None}} if key == "analytics_sync_status" else default

snapshot = analytics.build_snapshot()
assert snapshot["summary"] == {"videos": 1, "views": 100, "engagements": 13, "engagementRateByViews": 13.0}
assert snapshot["videos"][0]["viewsPerHourSincePrevious"] == 40
assert snapshot["videos"][0]["averageWatchSeconds"] is None
assert [point["views"] for point in snapshot["series"]] == [80, 100]
assert [point["engagements"] for point in snapshot["series"]] == [10, 13]
assert snapshot["cohorts"][0]["dimension"] == "formatLabel"
assert snapshot["cohorts"][0]["viewsPerVideo"] == 100
quality = {item["platform"]: item for item in snapshot["quality"]}
assert quality["tiktok"]["coveragePercent"] == 100.0
assert snapshot["trends"][1]["trend"] == "up"
assert snapshot["alerts"] == []
assert snapshot["recommendations"][0]["dimension"] == "trend"
assert snapshot["cohorts"]
assert snapshot["cohorts"][0]["sampleConfidence"] == "low"
assert snapshot["cohorts"][0]["baselineViewsPerVideo"] is not None
assert snapshot["cohorts"][0]["sampleWarning"]
assert snapshot["trendSignals"] == []

signals = analytics.validate_trend_signals({"signals": [{"platform": "youtube", "kind": "topic", "value": "Minecraft", "source": "fixture"}]})
assert signals[0]["platform"] == "youtube"
try:
    analytics.validate_trend_signals({"signals": [{"platform": "other", "kind": "topic", "value": "bad", "source": "fixture"}]})
except ValueError:
    pass
else:
    raise AssertionError("invalid trend signal accepted")

class FakeTrendResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return b'{"signals":[{"platform":"youtube","kind":"topic","value":"Live Minecraft","source":"fixture"}]}'

old_trends_url = os.environ.get("ANALYTICS_TRENDS_URL")
old_urlopen = analytics.urllib.request.urlopen
old_save_flag = analytics.state_db.save_flag
saved_trend_status = []
try:
    os.environ["ANALYTICS_TRENDS_URL"] = "https://trends.example.test/feed"
    analytics.urllib.request.urlopen = lambda *_args, **_kwargs: FakeTrendResponse()
    analytics.state_db.save_flag = lambda key, value: saved_trend_status.append((key, value))
    live_status = analytics.sync_trend_signals()
    assert live_status["synced"] == 1 and [item[0] for item in saved_trend_status] == ["analytics_trend_signals", "analytics_trend_sync_status"]
finally:
    analytics.urllib.request.urlopen = old_urlopen
    analytics.state_db.save_flag = old_save_flag
    if old_trends_url is None:
        os.environ.pop("ANALYTICS_TRENDS_URL", None)
    else:
        os.environ["ANALYTICS_TRENDS_URL"] = old_trends_url

experiment_db = ROOT / "out/test-analytics-experiments.sqlite3"
for suffix in ("", "-wal", "-shm"):
    experiment_db.with_name(experiment_db.name + suffix).unlink(missing_ok=True)
recommendation = state_db.save_analytics_recommendation({
    "id": "fixture:formatLabel:Quiz", "platform": "youtube", "dimension": "formatLabel", "value": "Quiz",
    "action": "Probar Quiz", "reason": "fixture", "priority": "high",
}, experiment_db)
experiment = state_db.create_analytics_experiment(recommendation["id"], 2, experiment_db)
assert experiment["status"] == "running" and experiment["variantValue"] == "Quiz"
assert state_db.set_analytics_experiment_status(experiment["id"], "completed", experiment_db)["status"] == "completed"
old_experiments = analytics.state_db.analytics_experiments
analytics.state_db.analytics_experiments = lambda: [experiment]
try:
    experiment_rows = analytics._build_experiments([
        {"platform": "youtube", "formatLabel": "Quiz", "views": 120, "engagements": 12},
        {"platform": "youtube", "formatLabel": "Quiz", "views": 100, "engagements": 10},
        {"platform": "youtube", "formatLabel": "Other", "views": 80, "engagements": 8},
        {"platform": "youtube", "formatLabel": "Other", "views": 70, "engagements": 7},
    ])
    assert experiment_rows[0]["sampleStatus"] == "ready"
    assert experiment_rows[0]["liftPct"] > 0
finally:
    analytics.state_db.analytics_experiments = old_experiments
for suffix in ("", "-wal", "-shm"):
    experiment_db.with_name(experiment_db.name + suffix).unlink(missing_ok=True)

props_path = ROOT / "out/test-analytics-props.json"
props_path.write_text('{"config":{"music":{"sourceName":"Fixture track @ 12s"}}}', encoding="utf-8")
old_read_artifact = analytics.read_artifact
analytics.read_artifact = lambda _video: {"templateVersion": "fixture-template", "configPath": "out/test-analytics-props.json"}
try:
    metadata = analytics._creative_metadata(
        {"format": "clues", "target": {"kind": "food"}},
        now.isoformat(),
        {"publishedTitle": "Guess Food", "publishedCaption": "Can you guess it?", "publishedHashtags": ["shorts"]},
    )
    assert metadata["musicSource"] == "Fixture track @ 12s"
    assert metadata["templateVersion"] == "fixture-template"
    assert metadata["publishedTitle"] == "Guess Food"
    assert metadata["publishedHashtags"] == ["shorts"]
finally:
    analytics.read_artifact = old_read_artifact
    props_path.unlink(missing_ok=True)

export_root = ROOT / "out/test-analytics-export"
export_root.mkdir(parents=True, exist_ok=True)
old_export_dir = analytics.EXPORT_DIR
analytics.EXPORT_DIR = export_root
try:
    analytics.write_exports(snapshot)
    export = (export_root / "gpt-analytics.md").read_text(encoding="utf-8")
    assert "## Recommendations" in export
    assert "## Data quality" in export
finally:
    analytics.EXPORT_DIR = old_export_dir
    for path in export_root.glob("*"):
        path.unlink(missing_ok=True)
    export_root.rmdir()
assert "raw" not in snapshot["videos"][0]
assert [len(batch) for batch in analytics._chunks(list(range(41)), 20)] == [20, 20, 1]

database = ROOT / "out/test-dashboard-analytics.sqlite3"
database.unlink(missing_ok=True)
try:
    state_db.set_video_metrics("mc-99", "tiktok", {
        "id": "123", "views": 100, "likes": 10, "comments": 2, "shares": 1,
        "saves": 3, "averageWatchSeconds": 4.5, "raw": {"availableMetrics": ["views"]},
    }, database)
    state_db.set_video_metrics("mc-99", "tiktok", {
        "id": "123", "views": 120, "likes": 11, "comments": 2, "shares": 1,
    }, database)
    assert state_db.video_metrics(database)[0]["views"] == 120
    assert len(state_db.video_metric_snapshots(database)) == 2
finally:
    for path in database.parent.glob(database.name + "*"):
        path.unlink(missing_ok=True)

print("ok: dashboard analytics")
