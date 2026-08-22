#!/usr/bin/env python3
import json
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import analytics_service  # noqa: E402


def call(base: str, path: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    body = json.dumps(payload).encode() if payload is not None else None
    try:
        with urlopen(Request(f"{base}{path}", data=body, headers={"Content-Type": "application/json"} if body else {}, method=method), timeout=5) as response:
            return response.status, json.loads(response.read() or b"{}")
    except Exception as error:
        if hasattr(error, "code"):
            return error.code, json.loads(error.read() or b"{}")
        raise


def main() -> None:
    service = analytics_service.AnalyticsService()
    expected = {
        "schemaVersion": 1,
        "summary": {"videos": 2, "views": 120, "engagements": 18},
        "platforms": [{"platform": "youtube", "videos": 1}, {"platform": "instagram", "videos": 1}],
    }
    sync_calls = []
    analytics_service.analytics.build_snapshot = lambda: expected  # type: ignore[assignment]
    analytics_service.analytics.write_exports = lambda: expected  # type: ignore[assignment]
    analytics_service.analytics.sync_all = lambda: sync_calls.append("synced")  # type: ignore[assignment]
    analytics_service.state_db.load_flag = lambda *_args: {"youtube": {"synced": 1}}  # type: ignore[assignment]
    analytics_service.state_db.set_analytics_recommendation_status = lambda recommendation_id, status: {"id": recommendation_id, "status": status}  # type: ignore[assignment]
    analytics_service.state_db.create_analytics_experiment = lambda recommendation_id, minimum_videos: {"id": "exp:" + recommendation_id, "minimumVideos": minimum_videos}  # type: ignore[assignment]
    analytics_service.analytics.import_trend_signals = lambda payload: payload.get("signals", [])  # type: ignore[assignment]
    analytics_service.analytics.sync_trend_signals = lambda: {"configured": True, "synced": 2, "error": None}  # type: ignore[assignment]
    server = analytics_service.make_server("127.0.0.1", 0, service)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        health_status, health = call(base, "/health")
        assert health_status == 200 and health["service"] == "analytics-api"
        snapshot_status, snapshot = call(base, "/api/analytics")
        assert snapshot_status == 200 and snapshot["summary"]["views"] == 120
        sync_status, sync = call(base, "/api/analytics/sync", "POST")
        assert sync_status == 202 and sync["sync"]["status"] in {"running", "completed"}
        for _ in range(20):
            if service.sync_status()["status"] != "running":
                break
            time.sleep(0.01)
        assert sync_calls == ["synced"] and service.sync_status()["status"] == "completed"
        recommendation_status, recommendation = call(base, "/api/analytics/recommendation", "POST", {"id": "fixture", "status": "applied"})
        assert recommendation_status == 200 and recommendation["recommendation"]["status"] == "applied"
        started_status, started = call(base, "/api/analytics/recommendation", "POST", {"id": "fixture", "status": "applied", "startExperiment": True, "minimumVideos": 4})
        assert started_status == 200 and started["experiment"]["minimumVideos"] == 4
        trend_status, trends = call(base, "/api/analytics/trends", "POST", {"signals": []})
        assert trend_status == 200 and trends["signals"] == []
        trend_sync_status, trend_sync = call(base, "/api/analytics/trends/sync", "POST", {})
        assert trend_sync_status == 200 and trend_sync["sync"]["synced"] == 2
        invalid_status, _ = call(base, "/api/analytics/unknown")
        assert invalid_status == 404
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
    print("ok: analytics API snapshot, sync lifecycle, and route guards")


if __name__ == "__main__":
    main()
