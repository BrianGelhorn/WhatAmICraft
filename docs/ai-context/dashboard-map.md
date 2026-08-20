# Dashboard map

- `dashboard/app.py`: HTTP API, jobs, diagnostics, OAuth and analytics proxy; synchronization lives in `scripts/analytics_service.py` when `ANALYTICS_API_URL` is configured.
- `dashboard/index.html`: dashboard UI and the three-format thumbnail preview.
- `scripts/produce_quiz_copy.py`: definitive Remotion producer.
- `scripts/publish_worker.py`: scheduler.
- `scripts/publish.py`: platform publisher.
- `scripts/state_db.py`: SQLite state.

Important routes: `/api/state`, `/api/diagnostics`, `/api/generate`, `/api/action`, `/api/publish-now`, `/api/publish-platform`, `/api/publishing/config`, `/api/analytics/sync`, and `/api/analytics/export.json`.

Keep the dashboard dependency-free: one Python server and one HTML file.
