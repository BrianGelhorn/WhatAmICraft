#!/usr/bin/env python3
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
    {"episodeId": "mc-99", "platform": "tiktok", "views": 100, "likes": 10, "comments": 2, "shares": 1, "capturedAt": now.isoformat()},
    {"episodeId": "mc-99", "platform": "tiktok", "views": 80, "likes": 8, "comments": 1, "shares": 1, "capturedAt": (now - timedelta(hours=1)).isoformat()},
]
analytics.state_db.load_flag = lambda *args: {"tiktok": {"configured": True, "synced": 1, "error": None}}

snapshot = analytics.build_snapshot()
assert snapshot["summary"] == {"videos": 1, "views": 100, "engagements": 13, "engagementRateByViews": 13.0}
assert snapshot["videos"][0]["viewsPerHourSincePrevious"] == 20
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
