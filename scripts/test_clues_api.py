#!/usr/bin/env python3
import json
import os
import shutil
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from clues_api import ClueCatalog, make_server  # noqa: E402
from clues_client import get_clue, list_clues, upload_clue  # noqa: E402
sys.path.insert(0, str(ROOT / "dashboard"))
import app as dashboard_app  # noqa: E402


def call(base: str, path: str, method: str = "GET", value: dict | None = None) -> tuple[int, dict]:
    body = json.dumps(value).encode() if value is not None else None
    try:
        with urlopen(Request(f"{base}{path}", data=body, headers={"Content-Type": "application/json"}, method=method), timeout=5) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        return error.code, json.loads(error.read())


def upload_fixture() -> dict:
    return {
        "episode": {
            "target": {"id": "ci_clue", "display_name": "CI Clue", "edition": "java", "version": "1.21.5", "kind": "item", "family": "test item"},
            "mode": "open_answer",
            "difficulty": "medium",
            "clue_count": 3,
            "clue_count_reason": "Three facts narrow the test candidates.",
            "candidates": ["ci_clue", "rival_one", "rival_two"],
            "facts": [
                {"id": "f_1", "scope": "family", "source_type": "minecraft-data", "source": "ci", "verified": True, "relation": "family", "semantic_key": "ci-family", "matches_candidates": ["ci_clue", "rival_one", "rival_two"]},
                {"id": "f_2", "scope": "target", "source_type": "wiki", "source": "https://example.test/f2", "verified": True, "relation": "use", "semantic_key": "ci-use", "matches_candidates": ["ci_clue", "rival_one"]},
                {"id": "f_3", "scope": "target", "source_type": "wiki", "source": "https://example.test/f3", "verified": True, "relation": "obtain", "semantic_key": "ci-obtain", "matches_candidates": ["ci_clue", "rival_two"]},
            ],
            "clues": [
                {"order": 1, "text": "Test clue 1", "referent": "target", "fact_ids": ["f_1"], "matches_candidates": ["ci_clue", "rival_one", "rival_two"]},
                {"order": 2, "text": "Test clue 2", "referent": "target", "fact_ids": ["f_2"], "matches_candidates": ["ci_clue", "rival_one"]},
                {"order": 3, "text": "Test clue 3", "referent": "target", "fact_ids": ["f_3"], "matches_candidates": ["ci_clue", "rival_two"]},
            ],
            "remaining_after_each_clue": [3, 2, 1],
            "sources": [{"title": "CI source", "url": "https://example.test/clue"}],
            "unique_answer": True,
            "needs_review": False,
        }
    }


def main() -> None:
    fixture = ROOT / "out/test-clues-api"
    shutil.rmtree(fixture, ignore_errors=True)
    source = fixture / "data/new-clues"
    source.mkdir(parents=True)
    shutil.copy(ROOT / "data/new-clues-20260815/amethyst_block.json", source / "amethyst_block.json")
    used_path = fixture / "data/used-targets.json"
    used_path.parent.mkdir(parents=True, exist_ok=True)
    used_path.write_text(json.dumps({"target_ids": ["amethyst_block"], "targets": [{"id": "amethyst_block", "sources": ["clue_bank"], "episode_ids": [], "video_files": []}]}), encoding="utf-8")
    server = make_server("127.0.0.1", 0, ClueCatalog(fixture, [source], fixture / "data/clues/inbox", used_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    dashboard_server = ThreadingHTTPServer(("127.0.0.1", 0), dashboard_app.Handler)
    dashboard_thread = threading.Thread(target=dashboard_server.serve_forever, daemon=True)
    dashboard_thread.start()
    dashboard_base = f"http://127.0.0.1:{dashboard_server.server_port}"
    try:
        status, used = call(base, "/api/clues?status=used")
        assert status == 200 and used["counts"] == {"all": 1, "used": 1, "unused": 0}
        assert used["items"][0]["status"] == "used"
        status, unused = call(base, "/api/clues?status=unused")
        assert status == 200 and unused["items"] == []
        os.environ["CLUES_API_URL"] = base
        assert get_clue("amethyst_block")["used"] is True
        proxy_status, proxy = call(dashboard_base, "/api/clues?status=used")
        assert proxy_status == 200 and proxy["items"][0]["id"] == "amethyst_block"

        value = upload_fixture()
        uploaded = upload_clue(value)
        assert uploaded["id"] == "ci_clue" and uploaded["status"] == "unused"
        assert list_clues("unused")["counts"] == {"all": 2, "used": 1, "unused": 1}
        duplicate_status, _ = call(base, "/api/clues", "POST", value)
        assert duplicate_status == 409

        used_path.write_text(json.dumps({"target_ids": ["amethyst_block", "ci_clue"], "targets": [{"id": "amethyst_block"}, {"id": "ci_clue", "episode_ids": ["mc-ci"]}]}), encoding="utf-8")
        assert get_clue("ci_clue")["status"] == "used"
        reused = upload_fixture()
        reused["episode"]["target"]["id"] = "amethyst_block"
        reused["episode"]["candidates"][0] = "amethyst_block"
        for fact in reused["episode"]["facts"]:
            fact["matches_candidates"] = ["amethyst_block" if item == "ci_clue" else item for item in fact["matches_candidates"]]
        for clue in reused["episode"]["clues"]:
            clue["matches_candidates"] = ["amethyst_block" if item == "ci_clue" else item for item in clue["matches_candidates"]]
        reused_status, _ = call(base, "/api/clues", "POST", reused)
        assert reused_status == 409
        invalid = upload_fixture()
        invalid["episode"]["clue_count"] = 2
        invalid_status, _ = call(base, "/api/clues", "POST", invalid)
        assert invalid_status == 400
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        dashboard_server.shutdown()
        dashboard_thread.join(timeout=5)
        dashboard_server.server_close()
        shutil.rmtree(fixture, ignore_errors=True)
    print("ok: clues API read, upload, used/unused separation, and validation")


if __name__ == "__main__":
    main()
