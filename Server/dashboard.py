#!/usr/bin/env python3
"""Loopback-only, read-only inventory for local Minecraft ZIP archives."""
from __future__ import annotations

import cgi
import io
import json
import os
import re
import subprocess
import threading
import time
import zipfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import asset_importer

ROOT = Path(__file__).parent
UPLOADS, CATALOGS, STATE = ROOT / "uploads", ROOT / "catalogs", ROOT / "dashboard_state.json"
MASTER_CATALOG = "all_assets.json"
MAX_UPLOAD = 128 * 1024 * 1024
MAX_MEMBERS, MAX_UNPACKED = 2_000, 512 * 1024 * 1024
JOB_LOCK = threading.Lock()
JOB = {"state": "idle", "message": "No scan running."}


def run_job(label: str, command: list[str], environment: dict[str, str] | None = None) -> None:
    if not JOB_LOCK.acquire(blocking=False):
        raise RuntimeError("Another task is already running")
    JOB.update(state="running", message=label, started=time.time())

    def worker() -> None:
        try:
            result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, timeout=900)
            output = (result.stdout + result.stderr).strip()
            JOB.update(state="done" if result.returncode == 0 else "failed", message=output[-4000:] or label)
        except (OSError, subprocess.TimeoutExpired) as error:
            JOB.update(state="failed", message=str(error))
        finally:
            JOB_LOCK.release()

    threading.Thread(target=worker, daemon=True).start()


