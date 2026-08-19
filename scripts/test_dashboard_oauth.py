#!/usr/bin/env python3
import os
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))
import app  # noqa: E402


class DashboardMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.views = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        if values.get("data-view-panel"):
            self.views.append(values["data-view-panel"])


markup = DashboardMarkup()
markup.feed((ROOT / "dashboard/index.html").read_text(encoding="utf-8"))
assert len(markup.ids) == len(set(markup.ids))
assert set(markup.views) == {"home", "videos", "music", "analytics", "publishing", "system"}
assert {"music-url", "music-starts", "music-templates", "music-rights", "music-import", "music-tracks"} <= set(markup.ids)
assert {"generated-new", "legacy-videos", "episodes-to-generate"} <= set(markup.ids)
state = app.dashboard_state()
legacy_ids = {item["id"] for item in state["legacyVideos"]}
assert not any(item["id"] in legacy_ids for item in state["toGenerate"])

os.environ["YOUTUBE_CLIENT_ID"] = "client"
os.environ["YOUTUBE_CLIENT_SECRET"] = "secret"
app.apply_runtime = lambda: None
url = urlparse(app.youtube_connect_url())
query = parse_qs(url.query)
assert query["redirect_uri"] == [app.YOUTUBE_REDIRECT_URI]
assert app.YOUTUBE_SCOPES == set(query["scope"][0].split())

saved = {}
app.json_request = lambda *args, **kwargs: ({"refresh_token": "refresh"}, {})
app.save_secrets = saved.update
app.complete_youtube_login({"state": query["state"], "code": ["code"]})
assert saved == {"YOUTUBE_REFRESH_TOKEN": "refresh"}
print("ok: dashboard oauth")
