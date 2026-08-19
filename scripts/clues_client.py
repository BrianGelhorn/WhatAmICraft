"""Small HTTP client for the isolated clues API."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class CluesApiError(RuntimeError):
    pass


def request_json(path: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    base = os.getenv("CLUES_API_URL", "").rstrip("/")
    if not base:
        raise CluesApiError("CLUES_API_URL no está configurada")
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    try:
        with urlopen(Request(f"{base}{path}", data=body, headers=headers, method=method), timeout=10) as response:
            return response.status, json.loads(response.read() or b"{}")
    except HTTPError as error:
        try:
            value = json.loads(error.read() or b"{}")
        except json.JSONDecodeError:
            value = {"error": "Respuesta inválida del servicio de pistas"}
        return error.code, value
    except URLError as error:
        raise CluesApiError(f"No se pudo contactar la API de pistas: {error.reason}") from error


def list_clues(status: str = "unused", limit: int = 100) -> dict:
    return request_json(f"/api/clues?status={status}&limit={limit}")[1]


def get_clue(target_id: str) -> dict:
    return request_json(f"/api/clues/{target_id}")[1]


def upload_clue(value: dict) -> dict:
    status, result = request_json("/api/clues", method="POST", payload=value)
    if status != 201:
        raise CluesApiError(result.get("error", "La API rechazó la pista"))
    return result