def state() -> dict:
    try:
        value = json.loads(STATE.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(value: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temporary.replace(STATE)


def selected_zip() -> str | None:
    name = state().get("selected_zip")
    return name if isinstance(name, str) and Path(name).name == name and (UPLOADS / name).is_file() else None


def catalog() -> dict | None:
    name = MASTER_CATALOG if (CATALOGS / MASTER_CATALOG).is_file() else state().get("catalog_file", MASTER_CATALOG)
    if not isinstance(name, str) or Path(name).name != name or not name.endswith(".json"):
        return None
    try:
        value = json.loads((CATALOGS / name).read_text(encoding="utf-8"))
        return value if isinstance(value, dict) and isinstance(value.get("assets"), list) else None
    except (OSError, json.JSONDecodeError, AttributeError):
        return None


def safe_zip(upload: bytes) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(upload)) as archive:
            entries = archive.infolist()
            if not entries or len(entries) > MAX_MEMBERS or sum(item.file_size for item in entries) > MAX_UNPACKED:
                raise ValueError("ZIP is too large or has too many members")
            for item in entries:
                path = Path(item.filename.replace("\\", "/"))
                if "\x00" in item.filename or path.is_absolute() or ".." in path.parts:
                    raise ValueError("ZIP contains an unsafe path")
                if item.file_size > MAX_UNPACKED or (item.compress_size and item.file_size > item.compress_size * 200):
                    raise ValueError("ZIP exceeds the compression safety limit")
    except zipfile.BadZipFile as error:
        raise ValueError("Not a valid ZIP") from error


def _archive_assets(result: dict, archive_name: str) -> list[dict]:
    assets = []
    for asset in result.get("assets", []):
        value = dict(asset)
        value["archive"] = archive_name
        value["id"] = f"{archive_name}:{asset['id']}"
        assets.append(value)
    return assets


def _existing_assets() -> list[dict]:
    assets = []
    for path in CATALOGS.glob("*.json"):
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if path.name == MASTER_CATALOG:
            assets.extend(result.get("assets", []))
            continue
        archive = result.get("source", path.stem)
        assets.extend(_archive_assets(result, archive))
    return assets


def _merged_catalog(source: Path, result: dict) -> dict:
    assets = _existing_assets()
    assets.extend(_archive_assets(result, source.name))
    unique = {}
    for asset in assets:
        unique.setdefault((asset.get("archive"), asset.get("source")), asset)
    assets = sorted(unique.values(), key=lambda item: (item.get("archive", ""), item.get("id", "")))
    return {
        "source": "collection",
        "kind": "collection",
        "sources": sorted({asset["archive"] for asset in assets}),
        "members": result.get("members", {}),
        "warnings": result.get("warnings", []),
        "assets": assets,
    }


def scan(source: Path) -> None:
    if not JOB_LOCK.acquire(blocking=False):
        raise RuntimeError("A scan is already running")
    JOB.update(state="running", message=f"Scanning {source.name}", started=time.time())

    def worker() -> None:
        try:
            result = asset_importer.inspect_bundle(source)
            result = _merged_catalog(source, result)
            CATALOGS.mkdir(exist_ok=True)
            target = CATALOGS / MASTER_CATALOG
            temporary = target.with_suffix(".tmp")
            temporary.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
            temporary.replace(target)
            JOB.update(state="done", message=f"Collection has {len(result['assets'])} schematic assets")
        except Exception as error:
            JOB.update(state="failed", message=f"Scan failed: {error}")
        finally:
            JOB_LOCK.release()

    threading.Thread(target=worker, daemon=True).start()


def status() -> dict:
    source, result = selected_zip(), catalog()
    return {"selected_source": source, "job": dict(JOB), "summary": ({key: value for key, value in result.items() if key != "assets"} if result else None),
            "counts": {"assets": len(result["assets"])} if result else {"assets": 0}, "assets": result["assets"] if result else []}


class Dashboard(BaseHTTPRequestHandler):
    server_version = "LocalAssetBrowser/1"

    def log_message(self, *_args) -> None:
        pass

    def local(self) -> bool:
        return self.headers.get("Host", "").split(":")[0] in {"127.0.0.1", "localhost"}

    def send_json(self, value: dict, code: int = 200) -> None:
        data = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def error(self, code: int, message: str) -> None:
        self.send_json({"error": message}, code)

    def do_GET(self) -> None:
        if not self.local():
            self.error(HTTPStatus.FORBIDDEN, "Loopback access only")
            return
        path = urlsplit(self.path)
        if path.path == "/api/status":
            self.send_json(status())
        elif path.path == "/api/assets":
            values, query = status(), parse_qs(path.query)
            text, family = query.get("q", [""])[-1].lower(), query.get("family", [""])[-1].lower()
            values["assets"] = [asset for asset in values["assets"] if (not family or asset["family"].lower() == family) and (not text or text in json.dumps(asset).lower())]
            values["counts"] = {"assets": len(values["assets"])}
            self.send_json(values)
        elif path.path == "/":
            data = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.error(HTTPStatus.NOT_FOUND, "Not found")

    def mutation_ok(self) -> bool:
        origin = self.headers.get("Origin", "")
        return self.local() and (not origin or urlsplit(origin).hostname in {"127.0.0.1", "localhost"})

    def do_POST(self) -> None:
        if not self.mutation_ok():
            self.error(HTTPStatus.FORBIDDEN, "Loopback access only")
            return
        path = urlsplit(self.path).path
        if path == "/build":
            self.build()
            return
        if path != "/upload":
            self.error(HTTPStatus.NOT_FOUND, "Not found")
            return
        try:
            self.upload()
        except Exception as error:
            self.error(HTTPStatus.BAD_REQUEST, str(error))

    def build(self) -> None:
        sources = sorted(UPLOADS.glob("*.zip"))
        environment = os.environ.copy()
        environment.pop("STUDIO_ASSET_ZIP", None)
        environment.pop("STUDIO_ASSET_ZIPS", None)
        if sources:
            environment["STUDIO_ASSET_ZIPS"] = os.pathsep.join(str(path) for path in sources)
        run_job("Building datapack from uploaded ZIPs", ["python", "scene_controller.py", "build"], environment)
        self.send_json(status(), 202)

    def upload(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Invalid Content-Length") from error
        if length <= 0 or length > MAX_UPLOAD:
            raise ValueError("Upload must be a ZIP up to 128 MiB")
        if JOB_LOCK.locked():
            raise RuntimeError("Wait for the current scan to finish")
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers.get("Content-Type", "")})
        item = form["bundle"] if "bundle" in form else None
        if item is None or not item.filename or not item.filename.lower().endswith(".zip"):
            raise ValueError("Choose a ZIP archive")
        raw = item.file.read(MAX_UPLOAD + 1)
        if len(raw) > MAX_UPLOAD:
            raise ValueError("Upload exceeds 128 MiB")
        safe_zip(raw)
        stem = re.sub(r"[^a-zA-Z0-9._-]+", "_", Path(item.filename).stem).strip("._") or "archive"
        UPLOADS.mkdir(exist_ok=True)
        target = UPLOADS / f"{stem}.zip"
        for number in range(2, 10_000):
            if not target.exists():
                break
            target = UPLOADS / f"{stem}-{number}.zip"
        temporary = target.with_suffix(".upload")
        temporary.write_bytes(raw)
        temporary.replace(target)
        save_state({"selected_zip": target.name, "catalog_file": MASTER_CATALOG})
        scan(target)
        self.send_json(status(), 202)


