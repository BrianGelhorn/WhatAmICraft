"""Small HTTP client for the isolated monitoring service."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class MonitorApiError(RuntimeError):
    pass


def request_json(path: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    base = os.getenv("MONITOR_API_URL", "").rstrip("/")
    if not base:
        raise MonitorApiError("MONITOR_API_URL no está configurada")
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    try:
        with urlopen(Request(f"{base}{path}", data=body, headers=headers, method=method), timeout=5) as response:
            return response.status, json.loads(response.read() or b"{}")
    except HTTPError as error:
        try:
            value = json.loads(error.read() or b"{}")
        except json.JSONDecodeError:
            value = {"error": "Respuesta inválida del servicio de monitoreo"}
        return error.code, value
    except URLError as error:
        raise MonitorApiError(f"No se pudo contactar el servicio de monitoreo: {error.reason}") from error
