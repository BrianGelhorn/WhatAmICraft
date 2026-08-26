import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOB_PATH = ROOT / "out/current-job.json"
JOB_PATHS = {
    "main": JOB_PATH,
    "generation": ROOT / "out/current-generation-job.json",
    "publishing": ROOT / "out/current-publishing-job.json",
}
LEGACY_OWNERS = {"automatic": "publisher-worker", "manual": "dashboard"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default() -> dict:
    return {
        "status": "idle",
        "label": "",
        "source": "",
        "lines": [],
        "returnCode": None,
        "startedAt": None,
        "updatedAt": None,
        "log": None,
        "pid": None,
        "owner": "",
    }


def _read_job(lane: str) -> dict:
    path = JOB_PATHS[lane]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        job = {**_default(), **value}
        current_owner = os.getenv("JOB_OWNER")
        owned = current_owner and (
            job.get("owner") == current_owner
            or (not job.get("owner") and LEGACY_OWNERS.get(job.get("source")) == current_owner)
        )
        if job["status"] == "running" and job["pid"] and owned and not _process_alive(job["pid"]):
            job.update({
                "status": "failed",
                "returnCode": -1,
                "updatedAt": _now(),
                "lines": [*job["lines"][-99:], "Tarea interrumpida: el proceso dejó de responder."],
            })
            _write(job, lane)
        return job
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return _default()


def read_job(lane: str | None = None) -> dict:
    if lane:
        return _read_job(lane)
    jobs = [(name, _read_job(name)) for name in JOB_PATHS]
    running = [(name, job) for name, job in jobs if job["status"] == "running"]
    if len(running) == 1:
        name, job = running[0]
        return {**job, "lane": name}
    if len(running) > 1:
        return {
            **_default(),
            "status": "running",
            "label": " + ".join(job["label"] for _, job in running if job["label"]),
            "source": "+".join(name for name, _ in running),
            "lines": [line for _, job in running for line in job["lines"][-6:]],
            "startedAt": min(job["startedAt"] for _, job in running if job["startedAt"]),
            "updatedAt": max(job["updatedAt"] for _, job in running if job["updatedAt"]),
            "lane": "multiple",
        }
    return _read_job("main")


def _process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _write(job: dict, lane: str = "main") -> None:
    path = JOB_PATHS[lane]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def begin_job(label: str, source: str, log: str | None = None, lane: str = "main") -> None:
    job = _read_job(lane)
    if job["status"] == "running":
        raise RuntimeError("Ya hay una tarea en curso")
    now = _now()
    _write({
        **_default(),
        "status": "running",
        "label": label,
        "source": source,
        "startedAt": now,
        "updatedAt": now,
        "log": log,
        "pid": None,
        "owner": os.getenv("JOB_OWNER", ""),
    }, lane)


def set_job_pid(pid: int, lane: str = "main") -> None:
    job = _read_job(lane)
    if job["status"] != "running":
        return
    job["pid"] = pid
    job["updatedAt"] = _now()
    _write(job, lane)


def append_job_line(line: str, lane: str = "main") -> None:
    job = _read_job(lane)
    if job["status"] != "running":
        return
    job["lines"] = [*job["lines"][-99:], line]
    job["updatedAt"] = _now()
    _write(job, lane)


def finish_job(status: str, return_code: int, error: str | None = None, lane: str = "main") -> None:
    job = _read_job(lane)
    job["status"] = status
    job["returnCode"] = return_code
    job["updatedAt"] = _now()
    if error:
        job["lines"] = [*job["lines"][-99:], error]
    _write(job, lane)
