"""Small HTTP client for the isolated analytics service."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class AnalyticsApiError(RuntimeError):
    pass


def _url(path: str) -> str:
    base = os.getenv("ANALYTICS_API_URL", "").rstrip("/")
    if not base:
        raise AnalyticsApiError("ANALYTICS_API_URL no está configurada")
    return f"{base}{path}"


def request_json(path: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    try:
        with urlopen(Request(_url(path), data=body, headers=headers, method=method), timeout=5) as response:
            return response.status, json.loads(response.read() or b"{}")
    except HTTPError as error:
        try:
            value = json.loads(error.read() or b"{}")
        except json.JSONDecodeError:
            value = {"error": "Respuesta inválida del servicio de analytics"}
        return error.code, value
    except URLError as error:
        raise AnalyticsApiError(f"No se pudo contactar el servicio de analytics: {error.reason}") from error


def request_text(path: str) -> tuple[int, str]:
    try:
        with urlopen(Request(_url(path), headers={"Accept": "text/markdown"}), timeout=5) as response:
            return response.status, response.read().decode("utf-8")
    except HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace")
    except URLError as error:
        raise AnalyticsApiError(f"No se pudo contactar el servicio de analytics: {error.reason}") from error
