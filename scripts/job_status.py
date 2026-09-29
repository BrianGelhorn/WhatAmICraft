import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOB_PATH = ROOT / "out/current-job.json"
JOB_PATHS = {
    "main": JOB_PATH,
    "generation": ROOT / "out/current-generation-job.json",
    "publishing": ROOT / "out/current-publishing-job.json",
}
LEGACY_OWNERS = {"automatic": "publisher-worker", "manual": "dashboard"}
STALE_PIDLESS_JOB = timedelta(minutes=15)


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
        "processStart": None,
        "owner": "",
    }


def _pidless_job_is_stale(job: dict) -> bool:
    if job.get("pid") or not job.get("updatedAt"):
        return False
    try:
        updated = datetime.fromisoformat(str(job["updatedAt"]).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - updated > STALE_PIDLESS_JOB


def _read_job(lane: str, recover: bool = True) -> dict:
    path = JOB_PATHS[lane]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        job = {**_default(), **value}
        current_owner = os.getenv("JOB_OWNER")
        owned = current_owner and (
            job.get("owner") == current_owner
            or (not job.get("owner") and LEGACY_OWNERS.get(job.get("source")) == current_owner)
        )
        if recover and job["status"] == "running" and owned and (
            (job["pid"] and not _same_process(job)) or _pidless_job_is_stale(job)
        ):
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


def _process_start(pid: int) -> str | None:
    try:
        return Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").split()[21]
    except (FileNotFoundError, IndexError, OSError):
        return None


def _same_process(job: dict) -> bool:
    pid = job["pid"]
    if not _process_alive(pid):
        return False
    expected = job.get("processStart")
    return expected is None or _process_start(pid) == str(expected)


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
    job["processStart"] = _process_start(pid)
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
    job = _read_job(lane, recover=False)
    job["status"] = status
    job["returnCode"] = return_code
    job["updatedAt"] = _now()
    if error:
        job["lines"] = [*job["lines"][-99:], error]
    _write(job, lane)
