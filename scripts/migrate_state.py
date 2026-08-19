#!/usr/bin/env python3
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review.storage import (  # noqa: E402
    ensure_state_db,
    pending_hints_items,
    pending_queue_ids,
    publishing_state,
    queue_items,
    state_db_path,
)


def main() -> int:
    ensure_state_db()
    print(f"SQLite state: {state_db_path()}")
    print(f"Queue items: {len(queue_items())}")
    print(f"Pending queue: {len(pending_queue_ids())}")
    print(f"Pending hints: {len(pending_hints_items())}")
    print(f"Published videos: {len(publishing_state()['videos'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
