#!/usr/bin/env python3
"""Validate the real clue catalog through the API catalog loader."""

import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from clues_api import ClueCatalog  # noqa: E402


def main() -> None:
    fixture = ROOT / "out/test-clues-api-catalog"
    shutil.rmtree(fixture, ignore_errors=True)
    source = fixture / "data/new-clues"
    source.mkdir(parents=True)
    for path in (ROOT / "data/new-clues-20260815").glob("*.json"):
        shutil.copy(path, source / path.name)
    shutil.copy(ROOT / "data/used-targets.json", fixture / "data/used-targets.json")
    result = ClueCatalog(fixture, [source], fixture / "data/clues/inbox", fixture / "data/used-targets.json").list()
    items = result["items"]
    counts = result["counts"]
    assert counts["all"] == len(items) and counts["all"] > 0
    assert counts["all"] == counts["used"] + counts["unused"]
    assert all(item["uniqueAnswer"] and not item["needsReview"] for item in items)
    assert all(len(item["clues"]) == 3 for item in items)
    assert all(item["target"]["id"] in item["candidates"] for item in items)
    shutil.rmtree(fixture, ignore_errors=True)
    print(f"ok: real clue catalog validated ({counts['all']} items)")


if __name__ == "__main__":
    main()
