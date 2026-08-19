#!/usr/bin/env python3
from publishing.settings import apply_runtime, enabled_platforms, load_config
from review.storage import publishing_state, queue_items, set_queue_status


def main() -> int:
    config = load_config()
    apply_runtime(config)
    required = set(enabled_platforms(config))
    state = publishing_state()["videos"]
    fixed = []
    for item in queue_items():
        if item.get("status") != "failed":
            continue
        platforms = set(state.get(item["episodeId"], {}).get("platforms", {}))
        if platforms and required <= platforms:
            set_queue_status(item["episodeId"], "completed")
            fixed.append(item["episodeId"])
    print(f"Reparados: {', '.join(fixed) if fixed else 'ninguno'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
