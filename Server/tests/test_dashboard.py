import io
import gzip
import http.client
import json
import os
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
import dashboard
import asset_importer
import curate_assets


def bundle(name="tree.schematic"):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(name, b"not parsed here")
    return output.getvalue()


def schematic() -> bytes:
    root = {"Width": (2, 1), "Height": (2, 1), "Length": (2, 1),
            "Blocks": (7, b"\x01"), "Data": (7, b"\x00")}
    return gzip.compress(asset_importer._tag(10, "", root))


class DashboardTests(unittest.TestCase):
    def test_dashboard_is_reachable_through_docker_loopback_publish(self):
        compose = (ROOT / "docker-compose.yaml").read_text()
        source = (ROOT / "dashboard.py").read_text()
        self.assertIn('"127.0.0.1:8765:8765"', compose)
        self.assertIn('ThreadingHTTPServer(("0.0.0.0", 8765)', source)

    def test_zip_accepts_world_and_rejects_unsafe_paths(self):
        world = io.BytesIO()
        with zipfile.ZipFile(world, "w") as archive:
            archive.writestr("MyWorld/level.dat", b"level")
            archive.writestr("MyWorld/region/r.0.0.mca", b"region")
        dashboard.safe_zip(world.getvalue())
        with self.assertRaises(ValueError):
            dashboard.safe_zip(bundle("../world/tree.schematic"))

    def test_inspect_bundle_reports_world_and_schematic_catalog(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "bundle.zip"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("world/level.dat", b"level")
                archive.writestr("world/region/r.0.0.mca", b"region")
                archive.writestr("trees/tree.schematic", schematic())
            result = asset_importer.inspect_bundle(source)
        self.assertEqual(result["kind"], "both")
        self.assertEqual(result["members"]["region_files"], 1)
        self.assertEqual(result["members"]["schematic_files"], 1)
        self.assertEqual(len(result["assets"]), 1)
        self.assertEqual(result["assets"][0]["family"], "tree")
        self.assertEqual(result["assets"][0]["blocks"], 1)

    def test_tree_legacy_palette_and_catalog_accumulate(self):
        self.assertEqual(asset_importer._legacy_state(162, 13)[0], "minecraft:dark_oak_log")
        self.assertEqual(asset_importer._legacy_state(190, 0)[0], "minecraft:jungle_fence")
        self.assertEqual(asset_importer._typed(2**40), (4, 2**40))
        self.assertIn("rock", asset_importer._asset_tags("roc_granite", "rock.schematic", "epic-rocks.zip"))
        self.assertNotIn("rock", asset_importer._asset_tags("pin_stonepine", "pine.schematic", "trees.zip"))
        self.assertIn("farm_tree", asset_importer._asset_tags("birch", "birch.schematic", "trees.zip"))
        old_catalogs = dashboard.CATALOGS
        with tempfile.TemporaryDirectory() as temp:
            dashboard.CATALOGS = Path(temp)
            dashboard.CATALOGS.mkdir(exist_ok=True)
            (dashboard.CATALOGS / "old.json").write_text(json.dumps({"source": "old.zip", "assets": [{"id": "old", "source": "old.schematic"}]}))
            merged = dashboard._merged_catalog(Path("new.zip"), {"members": {}, "warnings": [], "assets": [{"id": "new", "source": "new.schematic"}]})
            self.assertEqual(len(merged["assets"]), 2)
            self.assertEqual({asset["archive"] for asset in merged["assets"]}, {"old.zip", "new.zip"})
        dashboard.CATALOGS = old_catalogs

    def test_asset_placement_obeys_scene_policy(self):
        catalog = [
            {"id": "mushroom_1", "family": "mushroom", "archive": "mushrooms.zip", "tags": ["mushroom"], "size": [4, 4, 4], "blocks": 20},
            {"id": "rock_1", "family": "rock", "archive": "rocks.zip", "tags": ["rock"], "size": [4, 4, 4], "blocks": 20},
            {"id": "oak_1", "family": "oak", "archive": "trees.zip", "tags": ["farm_tree"], "size": [8, 15, 8], "blocks": 100},
        ]
        _, cave = asset_importer.placement_commands("f03", 1, (0, 0), catalog, lambda *_: 64)
        _, farm = asset_importer.placement_commands("f04", 1, (0, 0), catalog, lambda *_: 64)
        self.assertEqual(cave["assets"], ["rock_1"])
        self.assertEqual(farm["assets"], ["oak_1"])
        self.assertNotIn("mushroom_1", cave["assets"] + farm["assets"])

    def test_curator_keeps_only_compatible_bounded_schematics(self):
        unsupported = gzip.compress(asset_importer._tag(10, "", {
            "Width": (2, 1), "Height": (2, 1), "Length": (2, 1),
            "Blocks": (7, b"\x07"), "Data": (7, b"\x00"),
        }))
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp) / "source.zip", Path(temp) / "active.zip"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("good.schematic", schematic())
                archive.writestr("bad.schematic", unsupported)
            result = curate_assets.curate(source, target)
            with zipfile.ZipFile(target) as archive:
                names = archive.namelist()
        self.assertEqual((result["kept"], result["rejected"]), (1, 1))
        self.assertIn("good.schematic", names)
        self.assertNotIn("bad.schematic", names)

    def test_default_sources_ignore_raw_uploads(self):
        old_root = asset_importer.ROOT
        selected = os.environ.pop("STUDIO_ASSET_ZIPS", None)
        try:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                uploads = root / "uploads"
                uploads.mkdir()
                for name in ("raw.zip", "trees-compatible.zip"):
                    with zipfile.ZipFile(uploads / name, "w") as archive:
                        archive.writestr("asset.schematic", schematic())
                asset_importer.ROOT = root
                self.assertEqual([path.name for path in asset_importer.find_sources()], ["trees-compatible.zip"])
                os.environ["STUDIO_ASSET_ZIPS"] = str(uploads / "raw.zip")
                with self.assertRaises(ValueError):
                    asset_importer.find_sources()
        finally:
            os.environ.pop("STUDIO_ASSET_ZIPS", None)
            asset_importer.ROOT = old_root
            if selected is not None:
                os.environ["STUDIO_ASSET_ZIPS"] = selected

    def test_upload_status_api(self):
        old = dashboard.UPLOADS, dashboard.CATALOGS, dashboard.STATE, dashboard.LIBRARY_BUNDLES
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dashboard.UPLOADS, dashboard.CATALOGS, dashboard.STATE = root / "uploads", root / "catalogs", root / "state.json"
            dashboard.LIBRARY_BUNDLES = root / "library" / "bundles"
            server = dashboard.ThreadingHTTPServer(("127.0.0.1", 0), dashboard.Dashboard)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                raw = io.BytesIO()
                with zipfile.ZipFile(raw, "w") as archive:
                    archive.writestr("world/level.dat", b"level")
                    archive.writestr("world/region/r.0.0.mca", b"region")
                boundary = "test-boundary"
                body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"bundle\"; filename=\"world.zip\"\r\nContent-Type: application/zip\r\n\r\n".encode() + raw.getvalue() + f"\r\n--{boundary}--\r\n".encode())
                connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
                connection.request("POST", "/upload", body, {"Content-Type": f"multipart/form-data; boundary={boundary}", "Content-Length": str(len(body))})
                response = connection.getresponse()
                self.assertEqual(response.status, 202)
                self.assertEqual(response.getheader("Content-Length"), str(len(response.read())))
                for _ in range(20):
                    connection.request("GET", "/api/status")
                    response = connection.getresponse()
                    status = json.loads(response.read())
                    if status["job"]["state"] != "running":
                        break
                    time.sleep(.05)
                self.assertEqual(status["summary"]["kind"], "collection")
                self.assertEqual(status["counts"]["assets"], 0)
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()
                dashboard.UPLOADS, dashboard.CATALOGS, dashboard.STATE, dashboard.LIBRARY_BUNDLES = old

    def test_uploaded_bundle_preserves_source_and_activates_only_curated_assets(self):
        old = dashboard.UPLOADS, dashboard.CATALOGS, dashboard.STATE, dashboard.LIBRARY_BUNDLES
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dashboard.UPLOADS, dashboard.CATALOGS, dashboard.STATE = root / "uploads", root / "catalogs", root / "state.json"
            dashboard.LIBRARY_BUNDLES = root / "library" / "bundles"
            try:
                source = dashboard.LIBRARY_BUNDLES / "mixed.zip"
                source.parent.mkdir(parents=True)
                unsupported = gzip.compress(asset_importer._tag(10, "", {
                    "Width": (2, 1), "Height": (2, 1), "Length": (2, 1),
                    "Blocks": (7, b"\x07"), "Data": (7, b"\x00"),
                }))
                with zipfile.ZipFile(source, "w") as archive:
                    archive.writestr("good.schematic", schematic())
                    archive.writestr("bad.schematic", unsupported)
                active = dashboard.UPLOADS / "mixed-compatible.zip"
                dashboard.scan(source, active)
                for _ in range(100):
                    if dashboard.JOB["state"] != "running":
                        break
                    time.sleep(.02)
                with zipfile.ZipFile(active) as archive:
                    names = archive.namelist()
                self.assertTrue(source.is_file())
                self.assertIn("good.schematic", names)
                self.assertNotIn("bad.schematic", names)
                self.assertEqual(dashboard.status()["counts"]["assets"], 1)
            finally:
                dashboard.UPLOADS, dashboard.CATALOGS, dashboard.STATE, dashboard.LIBRARY_BUNDLES = old


if __name__ == "__main__":
    unittest.main()
