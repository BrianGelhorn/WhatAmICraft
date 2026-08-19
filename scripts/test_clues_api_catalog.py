#!/usr/bin/env python3
"""Validate the real clue catalog through the API catalog loader."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from clues_api import ClueCatalog  # noqa: E402


def main() -> None:
    result = ClueCatalog(ROOT).list()
    items = result["items"]
    counts = result["counts"]
    assert counts["all"] == len(items) and counts["all"] > 0
    assert counts["all"] == counts["used"] + counts["unused"]
    assert all(item["uniqueAnswer"] and not item["needsReview"] for item in items)
    assert all(len(item["clues"]) == 3 for item in items)
    assert all(item["target"]["id"] in item["candidates"] for item in items)
    print(f"ok: real clue catalog validated ({counts['all']} items)")


if __name__ == "__main__":
    main()