HTML = '''<!doctype html><meta charset="utf-8"><title>Local asset browser</title>
<style>body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem}section{border:1px solid #ccc;padding:1rem;margin:1rem 0}table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #ddd;padding:.35rem;text-align:left}input{margin:.25rem}small{color:#555}</style>
<h1>Local asset/world browser</h1><p>Uploads are inspected only: nothing is extracted, built, executed, or loaded into Minecraft.</p>
<section><form id=upload><input required name=bundle type=file accept=.zip><button>Upload and scan ZIP</button></form><p id=error></p></section>
<section><h2>Scan y generacion</h2><pre id=job></pre><div id=summary></div><button id=build>Aplicar todos los ZIPs al generador</button><small>Esto solo reconstruye el datapack; despues usa /reload y setup en Minecraft.</small></section>
<section><h2>Assets acumulados</h2><input id=q placeholder="Filter text"><input id=family placeholder="Family"><span id=count></span><table><thead><tr><th>Archive</th><th>ID</th><th>Family</th><th>Variant</th><th>Dimensions</th><th>Blocks</th><th>Entities</th><th>Scenes</th></tr></thead><tbody id=assets></tbody></table></section>
<script>const $=id=>document.getElementById(id);let latest={};function text(v){return document.createTextNode(v)}function draw(s){latest=s;$('job').textContent=JSON.stringify(s.job,null,2);$('summary').textContent=s.summary?JSON.stringify(s.summary,null,2):s.selected_source?'Waiting for scan...':'Upload a world or template ZIP.';list()}function list(){let q=$('q').value.toLowerCase(),f=$('family').value.toLowerCase(),a=latest.assets||[];a=a.filter(x=>(!q||JSON.stringify(x).toLowerCase().includes(q))&&(!f||x.family.toLowerCase()===f));$('count').textContent=`${a.length} assets`;$('assets').replaceChildren(...a.map(x=>{let r=document.createElement('tr');[x.archive,x.id,x.family,x.variant,(x.size||[]).join(' × '),x.blocks,x.entities,(x.scenes||[]).join(', ')].forEach(v=>{let c=document.createElement('td');c.append(text(String(v??'')));r.append(c)});return r}))}async function refresh(){let r=await fetch('/api/status'),s=await r.json();draw(s);if(s.job.state==='running')setTimeout(refresh,500)}$('q').oninput=$('family').oninput=list;$('upload').onsubmit=async e=>{e.preventDefault();$('error').textContent='';let r=await fetch('/upload',{method:'POST',body:new FormData(e.target)}),s=await r.json();if(!r.ok)$('error').textContent=s.error;else draw(s);setTimeout(refresh,300)};$('build').onclick=async()=>{let r=await fetch('/build',{method:'POST'});draw(await r.json());setTimeout(refresh,500)};refresh()</script>'''


if __name__ == "__main__":
    print("Asset browser: http://127.0.0.1:8765")
    ThreadingHTTPServer(("0.0.0.0", 8765), Dashboard).serve_forever()
